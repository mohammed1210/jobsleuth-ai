import test from 'node:test';
import assert from 'node:assert/strict';

import { APPLY_STAGES, canOpenApplyStage, resumeApplyStage } from '../lib/guidedApply';

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
