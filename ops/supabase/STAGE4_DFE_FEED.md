# UK Department for Education Teaching Vacancies (OGL v3) feed

**Draft-only / not deployed / no real vacancies imported.** This is a second
source option stacked on Stage 4's Greenhouse PR #98. No API secret required.
Source contract grounded in DfE's public GitHub repo:
- https://github.com/DFE-Digital/teaching-vacancies/blob/main/app/controllers/api/vacancies_controller.rb
- https://github.com/DFE-Digital/teaching-vacancies/blob/main/app/views/api/vacancies/index.json.jbuilder
- https://github.com/DFE-Digital/teaching-vacancies/blob/main/app/views/api/vacancies/_show.json.jbuilder
- https://github.com/DFE-Digital/teaching-vacancies/blob/main/app/views/pages/terms-and-conditions.html.slim

## Licence and user protections

DfE states job listing data may be republished on third-party sites under
[Open Government Licence 3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/).
The **API terms were last updated 9 July 2026** and explicitly prohibit
any fee or commission for contacting, interviewing, or hiring a respondent to
reused DfE listing data. JobSleuth's published DfE vacancy listings and their
direct employer application links must be **free to access**. JobSleuth's
optional paid CV writing tools are separate; do not make access/contact/apply
contingent on purchase or suggest DfE endorsement.

Display attribution: “Source: Department for Education — Teaching Vacancies.
Contains public sector information licensed under the Open Government Licence
v3.0.” Link to the OGL licence and the original vacancy. Re-check terms
before enabling a feed, and keep an auditable licence/version reference.

The API terms note that a valid Referrer header must be sent. The importer
supplies the actual public JobSleuth origin; DO NOT spoof an employer's domain.
This is a general England school-teaching and school support roles feed,
NOT comprehensive public/civil service or UK-wide vacancies.

## Protocol and validation

- GET only to fixed `https://teaching-vacancies.service.gov.uk/api/v1/jobs.json?page=N`
  with Accept JSON, real JobSleuth Referrer. No arbitrary URLs or redirects.
- Pagination contract: `openapi: 3.0.0`, `data[]`, `meta.count` and
  `meta.totalPages`. DfE server defaults to 100 max jobs per page.
- Max 200 pages / 20k vacancies and 1.5 MB per response for bounded use;
  count/shape must be consistent on every page. If the service shifts during
  the scan, refuse writes and expiry, not silently import partial data.
- Records come from actual schema.org `JobPosting` fields; verified country
  `GB`, official DfE /jobs/{slug} URL, verified employer and location,
  explicit annual GBP salary when available, date posted/valid-through.
  Never invent publication times, salary bands, descriptions or AI scores.
- `validThrough` is authoritative; an already-expired post is imported
  as inactive immediately. A no-longer-listed post is only deactivated
  after >72h of absence, with successful full-scan verification.
- Source identity tuple `(source=dfe_teaching_vacancies,
  source_board=england, external_id=slug)`, with unique upsert index from PR #98.
  No deletion of saved jobs or changes to user/application records.
- No cron or production SQL migration is enabled in this PR.

## Operator dry run and separately gated apply

```sh
cd backend
python -m scripts.ingest_dfe             # strict full-scan dry run; expected to fail closed if pagination overlaps
python -m scripts.ingest_dfe --pilot     # page-one-only preview, no writes
```

Requires full paginated scan. Apply uses the NEW Supabase backend secret in
the approved operator environment and only after review and tracked migration:

```sh
JOBSLEUTH_INGEST_ENABLED=true \
JOBSLEUTH_DFE_INGEST_ENABLED=true \
JOBSLEUTH_DFE_OGL_TERMS_ACK=true \
python -m scripts.ingest_dfe --apply
```

### Bounded first-page pilot while pagination is unstable

**Do not import using the full-scan path** until a complete stable scan can be
verified. The DfE API sorts by publication date alone; equal dates can overlap
between pages. As confirmed in the 22 November 2026 read-only GitHub Actions
probe, the full scan failed with `Incomplete, shifting or duplicate DfE pages`.
The full-scan path intentionally fails closed and must not be weakened.

The explicit `--pilot` option reads ONLY page one (at most 100 vacancies) and
validates each item; it reports `scope=first_page_only`, source total and
page count. A pilot is NOT the full feed, does not prove coverage, and NEVER
deactivates jobs because they are absent from the current first page. Advertised
closing times remain stored and enforced by `public.live_jobs` independently
of refreshes. Earlier withdrawal of a posting before its advertised deadline
cannot be inferred from this partial scan: a separate link/manual check is
required before calling a pilot listing verified.

Pilot writing requires ALL four explicit backend-only flags, tracked schema
migration and separate release approval:

```sh
JOBSLEUTH_INGEST_ENABLED=true \
JOBSLEUTH_DFE_INGEST_ENABLED=true \
JOBSLEUTH_DFE_OGL_TERMS_ACK=true \
JOBSLEUTH_DFE_PILOT_ENABLED=true \
python -m scripts.ingest_dfe --pilot --apply
```

For the initial release, verify the original application URLs and save/remove
flows against this small set before introducing any refresh scheduler.
`--pilot` must never be repurposed into full-feed missing-job expiry.

Never run these with real credentials in public CI or log private service keys.
Get explicit release approval before enabling imports or automation; acknowledge
OGL and third-party data retention/copyright exceptions.

## Testing / release gate

Offline synthetic HTTP regression tests must pass, plus Stage4 underlying
Postgres/RLS migration checks. Before live import, run a no-write DfE API
probe, confirm the Referrer is accepted and that actual JSON shape still
matches the repository source. If this cannot be verified, do not apply
or claim JobSleuth has imported DfE vacancies. Start with no scheduler,
monitor counts, then schedule daily refresh only after source and post-save
workflows pass end-to-end.

## Automatic closing-time enforcement (critical safety guarantee)

Stage 4 additive migration also adds `public.jobs.expires_at` and a
`public.live_jobs` view with PostgreSQL 15+ `security_invoker=true`.
The view filters already-closed posts with `expires_at > now()`, **even if
no refresh job ever runs again**. The public Jobs API and save-new-job checks
read this view. Historical `public.saved_jobs` still joins the base jobs
table so users may review closed saved adverts; the UI disables its original
application link once expiry has passed. Dedicated project RLS remains
in effect for the view's underlying table. This view and the SQL migration
MUST be applied together with the code release. Neither is applied yet.

### Location omissions observed in live full feed

Some DfE JobPosting rows have valid GB country codes but omit both locality
and region. The importer retains these adverts using the provided postcode
if available; otherwise it displays “England (specific location not
provided)”. Do not infer a town, or incorrectly exclude a legitimate
publisher's posting. Saved-job cards refresh on closing-time timers and
browser focus, so old tabs do not retain active Apply links indefinitely.


## 23 November 2026 — licensed vacancy UX and source enrichment

- Active job cards now offer **Help me apply** directly into JobSleuth's existing
  `/apply/vacancy?job=<ID>` workflow, in addition to the always-free original
  application link. Source data is fetched by ID from our own public API,
  not accepted as untrusted query-string HTML or third-party redirect targets.
- After sign-in, the job's employer, location, salary (when provided),
  closing date, official URL and DfE-supplied description prefill the vacancy
  workspace. Existing unsaved/saved draft work is never overwritten without
  an explicit replace action. The user must review and extract before analysis;
  **no fictitious AI percentage or auto-submission**.
- DfE's published `JobPosting.description` is now HTML-stripped and kept up
  to a clearly disclosed bounded 40,000 characters rather than silently clipped
  at 600. DfE's JSON may not include the entire rendered job page; the official
  original remains the authoritative place for all instructions.
- DfE `baseSalary.value.value` may be employer-authored GBP annual text
  (e.g. "£68,691.00 - £77,676.00 Annually (Actual)"). Preserve that text
  and infer amounts only when explicitly written; do not estimate or create
  an AI-generated pay band.

### One-time backfill of the *existing* 100 source records

The 22 November pilot imported 100 jobs using the old 600-character cap
and numeric-only salary parser. Updating the code alone **does not change**
those existing rows. Backfill must not be confused with importing a fresh
first page (which shifts), and it must not deactivate any missing postings.

- Use `python -m scripts.backfill_dfe_existing --max-records 100` as a **dry run**
  from a private, configured JobSleuth backend environment. It selects only
  already-imported DfE IDs and checks the DfE *individual* job API for each.
  It reports aggregate counts and changes no data.
- A real individual-job API read check is enforced by the Backend CI job
  on PR #101. This is not proof that all 100 old URLs remain accessible.
- To apply *after* a successful dry run and separate release review:
  `JOBSLEUTH_INGEST_ENABLED=true`,
  `JOBSLEUTH_DFE_INGEST_ENABLED=true`,
  `JOBSLEUTH_DFE_OGL_TERMS_ACK=true` and
  `JOBSLEUTH_DFE_BACKFILL_ENABLED=true`, with the command's `--apply`
  flag, in a controlled one-off operator process.
- The backfill performs only guarded updates to existing DfE jobs' salary
  and description fields. It inserts **zero** new jobs, changes **zero**
  users/saved-jobs/applications, never deactivates missing IDs and never
  schedules itself. Any individual publisher identity mismatch refuses writes.
- Confirm aggregate coverage and handoff functionality before considering
  any later scheduled ingestion; issue #100's full-feed pagination remains blocked.
- Do not expose database service keys, copied job content, API responses or
  authentication tokens in CI logs or client-side variables.
