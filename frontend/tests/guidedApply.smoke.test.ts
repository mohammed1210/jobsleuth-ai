import test from 'node:test';
import assert from 'node:assert/strict';

import { APPLY_STAGES, canOpenApplyStage, hasUnresolvedJobSwitch, isImportedAdvertEditor, needsApplyStageDowngrade, resumeApplyStage, unansweredMandatoryQuestions } from '../lib/guidedApply';

test('the customer sees four short task labels without internal terminology', () => {
  assert.deepEqual(APPLY_STAGES.map((stage) => stage.label), [
    'Your job', 'Key requirements', 'Your match', 'Your application',
  ]);
  assert.equal(new Set(APPLY_STAGES.map((stage) => stage.id)).size, 4);
});

test('no jumping into results or drafting before a successful analysis', () => {
  assert.equal(canOpenApplyStage(1, { hasCriteria: false, hasAnalysis: false }), true);
  for (const step of [2, 3, 4] as const) {
    assert.equal(canOpenApplyStage(step, { hasCriteria: false, hasAnalysis: false }), false);
  }
  assert.equal(canOpenApplyStage(2, { hasCriteria: true, hasAnalysis: false }), true);
  assert.equal(canOpenApplyStage(3, { hasCriteria: true, hasAnalysis: false }), false);
  assert.equal(canOpenApplyStage(4, { hasCriteria: true, hasAnalysis: false }), false);
  assert.equal(canOpenApplyStage(3, { hasCriteria: true, hasAnalysis: true }), true);
  assert.equal(canOpenApplyStage(4, { hasCriteria: true, hasAnalysis: true }), true);
});

test('resuming never fabricates a match or skips an unanswered eligibility step', () => {
  assert.equal(resumeApplyStage({ hasCriteria: false, hasAnalysis: false }), 1);
  assert.equal(resumeApplyStage({ hasCriteria: true, hasAnalysis: false }), 2);
  assert.equal(resumeApplyStage({ hasCriteria: true, hasAnalysis: true }), 3);
});

test('a newly selected vacancy never silently inherits the previous saved application', () => {
  const existingDraftForA = {
    selectedJobPresent: true,
    exactSourceMatch: false,
    importedThisJob: false,
    hasSavedWork: true,
  };
  assert.equal(hasUnresolvedJobSwitch(existingDraftForA), true);
  assert.equal(hasUnresolvedJobSwitch({ ...existingDraftForA, exactSourceMatch: true }), false);
  assert.equal(hasUnresolvedJobSwitch({ ...existingDraftForA, importedThisJob: true }), false);
  assert.equal(hasUnresolvedJobSwitch({ ...existingDraftForA, hasSavedWork: false }), false);
  assert.equal(hasUnresolvedJobSwitch({ ...existingDraftForA, selectedJobPresent: false }), false);
});

test('temporarily unvalidated assessment does not downgrade a step during auth refresh', () => {
  const temporarilyPending = { hasCriteria: true, hasAnalysis: false };
  assert.equal(needsApplyStageDowngrade(4, temporarilyPending, false), false);
  assert.equal(needsApplyStageDowngrade(3, temporarilyPending, false), false);
  assert.equal(needsApplyStageDowngrade(4, temporarilyPending, true), true);
  assert.equal(needsApplyStageDowngrade(3, { hasCriteria: true, hasAnalysis: true }, true), false);
  assert.equal(needsApplyStageDowngrade(2, { hasCriteria: false, hasAnalysis: false }, true), true);
});

test('editing the imported advert keeps the same editor mounted', () => {
  assert.equal(isImportedAdvertEditor({ sourceJobId: 99, linkedSourceJobId: 99, importedThisSession: false, exactSourceMatch: false }), true);
  assert.equal(isImportedAdvertEditor({ sourceJobId: 99, linkedSourceJobId: null, importedThisSession: true, exactSourceMatch: false }), true);
  assert.equal(isImportedAdvertEditor({ sourceJobId: 99, linkedSourceJobId: null, importedThisSession: false, exactSourceMatch: true }), true);
  assert.equal(isImportedAdvertEditor({ sourceJobId: 100, linkedSourceJobId: 99, importedThisSession: false, exactSourceMatch: false }), false);
});

test('mandatory qualification is an explicit answer; not sure is not an assumed yes', () => {
  const q = ['Qualified Teacher Status.', 'Required safeguarding certificate'];
  assert.deepEqual(unansweredMandatoryQuestions(q, {}), q);
  assert.deepEqual(unansweredMandatoryQuestions(q, { [q[0]]: 'no' }), [q[1]]);
  assert.deepEqual(unansweredMandatoryQuestions(q, { [q[0]]: 'unsure', [q[1]]: 'yes' }), []);
  assert.deepEqual(unansweredMandatoryQuestions([], {}), []);
});
