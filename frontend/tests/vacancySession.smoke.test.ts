import test from 'node:test';
import assert from 'node:assert/strict';
import { preserveVacancySession } from '../lib/vacancySession';

test('same-user auth refresh keeps the current vacancy and draft request mounted', () => {
  for (const event of ['SIGNED_IN', 'TOKEN_REFRESHED', 'INITIAL_SESSION']) {
    assert.equal(preserveVacancySession(event, 'owner-a', 'owner-a'), true);
  }
});

test('sign-out and account changes never preserve the previous owner state', () => {
  for (const event of ['SIGNED_IN', 'TOKEN_REFRESHED', 'INITIAL_SESSION', 'SIGNED_OUT', 'USER_UPDATED']) {
    assert.equal(preserveVacancySession(event, 'owner-a', 'owner-b'), false);
    assert.equal(preserveVacancySession(event, 'owner-a', null), false);
    assert.equal(preserveVacancySession(event, null, 'owner-b'), false);
  }
  assert.equal(preserveVacancySession('SIGNED_OUT', 'owner-a', 'owner-a'), false);
  assert.equal(preserveVacancySession('USER_UPDATED', 'owner-a', 'owner-a'), false);
});
