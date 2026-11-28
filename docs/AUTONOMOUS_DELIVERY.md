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
4. Prefer an existing PR branch. Use at most two active engineering PRs; create a new branch only for an existing defect without a suitable PR. Include tests and an acceptance checklist. Never push directly to `main`.
5. Run latest-head CI and relevant checks. Resolve actionable review findings with regression evidence; request fresh review after substantive changes. Do not merge merely because CI is green.
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

## Current priorities and release order (2026-11-28)

1. Verify guided Apply and draft retention in production; address semantic timeout, eligibility classification and drafting quality under existing work.
2. Clear remaining review debt: #92 guardrails, #95 migration security/supersession, #109 source rights, #90 billing. Keep payment and feed activation separately gated.
3. Track #102 security, #93 deployment freshness, #116 stale analysis, #117 eligibility, #118 matcher modifiers, #106 draft quality and #48 review debt.
4. Keep #60 pilot, #13 scorecard and other milestone issues open until their acceptance criteria are demonstrated.
5. Audit stale branches against merged PR heads, branch protection, open PR dependencies and deployment pins. Preserve closed-unmerged and security branches. Enable automatic head-branch deletion in repository settings only by owner action. Never overwrite a branch to simulate deletion.

## Automation coverage

- `.github/workflows/daily-regression.yml` (proposed): scheduled read-only backend tests and frontend build/tests; also supports manual dispatch. Runs only after it is merged into the default branch.
- The daily ChatGPT task performs opportunistic review and isolated PR work; its ability to edit/test code must be confirmed from an actual scheduled execution.
- GitHub Actions are checks, **not** a general-purpose coding agent; red CI does not automatically repair code.

## Progress ledger template

Date | Latest main SHA | Backend deployed SHA/date | Open PRs | Open issues | Branches | Checks | Work performed | Approval needed | Next single priority

## What the owner retains

Human decisions on pricing, spending, real user invitations, live payment activation, significant scope changes and production release approval. The agent prepares evidence and PRs for those decisions.
