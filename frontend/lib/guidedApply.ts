/** The guide changes presentation, never the underlying vacancy or evidence records. */
export type ApplyStage = 1 | 2 | 3 | 4;

export const APPLY_STAGES: ReadonlyArray<{ id: ApplyStage; label: string; hint: string }> = [
  { id: 1, label: 'Your job', hint: 'Load the advert' },
  { id: 2, label: 'Key requirements', hint: 'Confirm the essentials' },
  { id: 3, label: 'Your match', hint: 'Understand the evidence' },
  { id: 4, label: 'Your application', hint: 'Create and review' },
];

export type ApplyProgress = {
  hasCriteria: boolean;
  hasAnalysis: boolean;
};

export function canOpenApplyStage(stage: ApplyStage, progress: ApplyProgress): boolean {
  if (stage === 1) return true;
  if (stage === 2) return progress.hasCriteria;
  return progress.hasAnalysis;
}

/** A resumed application should return to the last independently verified stage. */
export function resumeApplyStage(progress: ApplyProgress): ApplyStage {
  if (progress.hasAnalysis) return 3;
  return progress.hasCriteria ? 2 : 1;
}
