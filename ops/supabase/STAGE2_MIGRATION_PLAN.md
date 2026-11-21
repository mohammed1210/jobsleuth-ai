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

## Consolidating test accounts into ONE permanent JobSleuth account (owner-reported plan)

On 21 November 2026, the owner confirmed that **only they have used JobSleuth**, sometimes via **one to three test logins**. This is useful planning context, but it is **not identity proof that all five users in the mixed PropNexus/JobSleuth Auth project are theirs**. Two Auth users with Evidence Bank records must still be verified against an owner-controlled private account list before any actual import.

**Proposed default:** create **one new verified JobSleuth Auth account** in the dedicated project using the owner's chosen permanent email/password and a fresh login. The old accounts remain intact and can still serve PropNexus. The private mapping can be explicitly *many old IDs to one new ID*, but only for source accounts the owner verifies.

- Two source Evidence Bank owners can consolidate 1 + 3 cards into **4 cards under one new Auth UUID**; preserve every card ID and field and both timestamps, after checking source record ID collisions.
- Pilot feedback includes **3 historic test submissions**. Preserve them as a private backup even if they are excluded from *real pilot conversion metrics*. Do not silently count them as real 5-user pilot results; decide whether to import/archive before the actual transfer.
- The other **three source accounts** remain untouched until the owner identifies which, if any, are unrelated to JobSleuth. Even if they are all test accounts, we need not migrate unnecessary logins.
- The migration rehearsal `stage2_single_account_consolidation.sql` simulates 2 old owners -> 1 new owner **only in a disposable local database**, proves data and timestamp preservation across all columns, and ROLLBACKs its simulated consolidation.
- For actual execution, separately authorize the confirmed set of source account identities, the chosen permanent login and whether to migrate pilot feedback. No `auth.users` rows should be inserted by SQL in a live project: use supported Supabase Auth signup/invitation/admin APIs with verified ownership. No actual user has been invited or migrated.
- **Do not merge the accounts on the legacy mixed-use Supabase project**. Only copy approved app records to the fresh account; this avoids altering PropNexus identity or data.

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


## Stage 2 real-transfer operator runbook (approved, but not yet executed)

The owner authorised the destination Auth account and transfer of FOUR evidence
cards and THREE historical feedback records from exactly TWO known, personally
owned test logins into ONE permanent new JobSleuth login. Source accounts and
data remain untouched, and Railway/Vercel/Stripe must not change.

**Create Auth account first:** In the NEW project's [Authentication → Users
dashboard](https://supabase.com/dashboard/project/uqvhnqhbushhtkthwrhk/auth/users),
select **Add user → Create new user** and choose the permanent email and a
strong password privately; if offered, use **Auto Confirm User** after verifying
it is your own address. This avoids confirmation redirects while the production
frontend still points at the old project. Alternatively use **Send invitation**,
but first check Authentication → URL Configuration to ensure the link has a
valid destination. In either case, confirm exactly one verified NEW Auth user
exists before the private transfer. Supabase connector does not expose Auth user invitation; do not
insert directly into Supabase-managed `auth.users` tables. No password or secret
should be given to ChatGPT.

**Private migration utility:** `ops/supabase/private_stage2_transfer.py` runs
on the owner's authorised private computer, with `psycopg[binary]` installed
in a local venv. Never run it through GitHub CI or on a shared terminal. Set
these environment variables privately using the source/target Supabase
"Connect" panels; NEVER paste values into Git or this conversation:

- `JOBSLEUTH_SOURCE_DB_URL` — OLD shared project PostgreSQL URL
- `JOBSLEUTH_TARGET_DB_URL` — NEW isolated project PostgreSQL URL
- `JOBSLEUTH_SOURCE_EMAILS` — exactly two verified test-account email addresses, comma-separated
- `JOBSLEUTH_DEST_EMAIL` — permanent new account email

Run without arguments first (read-only dry-run). Confirm the source records and
destination are as expected and that the new user has completed verification.
Only then run:

```sh
python ops/supabase/private_stage2_transfer.py --commit \
  --confirm CONFIRM_4_EVIDENCE_3_FEEDBACK
```

The script requires exact project URLs, two verified source accounts and one
verified destination account. It accepts precisely 4 evidence cards + 3 feedback
rows, performs an atomic NEW-project SQL transaction, preserves IDs/all business
fields/timestamps, and checks counts and remapped ownership before commit. It
does not modify the OLD database and does not print personal record contents.

**After transfer:** old production still writes to the shared project. Avoid
editing evidence until an approved coordinated frontend/backend cutover; rerun
an inventory to detect any new/changed source records. Production cutover and
billing remain separate approvals.
