/**
 * Feature flags for JobSleuth AI
 * All flags are SSR-safe and default to false when unset
 */

// Helper to safely parse boolean env vars
function parseBooleanFlag(value: string | undefined): boolean {
  if (!value) return false;
  return value.toLowerCase() === 'true' || value === '1';
}

export const featureFlags = {
  // AI-powered job fit scoring
  aifit: parseBooleanFlag(process.env.NEXT_PUBLIC_FEATURE_AI_FIT),

  // Resume suggestions and cover letter generation
  resumeTools: parseBooleanFlag(process.env.NEXT_PUBLIC_FEATURE_RESUME_TOOLS),

  // Email digest subscriptions
  digests: parseBooleanFlag(process.env.NEXT_PUBLIC_FEATURE_DIGESTS),

  // Internal Playwright scraping (backend feature exposed for UI consistency)
  scrapeInternal: parseBooleanFlag(process.env.NEXT_PUBLIC_FEATURE_SCRAPE_INTERNAL),
} as const;

export type FeatureFlags = typeof featureFlags;
