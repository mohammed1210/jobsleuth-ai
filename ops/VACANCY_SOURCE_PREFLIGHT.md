# Vacancy expansion preflight — 24 November 2026

Scope: research and read-only contract verification. No new live provider, database
write, paid service, scheduler or credentials. Current main includes the DfE pilot
and the guided Apply UX is being developed separately in PR #108.

## Stage 1: DfE refresh safety (#100)

Reviewed backend/lib/dfe_ingestion.py, backend/scripts/ingest_dfe.py and
ops/supabase/STAGE4_DFE_FEED.md. The latter records 100 imported pilot rows on
23 November, 96 expanded descriptions, and 72 salary texts. These are historical
verified counts, not a fresh production query. Existing code checks metadata
consistency, unique source IDs, and persistence before absence expiry. Partial
page-one pilot cannot deactivate absent jobs; published closing time remains
independent via live_jobs.

Do not relax the full-scan check merely to increase counts. The provider's
publish_on-only sort can shift across page boundaries (#100). Request a
supported stable cursor, deterministic tie-break or snapshot contract. If not
available, design a separately approved bounded upsert-only refresh and
individual official detail checks; never infer withdrawal from a partial scan.
Verify concurrent-run safety, daily rate limits, repeated full scans and
failure handling before scheduling. Review source expiry without touching
saved jobs or user evidence. Issue #100 remains open.

## Stage 2: source permissions register

Reviewed official documentation on 24 November 2026. A documented right to
display does not automatically establish permission to forward raw adverts to
a third-party AI processor or retain them indefinitely.

| Source | Display / storage | Remaining gates |
| --- | --- | --- |
| Himalayas | Terms clause 113 explicitly permits commercial own-site display; caching encouraged. | Preserve exact applicationLink, link credit to Himalayas, remove expired jobs, no onward syndication including Google Jobs/JobPosting. Confirm AI processor and saved-history retention. |
| DfE Find an Apprenticeship | Display Advert v2 explicitly recommends retrieving and storing adverts in one's own database. | Owner creates API account and acknowledges terms, backend key, verify AI/commercial context and attribution/retention, respect 150 requests/5 minutes. |
| YubHub | API declares CC BY 4.0 and free access; source credit required. | Confirm licence chain for employer descriptions, AI processing and timely withdrawal; do not assume all underlying rights. |
| We Work Remotely | Public RSS permitted with backlinks. | Confirm persistent storage, paid AI assistance, closure and UK eligibility. |
| NHS Jobs | Official XML/RSS self-serve primarily documented for employers; national job-board sharing supported. | Confirm national third-party access, licence, retention, terms, AI rights and costs. |
| Civil Service Jobs | GOV.UK publishing standard identifies OGL availability. | Identify authorised actual outbound feed, dataset-specific terms and third-party exclusions. |
| Reed / Jooble | API documented, commercial scope unresolved for our intended use. | Written rights confirmation before activation. |
| Indeed | No verified unrestricted download/republication agreement. | No scrape or unofficial scraping API. |

Official references:
- https://himalayas.app/api
- https://himalayas.app/terms (clause 113)
- https://himalayas.app/docs/openapi.json
- https://developer.apprenticeships.education.gov.uk/
- https://developer.apprenticeships.education.gov.uk/Documentation/display-advert-api-v2
- https://developer.apprenticeships.education.gov.uk/third-party-accounts/terms-conditions
- https://developer.apprenticeships.education.gov.uk/third-party-accounts/register
- https://yubhub.co/api/
- https://weworkremotely.com/remote-job-rss-feed
- https://www.nhsbsa.nhs.uk/about-nhs-jobs/nhs-jobs-integration-and-benefits
- https://www.gov.uk/government/publications/open-standards-for-government/publishing-vacancies-online-standards-profile--2

### Himalayas first technical milestone

Run from backend: python -m scripts.probe_himalayas

This fetches one official GB-filtered search page without a key and returns
aggregate counts only. No production database connection or writes. The
reported unexpired count is based on the advertised expiry time only, not
proof of current availability or a complete UK catalogue. Search filtering
comes from the publisher, not independently validated by this probe.
The web research endpoint request was inaccessible; a real operator/CI
probe remains required. No live result count asserted.

Before implementing a writer: establish stable GUID semantics (OpenAPI
example and detail URL prose differ); preserve exact applicationLink and
source credit, validate salary currency/period, UK location and timezone
eligibility, sanitize text. Search pages shift; totals are approximate.
Never expire from absent results alone. Individual official endpoint
returns 410 for closed jobs; respect that signal and expiryDate. Ensure
expired listings are removed from public display and assess whether saved
history needs a minimal tombstone instead of retaining full copied adverts.
Do not send provider content to external AI until scope is clear; no
syndication or structured-data export. Rate limits: keyed 60/minute and
10,000/day; anonymous limits lower. Cache and respect Retry-After.

## Stage 3: permission requests (drafts only, not sent)

### NHS Jobs — via official contact page
https://www.nhsbsa.nhs.uk/contact-nhs-jobs

Subject: NHS Jobs authorised vacancy feed for UK careers platform

We are developing JobSleuth, an independent UK job discovery and application
support service. Could you confirm whether we may access an authorised
national XML/RSS or JSON feed of public NHS Jobs vacancies, including full
advert text, closing dates and application links? Vacancy search and original
application links will remain free, with clear NHS Jobs source attribution.
We may separately offer optional paid CV and application assistance.

Please confirm the access method, any registration or fees, permitted
commercial display and local caching, withdrawal/retention requirements,
and whether user-requested AI analysis through a contracted processor is
permitted. We will not import applicant data, internal adverts, logos or
submit applications automatically. Please provide applicable terms and any
technical specification or publisher agreement.

### Civil Service Jobs — via official support/contact channel

Subject: Authorised Civil Service Jobs vacancy feed and reuse terms

We are developing JobSleuth, an independent UK careers platform that helps
candidates understand vacancy requirements and prepare applications. GOV.UK's
publishing vacancies guidance identifies Civil Service Jobs data as available
under the Open Government Licence. Could you direct us to the authorised
outbound vacancy feed/API and confirm which fields and adverts the licence
covers?

We intend to display public vacancies and original application links free of
charge, with attribution and timely removal. Optional paid application tools
would be separate. Please confirm bulk access, storage/refresh limits,
third-party exclusions, commercial display and user-requested AI analysis,
and any registration or cost. We do not seek applicant information or
permission to bypass access controls.

## Release sequence

1. Review this preflight and run fixture tests; independently validate the
   live one-page Himalayas contract and fix any mismatch.
2. Resolve Himalayas lifecycle and attribution/AI gates, then implement
   disabled-by-default adapter on a dedicated reviewed PR.
3. Owner registers for apprenticeship Display Advert v2 and stores key
   privately; then run bounded read-only validation.
4. Send reviewed NHS/Civil Service permission requests only with owner
   approval. No ingestion until documented permission and release approval.
5. Resolve DfE #100 before full refresh; no weakening of expiry protections.

No production settings, live data, billing or existing Apply work changed.
