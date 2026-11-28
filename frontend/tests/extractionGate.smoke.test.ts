import test from 'node:test';
import assert from 'node:assert/strict';
import { createExtractionGate } from '../lib/extractionGate';

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason: Error) => void;
  const promise = new Promise<T>((done, fail) => { resolve = done; reject = fail; });
  return { promise, resolve, reject };
}

test('replace draft while extracting ignores old criteria and preserves new extraction loading', async () => {
  const gate = createExtractionGate();
  const original = deferred<string[]>();
  const replacement = deferred<string[]>();
  let criteria: string[] = [];
  let loading = false;
  const extract = async (task: Promise<string[]>) => {
    const token = gate.begin();
    loading = true;
    try {
      const found = await task;
      if (gate.isCurrent(token)) criteria = found;
    } catch {
      if (gate.isCurrent(token)) criteria = ['fallback'];
    } finally {
      if (gate.isCurrent(token)) loading = false;
    }
  };

  const oldJob = extract(original.promise);
  gate.invalidate(); // 'Replace draft with this vacancy'
  criteria = [];
  const newJob = extract(replacement.promise);
  original.resolve(['old vacancy criterion']);
  await oldJob;
  assert.deepEqual(criteria, []);
  assert.equal(loading, true, 'old finally must not stop new extraction');
  replacement.resolve(['new vacancy criterion']);
  await newJob;
  assert.deepEqual(criteria, ['new vacancy criterion']);
  assert.equal(loading, false);
});

test('clearing a draft or switching users rejects stale success and error fallback', async () => {
  const gate = createExtractionGate();
  const oldSuccess = gate.begin();
  gate.invalidate(); // user clears draft
  assert.equal(gate.isCurrent(oldSuccess), false);
  const oldFailure = gate.begin();
  gate.invalidate(); // auth account changes
  assert.equal(gate.isCurrent(oldFailure), false);
  const current = gate.begin();
  assert.equal(gate.isCurrent(current), true);
  assert.equal(gate.isCurrent(oldSuccess), false);
});
