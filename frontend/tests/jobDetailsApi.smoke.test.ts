import test from 'node:test';
import assert from 'node:assert/strict';
import { fetchJobDetail, fetchJobs } from '../lib/api';

const sourceJob = {
  id: 94,
  title: 'Synthetic Operations Analyst',
  company: 'Fixture Public Agency',
  location: 'London',
  description: '<p>This is a synthetic fixture only.</p>',
  url: 'https://example.org/jobs/94',
  ai_score: null,
  date_posted: null,
};

async function withFetchMock(response: Response, run: () => Promise<void>) {
  const previous = globalThis.fetch;
  const requests: string[] = [];
  globalThis.fetch = async (input) => {
    requests.push(String(input));
    return response;
  };
  try {
    await run();
  } finally {
    globalThis.fetch = previous;
  }
  return requests;
}

test('job detail fetch returns the selected database record, never a sample', async () => {
  const calls = await withFetchMock(
    new Response(JSON.stringify(sourceJob), { status: 200 }),
    async () => {
      const job = await fetchJobDetail(94);
      assert.equal(job?.id, 94);
      assert.equal(job?.title, sourceJob.title);
      assert.equal(job?.company, sourceJob.company);
      assert.equal(job?.description, sourceJob.description);
      assert.equal(job?.url, sourceJob.url);
      assert.equal(job?.ai_score, null);
    },
  );
  assert.equal(calls.length, 1);
  assert.match(calls[0], /\/jobs\/94$/);
});

test('missing job has no fake details and returns null', async () => {
  const calls = await withFetchMock(new Response('', { status: 404 }), async () => {
    assert.equal(await fetchJobDetail(9999), null);
  });
  assert.equal(calls.length, 1);
});

test('API outage rejects rather than showing fake job details', async () => {
  await withFetchMock(new Response('server down', { status: 503 }), async () => {
    await assert.rejects(fetchJobDetail(1), /temporarily unavailable/i);
  });
});

test('invalid numeric identifier is rejected before any network call', async () => {
  const original = globalThis.fetch;
  globalThis.fetch = async () => { throw new Error('must not be called'); };
  try {
    assert.equal(await fetchJobDetail(0), null);
    assert.equal(await fetchJobDetail(-1), null);
    assert.equal(await fetchJobDetail(Number.NaN), null);
  } finally {
    globalThis.fetch = original;
  }
});

test('genuinely empty database returns empty list and zero total', async () => {
  await withFetchMock(
    new Response(JSON.stringify({ jobs: [], total: 0, page: 1, per_page: 10 }), { status: 200 }),
    async () => {
      const response = await fetchJobs({ page: '1', per_page: '10' });
      assert.deepEqual(response.jobs, []);
      assert.equal(response.total, 0);
    },
  );
});

test('job-list error does not invent local fallback vacancies', async () => {
  await withFetchMock(new Response('storage failure', { status: 503 }), async () => {
    await assert.rejects(fetchJobs({ page: '1' }), /Failed to fetch jobs/);
  });
});
