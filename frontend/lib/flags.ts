/**
 * Feature Flags - SSR-Safe Utilities
 * 
 * Provides type-safe access to feature flags with support for both
 * server-side rendering and client-side rendering.
 * 
 * All flags default to `false` when not set.
 */

type FeatureFlag = 
  | 'AI_FIT'
  | 'RESUME_TOOLS'
  | 'DIGESTS'
  | 'SCRAPE_INTERNAL';

/**
 * Get the value of a feature flag
 * @param flag - The feature flag name (without NEXT_PUBLIC_FEATURE_ prefix)
 * @returns boolean - true if flag is explicitly set to 'true', false otherwise
 */
export function getFeatureFlag(flag: FeatureFlag): boolean {
  if (typeof window === 'undefined') {
    // Server-side: access via process.env
    return process.env[`NEXT_PUBLIC_FEATURE_${flag}`] === 'true';
  } else {
    // Client-side: access via process.env (injected at build time)
    return process.env[`NEXT_PUBLIC_FEATURE_${flag}`] === 'true';
  }
}

/**
 * Get all feature flags as an object
 * Useful for debugging or passing to analytics
 */
export function getAllFeatureFlags(): Record<FeatureFlag, boolean> {
  return {
    AI_FIT: getFeatureFlag('AI_FIT'),
    RESUME_TOOLS: getFeatureFlag('RESUME_TOOLS'),
    DIGESTS: getFeatureFlag('DIGESTS'),
    SCRAPE_INTERNAL: getFeatureFlag('SCRAPE_INTERNAL'),
  };
}

/**
 * React hook for using feature flags
 * Provides reactive updates if flags change (though they shouldn't at runtime)
 */
export function useFeatureFlag(flag: FeatureFlag): boolean {
  return getFeatureFlag(flag);
}

/**
 * Check if any premium features are enabled
 * Useful for showing upgrade prompts
 */
export function hasAnyPremiumFeatures(): boolean {
  return getFeatureFlag('AI_FIT') || 
         getFeatureFlag('RESUME_TOOLS') || 
         getFeatureFlag('DIGESTS');
}

/**
 * Type guard to check if a string is a valid feature flag
 */
export function isValidFeatureFlag(flag: string): flag is FeatureFlag {
  return ['AI_FIT', 'RESUME_TOOLS', 'DIGESTS', 'SCRAPE_INTERNAL'].includes(flag);
}

// Export feature flag constants for easier imports
export const FEATURES = {
  AI_FIT: 'AI_FIT',
  RESUME_TOOLS: 'RESUME_TOOLS',
  DIGESTS: 'DIGESTS',
  SCRAPE_INTERNAL: 'SCRAPE_INTERNAL',
} as const;
