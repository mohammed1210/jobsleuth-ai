# Stage 3 — coordinated JobSleuth Supabase cutover (PREPARED, NOT APPROVED FOR RELEASE)

Last audited: 21 November 2026. This document supersedes the outdated pre-bootstrap
state described in older deployment notes. **Do not blindly follow the 2024
UUID-job migration or restore the PropNexus database.**

## Verified baseline (read-only)

- OLD shared project: `wsfemkhxttddztnhthkc` (also serves PropNexus).
  Historical snapshot retains 5 Auth accounts, 4 Evidence Bank cards and 3
  pilot feedback rows. **Do not change or delete this project.**
- NEW dedicated project: `uqvhnqhbushhtkthwrhk` (EU West).
  The approved Stage 1 schema is installed and tracked as migration
  `20261121191325_jobsleuth_isolated_initial_schema_20261121`.
- The owner created one verified NEW Auth account. Stage 2 copied the 4 Evidence
  Bank cards and 3 historical pilot feedback records from two of the owner's
  old test accounts; post-migration field/ID/timestamp checksums matched.
  The old source is intact; **never repeat Stage 2**.
- Among the four evidence rows one is an internal `cv_profile` record. The
  `/evidence` endpoint intentionally excludes that record; expect **three**
  visible cards and a separately retrievable CV profile, not four visible cards.
- NEW project contains **zero** saved jobs and zero subscription rows. No real
  job listings have been imported, and the current `/jobs` backend serves
  **mock example job listings**. Treat search/save-job scenarios as incomplete
  until the listings pipeline is connected. Do not claim a successful live job
  save against a fake job ID.
- Railway service `jobsleuth-ai` is online on `main` with root `backend`.
  Its variable names include `SUPABASE_URL`, `SUPABASE_KEY`,
  `SUPABASE_SERVICE_ROLE_KEY`, `DATABASE_URL`, `FRONTEND_URL` and
  `STRIPE_SECRET_KEY`. OAuth connector access shows names, **not values**,
  so the connection URL was not independently checked at this audit.
  `DATABASE_URL` is not referenced by current backend application code per
  GitHub code search. **Do not overwrite it** without proving its owner/use.
- The Vercel project is not yet connected to ChatGPT, so active environment
  variable values and preview/production target configuration cannot be
  checked via the connected tools. The owner must connect Vercel or use its
  dashboard; do not guess any Vercel project IDs or current keys.
- Checkout remains disabled under the default `BILLING_CHECKOUT_ENABLED=false`
  (the connected Railway service did not list a corresponding override).
  PR #90's atomic Stripe migration is **not applied**. Do not activate
  checkout/webhooks as part of this release.

## Engineering gates before release

1. Review and merge the fail-closed Auth, Saved Jobs, user-profile and UI error
   handling PR in this workstream. Existing implementations return mock user
   profiles, accept synthetic bearer tokens on some paths, and report saved
   jobs as persisted when the database is down. These are blockers.
2. Await the latest Codex review and CI result. Keep old auth tests synthetic;
   never use real service-role credentials or user passwords in CI.
3. Resolve the Supabase Auth security advisor warning, **leaked-password
   protection disabled**, before onboarding external testers:
   https://supabase.com/docs/guides/auth/password-security#password-strength-and-leaked-password-protection
4. Record existing Railway/Vercel variable names and *secure backup of values*
   privately so production can be rolled back; never put secrets in this repo.
   Confirm billing flags remain off and domains/CORS/redirects match reality.
5. Ensure both projects' schema and record counts still match this documented
   snapshot. If any source evidence changed since Stage 2, halt and reconcile,
   not overwrite the target.
6. For live Apps and account sessions, plan a fresh sign-in to the new Auth
   project. A JWT from the old project must be rejected by the new backend.

## Exact environment-variable change set (approval required)

Frontend **Vercel production** (NEXT_PUBLIC variables are public by design):
- `NEXT_PUBLIC_SUPABASE_URL` -> new project's project URL.
- `NEXT_PUBLIC_SUPABASE_KEY` -> new project's **publishable/anon** key only.
- Keep `NEXT_PUBLIC_BACKEND_URL` pointing to the same approved Railway backend.
- Keep Stripe public variables unchanged and checkout disabled.

Backend **Railway production**:
- `SUPABASE_URL` -> new project's project URL.
- `SUPABASE_KEY` -> new project's publishable/anon key.
- `SUPABASE_SERVICE_ROLE_KEY` -> new project's secret service-role credential.
- Leave `DATABASE_URL`, `STRIPE_SECRET_KEY`, `FRONTEND_URL`,
  `OPENAI_API_KEY` and other unrelated settings untouched.
- Confirm `BILLING_CHECKOUT_ENABLED` is false; never enable paid checkout.
- Never expose the service role key in `NEXT_PUBLIC_*`, frontend builds,
  logs, GitHub, or ChatGPT.

The Vercel production build embeds `NEXT_PUBLIC_*` values at BUILD TIME. A
fresh build/redeployment is required after changing them. Coordinate Railway
backend and Vercel frontend so they converge on the same Auth issuer; mismatched
environments will reject valid user tokens. Avoid running frontend previews
against an incompatible live production backend.

## Proposed release sequence (separate explicit owner approval)

1. Identify active Vercel production project and all custom domains in its
   settings. Verify the approved app URL and local login flow.
2. Take privately stored configuration backups and record a deployment
   checkpoint, including Railway and Vercel revision IDs.
3. Freeze JobSleuth-only evidence edits briefly; DO NOT freeze or mutate
   PropNexus or the old Supabase Auth users.
4. Perform a final counts/schema/ownership read-only preflight and confirm
   new project's Auth profile and 4/3 records still match.
5. Prepare both platforms' new Supabase URLs and keys, keeping them in their
   secret managers; apply/redeploy in a short coordinated release window.
   Do not touch Stripe/DB connection variables outside the three Railway
   Supabase vars and two Vercel NEXT_PUBLIC vars above.
6. Open the Vercel frontend in a fresh browser/private session and sign in
   with the NEW project's password. Old sessions must not be reused.
7. Verify backend `/health` = 200; unauthenticated `/evidence`,
   `/users/me` and `/saved-jobs` return 401.
8. Verify authenticated `/users/me` returns the new account; `/users/me/plan`
   = free; `/evidence` shows 3 visible cards; `/candidate-profile` shows
   the private CV profile. Check all 4 underlying records still exist.
9. Test create/read/update/delete with a clearly synthetic evidence card owned
   by the test account, and delete that card at the end. Verify no other users
   can read it. Test saved-jobs: empty is `[]`, no fake success on failures;
   an invalid/nonexistent job ID returns 404. Do NOT seed fake production jobs
   merely to make this test pass.
10. Verify actual Vercel and Railway deployed versions, CORS, callback URLs,
    error rates and logs. Run the real vacancy-to-application analysis flow;
    log no applicant content or secrets. Checkout must remain disabled.
11. Lift the JobSleuth edit freeze only after all checks pass; keep old project
    data unchanged for rollback and historical record reconciliation.

## Rollback

Do not simply switch environment URLs back blindly: user activity on the new
project after cutover can create divergent records, and old/new session tokens
are not interchangeable. If an issue is detected, first halt new JobSleuth
writes, preserve changes from BOTH projects, assess ownership/deltas and secure
any new records, then restore the previously recorded matching Railway/Vercel
configuration and deployments in one coordinated operation. Require new login
and re-run smoke tests. Preserve the old shared project until an independently
approved deletion/retention decision.

**This file prepares the cutover; it does not authorize or deploy it.**
