#!/usr/bin/env bash
# Synthetic isolated database ONLY. No Supabase credentials, external requests
# or applicant content. Docker must be available.
set -euo pipefail
cd "$(dirname "$0")/../.."
db="$(docker run --rm -d -e POSTGRES_HOST_AUTH_METHOD=trust postgres:16)"
trap 'docker stop "$db" >/dev/null 2>&1 || true' EXIT
for _ in $(seq 1 40); do
  if docker exec "$db" pg_isready -U postgres >/dev/null 2>&1; then break; fi
  sleep 1
done
sql() { docker exec -i "$db" psql -X -v ON_ERROR_STOP=1 -U postgres "$@"; }
sql <<'SETUP'
create role anon;
create role authenticated;
create role service_role bypassrls;
create schema auth;
create table auth.users (id uuid primary key);
create function auth.uid() returns uuid language sql stable as
  $$ select nullif(current_setting('request.jwt.claim.sub', true),'')::uuid $$;
grant usage on schema auth to anon, authenticated, service_role;
grant execute on function auth.uid() to anon, authenticated, service_role;
SETUP
sql < ops/supabase/fresh_project_bootstrap.sql
sql < ops/supabase/verify_fresh_project.sql
# Preflight must reject repeat bootstrap rather than silently keep drift.
if sql < ops/supabase/fresh_project_bootstrap.sql >/dev/null 2>&1; then
  echo "Bootstrap unexpectedly allowed existing application tables" >&2
  exit 1
fi
sql <<'TESTDATA'
insert into auth.users(id) values
('00000000-0000-4000-8000-000000000001'),
('00000000-0000-4000-8000-000000000002');
insert into public.jobs(title,company,location)
  values ('Synthetic role','Synthetic company','Remote');
insert into public.evidence_cards(user_id,title)
  values ('00000000-0000-4000-8000-000000000001','Synthetic owner A'),
         ('00000000-0000-4000-8000-000000000002','Synthetic owner B');
TESTDATA
# A real RLS check, with SET ROLE and a synthetic JWT claim.
visible="$(sql -qAtc "set role authenticated; set request.jwt.claim.sub = '00000000-0000-4000-8000-000000000001'; select count(*) from public.evidence_cards;")"
test "$visible" = 1
# Anonymous access to evidence and subscriptions must be denied by ACLs.
if sql -qAtc 'set role anon; select count(*) from public.subscriptions;' >/dev/null 2>&1; then
  echo "Anonymous access to subscriptions unexpectedly succeeded" >&2
  exit 1
fi
if sql -qAtc 'set role anon; select count(*) from public.evidence_cards;' >/dev/null 2>&1; then
  echo "Anonymous access to evidence unexpectedly succeeded" >&2
  exit 1
fi
# Stage 4 additive job-ingestion schema is compatible with Stage 1 and
# repeat-safe. Test every DDL step in the same disposable Postgres instance.
sql < ops/supabase/stage4_jobs_ingestion.sql
sql < ops/supabase/stage4_jobs_ingestion.sql
sql <<'STAGE4'
do $check$
begin
  if not exists (
    select 1 from pg_indexes
    where schemaname='public' and tablename='jobs'
      and indexname='jobs_provider_identity_unique'
  ) then raise exception 'Job source unique index missing'; end if;
end
$check$;
insert into public.jobs(title, company, location, source, source_board,
                        external_id, last_seen_at, is_active)
values ('Synthetic vacancy', 'Synthetic employer', 'London, United Kingdom',
        'greenhouse', 'synthetic', '1234', now(), true)
on conflict(source, source_board, external_id)
do update set title=excluded.title, last_seen_at=excluded.last_seen_at;
insert into public.jobs(title, company, location, source, source_board,
                        external_id, last_seen_at, is_active)
values ('Synthetic vacancy', 'Synthetic employer', 'London, United Kingdom',
        'greenhouse', 'synthetic', '1234', now(), true)
on conflict(source, source_board, external_id)
do update set title=excluded.title, last_seen_at=excluded.last_seen_at;
do $check$
begin
  if (select count(*) from public.jobs
      where source='greenhouse' and source_board='synthetic'
      and external_id='1234') <> 1
  then raise exception 'Source idempotence failed'; end if;
end
$check$;
insert into public.saved_jobs(user_id, job_id)
select '00000000-0000-4000-8000-000000000001', id
from public.jobs where source='greenhouse'
 and source_board='synthetic' and external_id='1234';
update public.jobs set is_active=false
where source='greenhouse' and source_board='synthetic' and external_id='1234';
do $check$
begin
  if (select count(*) from public.saved_jobs) <> 1
  then raise exception 'Closing an expired vacancy removed saved-job history'; end if;
end
$check$;
STAGE4
# Public may still SELECT closed rows for saved-job history, while the API
# explicitly filters is_active. Neither anon nor authenticated may INSERT.
for role in anon authenticated; do
  if sql -qAtc "set role $role; insert into public.jobs(title,company,location) values ('Unsafe','No','London');" >/dev/null 2>&1; then
    echo "Stage 4 unexpectedly granted $role direct job writes" >&2
    exit 1
  fi
done
echo "Stage 4 schema, idempotence, RLS and saved-job retention passed"
echo "Fresh-project schema and RLS checks passed"
