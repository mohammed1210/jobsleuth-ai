# Stage 2: selective account, Evidence Bank and pilot feedback migration

**STATUS: PREPARATION / NO CUSTOMER DATA MOVED.**
Source: legacy shared Supabase project `wsfemkhxttddztnhthkc` (also used by PropNexus).
Target: dedicated JobSleuth project `uqvhnqhbushhtkthwrhk` (Stage 1 schema already applied).
Never perform a full shared-project restore onto JobSleuth: it would copy unrelated PropNexus users and tables and conflict with the new schema.

## Evidence inventory — read-only snapshot, 21 November 2026

- Source `auth.users`: **5** password-based email accounts, **4** email-confirmed and signed in.
- `evidence_cards`: **4** records across **2** owners, with no missing Auth owner.
- `pilot_feedback`: **3** records, all owned by the same owner that has **3** of the Evidence Bank cards.
- A second owner has **1** Evidence Bank card and no pilot feedback.
- **Three other Auth accounts own no evidence or feedback**; their application affiliation is **unverified**. Do not migrate these based on absence of data or assume they belong to PropNexus.
- Source `subscriptions`: 0 records. No JobSleuth-specific storage buckets or objects were found. Existing buckets are for another application's property images and must not be copied.
- Source Evidence Bank and feedback column names/types were inspected and match the new baseline schema; column-by-column and ownership verification is still mandatory when real records are approved for transfer.
- Target remains free of Auth users and applicant records as of this read-only audit.
- No account emails, UUIDs, passwords, token values, evidence text or applicant content are stored in this repository.

These figures are **not** a lock or a final export count. Repeat the read-only inventory immediately before transfer and reconcile any new writes.

## Private owner identification (not done)

1. Privately identify which specific people control the **two Auth accounts with JobSleuth Evidence Bank records**. Verify application affiliation from the service/consent context and a verified account ownership process — not from untrusted `raw_user_meta_data` or a user-supplied email alone.
2. Independently determine whether any of the other three Auth accounts actually used JobSleuth and should keep an account even if they have no Evidence Bank records.
3. Record a **private, access-controlled mapping**, `source_auth_uuid -> target_auth_uuid`, plus evidence/feedback counts and account-owner approval. The mapping MUST NOT be committed, attached to PRs, pasted into chat or exposed in CI logs.
4. For a selected migration, prefer new Supabase Auth account creation/invitation with an explicit user sign-in/reset flow; the destination can assign different UUIDs, so all transferred `user_id` foreign keys must be remapped.
5. A selective direct Auth-schema/hashed-password migration may preserve source UUIDs and passwords but requires a separately validated, supported method and is **not** authorized here. Do not restore the entire `auth` schema from the shared project: it would bring unrelated users. Do not copy passwords/hashes/sessions into scripts, logs or GitHub.
6. New-project access tokens will use a different issuer/signing configuration. Plan a deliberate fresh login. Old session cookies/tokens are not portable. Do not copy or reuse JWT signing secrets.

## Transfer plan (requires separate owner approval)

1. Record a private backup/restore checkpoint of the OLD project and a migration start time. No deletion, mutation or routine suspension of PropNexus.
2. Restrict new JobSleuth writes for an agreed, short cutover window; do not alter PropNexus traffic. Take a final source-only audit and reconcile the owner list and counts.
3. Ensure selected target Auth users **exist, are verified, and own the expected destination UUIDs** before transferring rows. Never fabricate `auth.users` rows or bypass Supabase Auth in production.
4. Export **only whitelisted owners'** `public.evidence_cards` and `public.pilot_feedback` via a private authorized environment. Keep content in transit encrypted and off PRs, CI artifacts, app logs and chat. Retain original record `id`, business fields, `created_at`, and `updated_at`; remap `user_id` through the verified private mapping. There are no source Saved Jobs or JobSleuth storage assets to move.
5. Refuse transfers with missing/ambiguous owner mappings, duplicate record IDs, target duplicates, null ownership, schema mismatches, or conflicting content. Stop rather than delete or overwrite. The synthetic rehearsal under `ops/supabase/stage2_synthetic_rehearsal.sql` demonstrates owner mapping and content/timestamp preservation **only with fake data**.
6. Validate **total and per-owner counts**, every original ID, owner remapping, timestamps/content checksums calculated locally and privately, target RLS cross-user isolation, and login/record access for each approved account. If counts differ, halt production cutover.
7. After a separate release approval, switch Railway and Vercel to the same new Auth project in one coordinated release, with a rollback checklist and a newly generated test login. Keep Stripe checkout disabled and PR #90's billing migration separate.
8. Preserve the old project and old records intact until an approved retention/deletion decision. Rollback after new writes may require another reconciliation; do NOT blindly switch environment URLs back and forth.

## Runbook gates

- Owner confirms affected accounts and approves which ones may move.
- Explicit second approval for private auth/data transfer, separate from Stage 1 schema approval.
- Private migration operator and storage method are identified; secret strings never enter assistant conversations.
- The selected strategy is confirmed against current [Supabase Auth migration guidance](https://supabase.com/kb/troubleshooting/migrating-auth-users-between-projects). Restoring the **entire** Auth schema is unsafe for this mixed-use source.
- Synthetic Postgres rehearsal and all CI checks pass; security review resolves P0/P1.
- Final snapshot and target preflight are reviewed, then cutover is approved separately.
- Avoid GitHub Actions executions with production tokens; synthetic tests require none.

## Private inventory query

The non-identifying report in `ops/supabase/stage2_read_only_inventory.sql` can be reviewed in the OLD project via read-only SQL. It outputs no email, actual UUID or evidence-card content. If an operator needs the actual account identities, they must review them privately in Supabase under appropriate access controls.

**Current authorization stops at Stage 2 planning.** Neither this PR nor CI transfers records or changes Railway, Vercel, Stripe or either production database.
