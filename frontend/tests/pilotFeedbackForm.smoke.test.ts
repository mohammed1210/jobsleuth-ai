import test from 'node:test';
import assert from 'node:assert/strict';

import {
  binaryPilotAnswer,
  EMPTY_PILOT_FEEDBACK,
  isPilotFeedbackComplete,
  type PilotFeedbackDraft,
} from '../lib/pilotFeedbackForm';

test('pilot feedback starts unanswered instead of preselecting positive signals', () => {
  assert.equal(EMPTY_PILOT_FEEDBACK.usefulness, null);
  assert.equal(EMPTY_PILOT_FEEDBACK.wouldSubmit, '');
  assert.equal(EMPTY_PILOT_FEEDBACK.recommendationTrust, '');
  assert.equal(EMPTY_PILOT_FEEDBACK.materialTimeSaving, '');
  assert.equal(EMPTY_PILOT_FEEDBACK.wouldUseAgain, '');
  assert.equal(EMPTY_PILOT_FEEDBACK.paymentSignal, '');
  assert.equal(isPilotFeedbackComplete({ ...EMPTY_PILOT_FEEDBACK }), false);
});

test('pilot feedback only becomes complete after every explicit answer', () => {
  const completed: PilotFeedbackDraft = {
    usefulness: 8,
    wouldSubmit: 'yes',
    recommendationTrust: 'no',
    materialTimeSaving: 'yes',
    wouldUseAgain: 'yes',
    paymentSignal: 'maybe',
  };

  assert.equal(isPilotFeedbackComplete(completed), true);
  assert.equal(isPilotFeedbackComplete({ ...completed, paymentSignal: '' }), false);
  assert.equal(isPilotFeedbackComplete({ ...completed, usefulness: null }), false);
});

test('binary pilot answers convert only explicit yes and no choices', () => {
  assert.equal(binaryPilotAnswer('yes'), true);
  assert.equal(binaryPilotAnswer('no'), false);
  assert.throws(() => binaryPilotAnswer(''), /required/);
});
