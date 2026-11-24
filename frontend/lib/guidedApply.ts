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

/** Prevent a link for job B from silently applying to saved work for job A. */
export function hasUnresolvedJobSwitch({
  selectedJobPresent, exactSourceMatch, importedThisJob, hasSavedWork,
}: {
  selectedJobPresent: boolean;
  exactSourceMatch: boolean;
  importedThisJob: boolean;
  hasSavedWork: boolean;
}): boolean {
  return selectedJobPresent && hasSavedWork && !exactSourceMatch && !importedThisJob;
}

/** A temporarily unvalidated assessment must not push users backwards during hydration. */
export function needsApplyStageDowngrade(
  stage: ApplyStage,
  progress: ApplyProgress,
  revalidationComplete: boolean,
): boolean {
  if (!revalidationComplete) return false;
  if (stage > 2 && !progress.hasAnalysis) return true;
  return stage === 2 && !progress.hasCriteria;
}

/** Keep the same imported-advert editor mounted after the applicant types. */
export function isImportedAdvertEditor({
  sourceJobId,
  linkedSourceJobId,
  importedThisSession,
  exactSourceMatch,
}: {
  sourceJobId: number | null;
  linkedSourceJobId: number | null;
  importedThisSession: boolean;
  exactSourceMatch: boolean;
}): boolean {
  return sourceJobId !== null
    && (linkedSourceJobId === sourceJobId || importedThisSession || exactSourceMatch);
}

/** An explicit 'Not sure' is a valid answer, but must not be treated as meeting the requirement. */
export function unansweredMandatoryQuestions(
  requirements: string[],
  answers: Record<string, 'yes' | 'no' | 'unsure'>,
): string[] {
  return requirements.filter((requirement) => !Object.prototype.hasOwnProperty.call(answers, requirement));
}
