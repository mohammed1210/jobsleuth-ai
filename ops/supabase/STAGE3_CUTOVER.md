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
- NEW project contains **zero** saved jobs and zero subscription rows.
  This dependent PR replaces the demo `/jobs` backend with database-backed
  public-read queries, so its response is an honest empty list until actual
  vacancy ingestion is enabled. No real jobs have been imported. Do not seed
  fake jobs merely to make Saved Jobs tests pass; verify real ingestion
  separately before the launch.
- Railway service `jobsleuth-ai` is online on `main` with root `backend`.
  Its variable names include `SUPABASE_URL`, `SUPABASE_KEY`,
  `SUPABASE_SERVICE_ROLE_KEY`, `DATABASE_URL`, `FRONTEND_URL` and
  `STRIPE_SECRET_KEY`. OAuth connector access shows names, **not values**,
  so the connection URL was not independently checked at this audit.
  `DATABASE_URL` is not referenced by current backend application code per
  GitHub code search. **Do not overwrite it** without proving its owner/use.
- VERIFIED 22 November 2026: Vercel access is NOW connected and read-only.
  Team `mohammed-abbas-projects-8ab7e126`, project `jobsleuth-ai`
  (ID `prj_i7d9iVkepLHSnAHVyTP2tKRnYkdu`). Public production domain
  `jobsleuth-ai.vercel.app` was verified. Latest READY production deployment
  `dpl_8Jes4fhgzxHfgdeasQcJu8viop57` matches main commit
  `ea7fa74b380f5a28c63c53d12671040087523c52`; PR #96/#97 previews
  are NOT production deployments.
- VERIFIED read-only Vercel project env values and scopes:
  `NEXT_PUBLIC_SUPABASE_URL` currently points to OLD shared project
  `wsfemkhxttddztnhthkc`, NOT the isolated project.
  `NEXT_PUBLIC_SUPABASE_KEY` is an `anon` JWT key, not a service-role key.
  `NEXT_PUBLIC_BACKEND_URL` points to the Railway production HTTPS domain.
  `NEXT_PUBLIC_API_URL` is defined but has no value; do not rely on it for
  cross-service routing. Both Supabase variables and the backend URL currently
  target **development, preview AND production**. Split/update targets carefully
  during an approved release; changing one shared variable can affect all
  deployment environments. No env values or credentials are recorded here.
- Dedicated Supabase has two enabled frontend-compatible keys: a modern
  publishable key and a legacy anon key. The new service-role credential is
  NOT available via the connected Supabase management tools; it must be
  supplied privately into Railway's secret manager, never pasted into ChatGPT
  or GitHub. Before release, validate new public key/project URL pairing and
  privately store an authorised rollback copy of both platforms' old values.
  Service_role must never appear in `NEXT_PUBLIC_*`.
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
4. VERIFIED on Vercel: production Supabase URL still points to OLD shared
   project; public key is anon and backend URL targets Railway. Do NOT switch
   only Vercel (or only Railway): old/new JWT issuers will disagree. Record
   existing Railway/Vercel variable names and *secure backup of values*
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

1. VERIFIED: the Vercel project is `jobsleuth-ai`; current production
   domain is `jobsleuth-ai.vercel.app`, and last READY production deployment is
   `dpl_8Jes4fhgzxHfgdeasQcJu8viop57` on `main`. Before switching,
   recheck these IDs and verify the approved live app URL/callback configuration.
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

## 22 November 2026 go/no-go snapshot

| Gate | Current read-only finding | Release status |
|---|---|---|
| New Supabase schema and private records | One verified Auth account; 4 evidence cards; 3 test feedback rows | PASS |
| New Supabase job inventory | 0 real jobs; 0 saved jobs | Expected empty; real ingestion needed for end-to-end save tests |
| Vercel production project | Identified, GitHub main deployed and ready | PASS |
| Frontend production Supabase identity | Points to old mixed-use project | Requires coordinated change |
| Frontend public key exposure | Correctly classified as anon, not service_role | PASS for current config |
| Vercel backend URL | Existing Railway production HTTPS service | PASS |
| Railway production environment values | Names visible, sensitive values redacted | Must verify privately during release |
| Frontend/build code | PRs #96 and #97 draft/unmerged, tests passed | Merge/release approval still required |
| Supabase Auth advisor | Leaked-password protection disabled | Resolve before external pilot |
| Live paid checkout | Not enabled; Stripe migration separate | MUST STAY OFF |

**No-go until explicit owner approval** to merge/release the reviewed PRs and
coordinate Railway + Vercel in one controlled production cutover. The owner
has authorized Stage 3 investigation and preparation, NOT an implicit secrets
rotation, redeployment, or automatic billing activation. Fresh login and
app-level Evidence Bank checks remain post-cutover smoke tests.
