import test from 'node:test';
import assert from 'node:assert/strict';

import {
  canQuickSaveImportedEvidence,
  dedupeImportedEvidence,
  isLikelyDuplicate,
} from '../lib/evidenceImportDedupe';

test('duplicate import is removed when the same example is repeated', () => {
  const saved = {
    title: 'Operational incident',
    situation: 'A time-sensitive operational incident required a response.',
    task: 'I needed to coordinate with partner agencies.',
    actions: ['I briefed police and operational colleagues and recorded the decision.'],
    outcome: 'The incident was resolved safely.',
  };
  const repeated = {
    ...saved,
    title: 'Operational response example',
  };

  assert.equal(isLikelyDuplicate(saved, repeated), true);
  const result = dedupeImportedEvidence([repeated], [saved]);
  assert.equal(result.unique.length, 0);
  assert.equal(result.skipped, 1);
});

test('different examples are retained even when both are operational', () => {
  const first = {
    title: 'Freight examination',
    situation: 'A freight examination required specialist equipment.',
    task: 'I assessed relocation options.',
    actions: ['I checked equipment availability and recommended relocation.'],
    outcome: 'The examination continued at another port.',
  };
  const second = {
    title: 'Custody incident',
    situation: 'A detainee became distressed during transport.',
    task: 'I needed to protect welfare and maintain security.',
    actions: ['I communicated calmly and followed the welfare process.'],
    outcome: 'The detainee arrived safely at court.',
  };

  assert.equal(isLikelyDuplicate(first, second), false);
  const result = dedupeImportedEvidence([first, second], []);
  assert.equal(result.unique.length, 2);
  assert.equal(result.skipped, 0);
});

test('quick save requires context or responsibility, actions and an outcome', () => {
  assert.equal(
    canQuickSaveImportedEvidence({
      situation: 'A live operational issue occurred.',
      actions: ['I coordinated the response.'],
      outcome: 'The issue was resolved safely.',
    }),
    true,
  );
  assert.equal(
    canQuickSaveImportedEvidence({
      situation: 'A live operational issue occurred.',
      actions: ['I coordinated the response.'],
      outcome: '',
    }),
    false,
  );
});
