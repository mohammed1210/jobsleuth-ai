# JobSleuth MVP Plan

## Complete

- App Router only frontend structure under `frontend/app`.
- FastAPI backend entrypoint at `backend/main.py`.
- Health, config, and guarded debug route diagnostics.
- Job listing and detail endpoints with mock seed data and filter-ready structure.
- Saved jobs API using Supabase access tokens from `Authorization: Bearer` headers.
- AI score, resume improvement, and cover-letter endpoints with deterministic fallback output when OpenAI is not configured.
- Stripe checkout, billing portal, and webhook routes with safe `{ok: false}` responses when Stripe is not configured.
- Supabase magic-link frontend flow using `supabase.auth.getSession()`.
- Free, Pro, and Career Plus pricing UI.
- Analytics placeholder widgets with premium locked states.
- Lean frontend/backend CI.

## Stubbed

- Job data uses mock seed data when Supabase jobs are unavailable.
- Subscription status is a placeholder until webhook persistence is connected.
- Billing portal requires a Stripe customer ID lookup before production use.
- Email digest route imports and calls `send_digest_email`, but SMTP vars are optional and missing vars no-op.
- AI features use deterministic fallbacks without `OPENAI_API_KEY`.

## Next Sprints

1. Persist jobs, saved jobs joins, user profiles, and subscriptions in Supabase.
2. Store Stripe customer IDs and subscription status from webhooks.
3. Add application tracking and analytics rollups.
4. Add resume/profile onboarding to improve AI match scoring.
5. Add digest preferences and scheduled digest execution.

## Monetisation Path

- Free: browse jobs, basic filters, limited saves.
- Pro: unlimited saved jobs, AI scores, resume improvements, digest readiness.
- Career Plus: analytics, salary fit tracking, priority matches, workflow exports.
