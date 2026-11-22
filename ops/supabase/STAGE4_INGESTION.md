# Stage 4 — controlled public employer-board ingestion

**CURRENT STATUS: CODE-ONLY DRAFT, NOT LIVE.** No real vacancy data has been
imported or scheduled. First apply the reviewed additive schema to the
**dedicated** Supabase project, not the old shared PropNexus project.

## Source choice and rights gate

- Adapter: the [Greenhouse Job Board API](https://docs.greenhouse.io/job-board),
  `GET /v1/boards/{board_token}/jobs?content=true`, from a fixed HTTPS
  `boards-api.greenhouse.io` host. Official documentation states the GET
  endpoint returns public job-board postings; the application POST endpoint
  requires authentication.
- The public endpoint is intended for rendering employer job boards; public
  accessibility alone does **not** grant unrestricted commercial syndication.
  Before enabling a board in JobSleuth, confirm the employer's re-use/embedding
  permission or an appropriate agreement/terms, then document the operator's
  approval privately. Only allowlisted board slugs that meet that review may
  appear in `JOBSLEUTH_GREENHOUSE_BOARDS`.
- Do NOT ingest Adzuna, Reed, Civil Service Jobs or other third-party job
  aggregators without checking their specific licences and attribution rules.
- This importer stores a small plain-text excerpt (max 600 characters), title,
  source, company, location, source update time and a direct employer APPLY link.
  It does **not** ingest job seeker data, CVs or submissions, and does not
  fabricate advertised salary, AI score or posting date.
- Example metadata-only configuration format (illustrative ONLY; employers
  listed here are NOT automatically approved): `heatgeek=Heat Geek,rightmovecareers=Rightmove`.
  The importer has **no default boards**.

## Schema, safeguards and lifecycle

1. `ops/supabase/stage4_jobs_ingestion.sql` adds `source_board`,
   `external_id`, `is_active`, `last_seen_at`, `source_updated_at`,
   a unique key on (source, board, external ID), and index for live jobs.
   The old `jobs.id` remains bigint, and foreign-keyed `saved_jobs` records
   are never deleted by ingestion.
2. `GET /jobs` and `GET /jobs/{id}` only show active postings. Expired
   postings remain in the database for saved-job history; the UI may need a
   separate 'no longer available' label.
3. Feed fetches use fixed Greenhouse hostname, no redirects, strict board slugs,
   HTTP error handling, payload size/count checks, country/UK location checks,
   official apply URLs and stripped/shortened descriptions.
4. Deduplicate within boards and in PostgreSQL through unique upserts. A
   successful re-fetch refreshes `last_seen_at` without changing `created_at`.
   An absent posting is marked inactive only after >72 hours and a successful
   complete non-empty board scan. If upstream fails or UK data is malformed,
   do not expire any listings. No hard deletions.
5. No cron job is enabled by this PR. A *separate* scheduling design can run
   daily with a least-privilege backend-only secret, alert on nonzero exit,
   and report feed counts, source failures and last success. NEVER put a
   service-role key into public browser/client variables or GitHub logs.

## Private operator commands (not run in production automatically)

From `backend/` with a vetted source-board list set privately:

```sh
python -m scripts.ingest_greenhouse
```

This is dry-run only. An apply **additionally** requires BOTH
`JOBSLEUTH_FEED_RIGHTS_CONFIRMED=true` and
`JOBSLEUTH_INGEST_ENABLED=true`, plus valid backend Supabase credentials,
and the approved schema having been applied:

```sh
python -m scripts.ingest_greenhouse --apply
```

Do not turn these flags on until the source licence has been reviewed and a
runbook/rollback checkpoint approved. The importer never changes old Supabase
project records or user accounts. Check feed health and actual employer apply
URLs before marketing the listings as complete.

## Acceptance

- CI unit tests use a synthetic Greenhouse API; no external network, paid
  services or customer data.
- Validate schema/RLS against a disposable Postgres test database.
- Confirm repeated imports preserve stable job IDs; missing jobs become inactive
  only after grace period; the Saved Jobs relation is intact; API does not
  expose inactive jobs; and unapproved feeds cannot write.
- Before live activation, run read-only publisher rights and source endpoint
  checks; apply a tracked schema migration; conduct a private dry run; then
  authorise first incremental import and daily monitoring separately.
