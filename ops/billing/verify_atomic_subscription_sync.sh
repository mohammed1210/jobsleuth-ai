#!/usr/bin/env bash
# Disposable local Docker database only; no Supabase credentials or network DB.
set -euo pipefail
cd "$(dirname "$0")/../.."
db="$(docker run --rm -d -e POSTGRES_HOST_AUTH_METHOD=trust postgres:16)"
trap 'docker stop "$db" >/dev/null 2>&1 || true' EXIT
for _ in $(seq 1 40); do
    if docker exec "$db" pg_isready -U postgres >/dev/null 2>&1; then break; fi
    sleep 1
done
sql() { docker exec -i "$db" psql -X -v ON_ERROR_STOP=1 -U postgres "$@"; }
sql <<'SQL'
create role anon;
create role authenticated;
create role service_role bypassrls;
create schema auth;
create table auth.users (id uuid primary key);
create function auth.uid() returns uuid language sql as 'select null::uuid';
create function auth.role() returns text language sql as 'select current_user::text';
SQL
sql < supabase/schema.sql
sql < ops/billing/atomic_subscription_sync.sql
sql < ops/billing/test_atomic_subscription_sync.sql
# Two separate connections race to insert the same user with different customers.
sql -c "insert into auth.users values ('00000000-0000-4000-8000-000000000002');"
call_one="select public.billing_sync_subscription('00000000-0000-4000-8000-000000000002','cus_race1','sub_race1',100,'pro','active',null);"
call_two="select public.billing_sync_subscription('00000000-0000-4000-8000-000000000002','cus_race2','sub_race2',101,'pro','active',null);"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"; docker stop "$db" >/dev/null 2>&1 || true' EXIT
sql -Atc "$call_one" > "$tmp/one" & first=$!
sql -Atc "$call_two" > "$tmp/two" & second=$!
wait "$first"; wait "$second"
test "$(cat "$tmp/one" "$tmp/two" | sort | tr '\n' ' ')" = "applied retry "
test "$(sql -Atc "select count(*) from public.subscriptions where user_id='00000000-0000-4000-8000-000000000002'")" = 1
echo 'Atomic subscription SQL checks passed'
