# Feature Flags

JobSleuth AI uses environment-based feature flags to control the availability of features. All flags are SSR-safe and default to `false` when unset.

## Available Flags

### `NEXT_PUBLIC_FEATURE_AI_FIT`
- **Default**: `false`
- **Description**: Enables AI-powered job fit scoring on job detail pages
- **Impact**: Shows/hides the AI Fit panel that displays match percentage and reasoning

### `NEXT_PUBLIC_FEATURE_RESUME_TOOLS`
- **Default**: `false`
- **Description**: Enables resume suggestion and cover letter generation tools
- **Impact**: Shows/hides resume tools in the application flow

### `NEXT_PUBLIC_FEATURE_DIGESTS`
- **Default**: `false`
- **Description**: Enables email digest subscription and management
- **Impact**: Shows/hides digest configuration in account settings

### `NEXT_PUBLIC_FEATURE_SCRAPE_INTERNAL`
- **Default**: `false`
- **Description**: Enables internal Playwright-based scraping (fallback to provider APIs when disabled)
- **Impact**: Backend scraping behavior; controls whether to use internal scraper

## Configuration

Add these environment variables to your `.env.local` (frontend) or deployment environment:

```bash
# Enable all features
NEXT_PUBLIC_FEATURE_AI_FIT=true
NEXT_PUBLIC_FEATURE_RESUME_TOOLS=true
NEXT_PUBLIC_FEATURE_DIGESTS=true
NEXT_PUBLIC_FEATURE_SCRAPE_INTERNAL=true
```

## Usage

### Frontend (React/Next.js)

```typescript
import { featureFlags } from '@/lib/flags';

// In a component
if (featureFlags.aifit) {
  return <AIFitPanel />;
}

// In server components
if (featureFlags.resumeTools) {
  return <ResumeToolsSection />;
}
```

### Backend (Python/FastAPI)

```python
from lib.settings import settings

if settings.FEATURE_SCRAPE_INTERNAL:
    # Use internal Playwright scraper
    result = await internal_scraper.scrape(url)
else:
    # Use provider API
    result = await provider_scraper.scrape(url)
```

## Best Practices

1. **Always check flags before rendering feature UI** - prevents broken links and confusion
2. **Graceful degradation** - provide fallbacks when features are disabled
3. **Document flag changes** - update this file when adding new flags
4. **Test both states** - ensure features work when enabled and don't break when disabled

## Adding New Flags

1. Add the environment variable with `NEXT_PUBLIC_FEATURE_` prefix
2. Update `frontend/lib/flags.ts` with the new flag
3. Document it in this file
4. Add to `.env.example` with default value
