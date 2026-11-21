#!/usr/bin/env bash
# Runs ONLY against a disposable local PostgreSQL Docker container.
# No live database URL, secret, applicant content or account IDs are read.
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
create table auth.users(id uuid primary key);
create function auth.uid() returns uuid language sql stable as
 $$ select nullif(current_setting('request.jwt.claim.sub',true),'')::uuid $$;
grant usage on schema auth to anon, authenticated, service_role;
grant execute on function auth.uid() to anon, authenticated, service_role;
SETUP
sql < ops/supabase/fresh_project_bootstrap.sql > /dev/null
sql < ops/supabase/stage2_synthetic_rehearsal.sql > /dev/null
# Role tests use synthetic identities. A signed-in user cannot see another
# user's Evidence Bank or feedback, and anonymous billing access is denied.
a_cards="$(sql -qAtc "set role authenticated; set request.jwt.claim.sub = '00000000-0000-4000-8000-000000000031'; select count(*) from public.evidence_cards;")"
b_cards="$(sql -qAtc "set role authenticated; set request.jwt.claim.sub = '00000000-0000-4000-8000-000000000032'; select count(*) from public.evidence_cards;")"
a_feedback="$(sql -qAtc "set role authenticated; set request.jwt.claim.sub = '00000000-0000-4000-8000-000000000031'; select count(*) from public.pilot_feedback;")"
b_feedback="$(sql -qAtc "set role authenticated; set request.jwt.claim.sub = '00000000-0000-4000-8000-000000000032'; select count(*) from public.pilot_feedback;")"
test "$a_cards" = 1
test "$b_cards" = 3
test "$a_feedback" = 0
test "$b_feedback" = 3
if sql -qAtc 'set role anon; select count(*) from public.evidence_cards;' > /dev/null 2>&1; then
  echo "Anonymous access to private Evidence Bank was unexpectedly allowed" >&2
  exit 1
fi
echo "Stage 2 synthetic account remapping and RLS checks passed"
