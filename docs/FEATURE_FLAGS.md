# Feature Flags

JobSleuth AI uses feature flags to control the rollout of new features and enable/disable functionality without code changes.

## Available Flags

All feature flags are environment variables with the `NEXT_PUBLIC_FEATURE_` prefix. They are SSR-safe and can be used in both client and server components.

### `NEXT_PUBLIC_FEATURE_AI_FIT`

**Default:** `false`

Controls the AI-powered job fit scoring feature. When enabled, users can see personalized job match scores based on their resume and preferences.

**Usage:**
- Job detail page: Shows AI Fit panel with score and factors
- Job listings: Can sort/filter by fit score

**Dependencies:**
- Requires `OPENAI_API_KEY` to be set in backend
- Falls back to heuristic scoring if OpenAI is unavailable

### `NEXT_PUBLIC_FEATURE_RESUME_TOOLS`

**Default:** `false`

Enables resume enhancement and cover letter generation tools.

**Usage:**
- Resume bullet point suggestions
- Cover letter generation tailored to specific jobs
- Resume analysis and improvement tips

**Dependencies:**
- Requires `OPENAI_API_KEY` for best results
- Basic functionality works without API key

### `NEXT_PUBLIC_FEATURE_DIGESTS`

**Default:** `false`

Enables email digest subscriptions for job alerts.

**Usage:**
- Users can subscribe to daily/weekly/monthly job digests
- Customizable filters (location, salary, type, etc.)
- Digest management in account settings

**Dependencies:**
- Requires `RESEND_API_KEY` or email service configuration
- Backend `/digests/run` endpoint must be set up

### `NEXT_PUBLIC_FEATURE_SCRAPE_INTERNAL`

**Default:** `false`

Enables internal web scraping using Playwright as a fallback/supplement to external job APIs.

**Usage:**
- Scrapes job boards directly when provider APIs are unavailable
- Provides more comprehensive job coverage
- Rate-limited and respects robots.txt

**Dependencies:**
- Requires Playwright installation in backend
- Optional: `PROXY_URL` for distributed scraping
- `HEADLESS=true` recommended for production

## Implementation

### Frontend (Next.js)

Feature flags are implemented in `frontend/lib/flags.ts` with SSR-safe helpers:

```typescript
import { getFeatureFlag } from '@/lib/flags';

// In a React component
const showAIFit = getFeatureFlag('AI_FIT');

if (showAIFit) {
  return <AIFitPanel />;
}
```

### Backend (FastAPI)

Backend can check flags via environment variables:

```python
from backend.lib.settings import settings

if settings.FEATURE_AI_FIT:
    # AI fit scoring logic
    pass
```

## Configuration

### Development

Set flags in `.env.local`:

```bash
NEXT_PUBLIC_FEATURE_AI_FIT=true
NEXT_PUBLIC_FEATURE_RESUME_TOOLS=false
NEXT_PUBLIC_FEATURE_DIGESTS=false
NEXT_PUBLIC_FEATURE_SCRAPE_INTERNAL=false
```

### Production (Vercel)

Set environment variables in Vercel dashboard or via CLI:

```bash
vercel env add NEXT_PUBLIC_FEATURE_AI_FIT
```

### Production (Railway - Backend)

Set environment variables in Railway dashboard or via CLI:

```bash
railway variables set FEATURE_AI_FIT=true
```

## Best Practices

1. **Default to `false`**: New features should be disabled by default
2. **Gradual Rollout**: Enable for internal testing first, then beta users, then all users
3. **Monitor Impact**: Track feature usage and performance impact
4. **Clean Up**: Remove flags once features are stable and rolled out to 100%
5. **Document Dependencies**: Always document external service dependencies

## Testing

Feature flags can be overridden in tests:

```typescript
// Jest/Vitest
process.env.NEXT_PUBLIC_FEATURE_AI_FIT = 'true';
```

```python
# Pytest
@pytest.fixture
def enable_ai_fit(monkeypatch):
    monkeypatch.setenv('FEATURE_AI_FIT', 'true')
```

## Troubleshooting

### Flag Not Working

1. Ensure the environment variable is prefixed with `NEXT_PUBLIC_` for frontend flags
2. Restart dev server after changing `.env.local`
3. Check that the flag is properly imported and used
4. Verify flag name matches exactly (case-sensitive)

### Feature Partially Working

1. Check for required dependencies (API keys, services)
2. Review backend logs for errors
3. Ensure both frontend and backend flags are aligned if feature spans both
