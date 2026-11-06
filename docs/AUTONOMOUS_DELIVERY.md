# JobSleuth: controlled autonomous delivery

## Objective

Move from ad hoc conversations and PR-by-PR fixes to a small, repeatable improvement cycle. Preserve the evidence-grounded Apply workflow and prioritise a real five-user pilot before speculative features.

## Existing tools (reviewed 2026-11-06)

- **GitHub**: source of truth for code, PRs, CI, Codex reviews and backlog. Main already has Backend CI, Frontend CI, PR Labeler and weekly CodeQL.
- **Railway**: production backend is sourced from `main`. Check deployment freshness and health before claiming any PR is live.
- **Vercel**: frontend deployment and preview checks need independent verification; passing GitHub CI alone is not proof of end-to-end success.
- **ChatGPT scheduled engineering review**: a daily task can review status and attempt bounded PR work when its tool access permits. Do not assume it has a persistent machine, uninterrupted runtime or a connected coding sandbox.
- **Railway cloud-agent automations**: not enabled for the connected JobSleuth Railway account on 2026-11-06. Do not assume this runs.

## Daily operating sequence

1. Refresh repository `main`, open PRs, review threads, failing checks, outstanding GitHub issues, latest Railway deployment and any pilot feedback. Work from fresh state, not chat memory.
2. Prioritise one high-impact item: **P0 incident > P1 evidence/eligibility/auth/privacy issue > common-path pilot blocker > billing safety > regression coverage > cosmetics**.
3. Choose the smallest independently testable fix. Prefer existing issues, especially #90, #88, #60 and #48. Avoid duplicate PRs.
4. Make changes on a new topic branch. Include tests and a short reproduction/acceptance checklist. Open a draft PR; never push directly to `main`.
5. Let Backend CI, Frontend CI and relevant GitHub checks run. Fix P0/P1 and common-path P2 findings, but defer theoretical P2 parser variations unless observed in real pilot use.
6. Request human review at the merge gate. Check deployment status, live `/health` and end-to-end smoke flow after an approved release.
7. Record what was accomplished, proof (checks/links), blockers, and one next action. Do not report an unmerged PR as shipped.

## Non-negotiable approval gates

- No unattended PR merging, branch-protection changes, production deployments, database migrations, paid service provisioning or account/billing activation.
- No modifying secrets, webhook signing configuration, Stripe prices, paid entitlements or access controls without review.
- Keep checkout disabled until #88 acceptance criteria and a genuine Stripe test-mode checkout/webhook lifecycle are verified.
- Never put candidate CVs, vacancy texts, Evidence Cards, drafts, credentials or personal pilot records in issues, CI logs or external tooling.
- No generated accomplishments or unsupported claim inflation. Maintain explicit distinction between personnel management and management of risks/projects.
- If authentication, Vercel access, Supabase permissions, testing or code-execution capability is missing: record the limitation rather than claiming completion.

## Review checklist before each merge

- [ ] Change is small and linked to an issue or documented user-observed defect
- [ ] P0/P1 Codex issues resolved; common-path P2 addressed when feasible
- [ ] Backend CI green
- [ ] Frontend CI green
- [ ] Security/data exposure reviewed for auth, billing, evidence or database changes
- [ ] Any migration has a rollback plan and explicit approval
- [ ] Reviewer has confirmed deployment implications

## Current priorities and release order

1. Reconcile **PR #90** with latest `main`; finish verified Stripe lifecycle persistence, but keep checkout disabled.
2. Close **issue #88** safety work only after authenticated checkout/portal, server-side feature gates, test catalogue and real sandbox lifecycle checks are proven.
3. Confirm frontend and backend deployments correspond to intended commits; establish post-deploy smoke checks.
4. Run **issue #60** five-tester pilot and collect anonymised outcomes. An actual payment signal is distinct from stated willingness to pay.
5. Keep **issue #48** review debt bounded by observed P1 issues; do not indefinitely delay pilot validation for speculative P2s.
6. Reassess scope and monetisation only after the pilot decision gate in **issue #13**.

## Automation coverage

- `.github/workflows/daily-regression.yml` (proposed): scheduled read-only backend tests and frontend build/tests; also supports manual dispatch. Runs only after it is merged into the default branch.
- The daily ChatGPT task performs opportunistic review and isolated PR work; its ability to edit/test code must be confirmed from an actual scheduled execution.
- GitHub Actions are checks, **not** a general-purpose coding agent; red CI does not automatically repair code.

## Progress ledger template

Date | Latest main SHA | Backend deployed SHA/date | Open PRs | Checks | Work performed | Approval needed | Next single priority

## What the owner retains

Human decisions on pricing, spending, real user invitations, live payment activation, significant scope changes and production release approval. The agent prepares evidence and PRs for those decisions.
