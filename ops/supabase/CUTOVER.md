# JobSleuth isolated Supabase project — cutover gate

**Status: draft, review only.** Supabase project `uqvhnqhbushhtkthwrhk` is healthy but empty as last observed on 21 November 2026. The running Railway backend still uses the older Supabase project associated with PropNexus. No cutover has been approved.

## Why a fresh bootstrap?

The repository's historical `20240101000000_initial_schema.sql` creates UUID job identifiers and a legacy `users` table. The current backend and `supabase/schema.sql` expect bigint job identifiers, `auth.users` and `user_profiles`. Never apply the historical migrations blindly to the newly created project; the resulting schema is incompatible with the current Saved Jobs API.

`fresh_project_bootstrap.sql` is an **unapplied standalone candidate**, not a migration in the CLI history. It creates only the six tables needed by the current API, matching the current schema and Evidence Bank/pilot feedback definitions; it uses RLS owner policies, least-privilege table grants, and revokes direct public invocation of the `rls_auto_enable()` event-trigger function if present.

The subscription table intentionally has the main-branch baseline shape. PR #90's revision columns, uniqueness constraint and atomic billing RPC are a **separate later step**, subject to independent schema/security review and sandbox checks.

## Verification before any database write

1. Obtain a complete security review of this SQL, the historical migrations and the current backend dependencies.
2. Confirm the target project ID and environment: **only** the new empty JobSleuth project; do not point any commands at PropNexus.
3. Confirm fresh-project tables are still absent, and no pilot accounts/data have appeared. If not empty, halt and reconcile; never force or delete.
4. Run `bash ops/supabase/verify_fresh_project.sh` in a disposable Docker PostgreSQL environment. This does not connect to Supabase. Review CI logs and permissions.
5. Get explicit owner approval for the actual new-project DDL. Record migration history and a schema snapshot using a supported Supabase migration process rather than pretending the standalone candidate was applied as a tracked migration. Verify effective ACL/RLS using the Supabase security advisor after installation.

## Existing account and content migration — no actions taken

A new Supabase Auth project has different keys/JWT issuer and no existing accounts. Changing only `SUPABASE_URL` will make existing users' sessions invalid and leave profiles/evidence behind. Before cutover, arrange a supported auth/user migration, preserving user UUIDs where supported, and plan secure transfer of JobSleuth-only tables, storage objects and RLS ownership. Do not copy password hashes, session tokens or CV/application content into GitHub or logs. Use approved export/import tooling, private staging and auditable mapping; verify counts and user consent where necessary. Avoid assuming PropNexus customers belong to JobSleuth.

## Controlled release sequence (not authorized)

- Keep checkout disabled and PR #90 unmerged.
- Apply the reviewed base schema to the isolated project and verify with metadata and synthetic identities.
- Reconcile any JobSleuth accounts and associated content from the old project using a separately approved migration, then test login, Evidence Bank and Saved Jobs with synthetic accounts.
- Review/apply PR #90's atomic billing migration only after database compatibility and sandbox tests.
- Verify Vercel **public** Supabase URL/publishable key and Railway **private** service-role and related credentials via dashboard, without sharing secrets in chat or Git. Never put a service-role key into `NEXT_PUBLIC_` variables.
- Switch Vercel/Railway only as a coordinated owner-approved release with a tested rollback plan. Avoid leaving frontend and backend pointed to different Auth projects.
- Perform health, 401 unauthenticated access, Evidence Bank, saved-job persistence, and end-to-end Apply smoke tests before the five-user pilot. Do not enable real payments.

## Rollback

An aborted bootstrap transaction rolls back atomically. After cutover, rollback also depends on account/content reconciliation and frontend/backend matching JWT issuers; restoring old URLs alone is **not** a safe data rollback. Preserve the old project and backups until reviewed reconciliation and rollout verification are complete. Never delete or repurpose the PropNexus project.
