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
python -m scripts.ingest_dfe             # no writes
```

Requires full paginated scan. Apply uses the NEW Supabase backend secret in
the approved operator environment and only after review and tracked migration:

```sh
JOBSLEUTH_INGEST_ENABLED=true \
JOBSLEUTH_DFE_INGEST_ENABLED=true \
JOBSLEUTH_DFE_OGL_TERMS_ACK=true \
python -m scripts.ingest_dfe --apply
```

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
