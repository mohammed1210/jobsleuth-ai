# Atomic billing persistence — release and recovery gate

Status: review candidate; no production migration or billing activation authorized.

## Before approval

- Identify the exact Supabase project from the backend's configured project reference (not a guess from account/project names). Inspect only schema/catalog metadata; never copy customer rows or secrets into GitHub.
- Verify the deployed subscriptions table against `supabase/schema.sql`: column types, owner foreign key, primary key, unique Stripe identifiers, RLS and actual service-role table/sequence privileges. The historical initial migration does not create this table.
- Check counts of missing owners, duplicate owners and legacy subscription rows with a separately approved minimal aggregate audit. Never automatically delete or merge rows to satisfy the new constraint.
- Confirm Stripe SDK compatibility, server-side checkout/account binding and sandbox lifecycle; reconcile legacy or same-second competing subscriptions against Stripe. A rejected ambiguous update does not itself remove an existing entitlement.
- Run the new PostgreSQL harness and backend/frontend CI on the candidate integrated with current main. Obtain completed security review and resolve blocking findings.
- Prepare the tracked migration with the Supabase CLI in an isolated environment after schema compatibility is established. Keep checkout disabled. Review backup/restore availability and database/release order before approval.

## Approved rollout proposal (not executed)

1. Keep checkout disabled and do not configure live webhook delivery. Confirm no active billing writers; capture the existing release SHA and approved backup/restore point.
2. Apply the reviewed additive migration transaction with a bounded lock timeout. Abort on duplicate/null owners or schema mismatch; do not remove constraints or data to force it through.
3. Verify the RPC is callable by service_role and denied to anon/authenticated, and that existing entitlement reads remain compatible. Verify schema and migration history without publishing customer records.
4. Deploy the approved backend SHA after the RPC exists. Run anonymous health/auth-denial checks, synthetic Apply smoke checks and isolated Stripe sandbox checkout, renewal/failure and cancellation tests.
5. Keep live payments off until an independent approval after the sandbox lifecycle succeeds.

## Recovery

- A transaction that has not committed can be rolled back without a partial schema update.
- If application deployment fails after the database change, preserve the additive columns and uniqueness constraint initially; restore the previously approved backend only after checking compatibility. Keep checkout off and prevent billing writes during recovery. Do not assume a legacy webhook writer is safe.
- Do not automatically drop the RPC, revisions or uniqueness constraints or restore stale subscription records. A separate reviewed reverse migration or Stripe reconciliation plan is required if database rollback is necessary, especially after any billing writes.
- Document the outcome in PR #90 and issue #88. Production writes, schema changes, deployment and live billing each require owner approval.
