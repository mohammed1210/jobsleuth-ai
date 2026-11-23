import test from 'node:test';
import assert from 'node:assert/strict';
import { advertForApplication, applicationPath, safeLoginReturnPath, signInPathForJob } from '../lib/jobApplicationHandoff';
import { detectApplicationInstructions } from '../lib/applicationInstructions';

const job = {
  id: 100,
  title: 'Cleaner',
  company: 'Fixture School',
  location: 'Rugby, West Midlands',
  role_type: 'Part Time',
  salary: '£12,500 - £14,000 per year',
  expires_at: '2026-11-27T12:00:00+00:00',
  url: 'https://teaching-vacancies.service.gov.uk/jobs/fixture-cleaner',
  description: 'Full publisher text with responsibilities, and more than a short preview.',
};

test('JobSleuth application route is local and preserves the selected job', () => {
  assert.equal(applicationPath(100), '/apply/vacancy?job=100');
  assert.equal(
    signInPathForJob(100),
    '/login?next=%2Fapply%2Fvacancy%3Fjob%3D100',
  );
  assert.equal(safeLoginReturnPath('/apply/vacancy?job=100'), '/apply/vacancy?job=100');
  for (const input of ['https://evil.test', '//evil.test', '/jobs/100', '/apply/vacancy?job=100&next=//bad', '/apply/vacancy?job=notanid']) {
    assert.equal(safeLoginReturnPath(input), '/apply/vacancy');
  }
  assert.throws(() => applicationPath(0), /Invalid job ID/);
});

test('source job details prefill Apply with correct role, pay, source and complete description', () => {
  const advert = advertForApplication(job);
  assert.match(advert, /Job title\s+Cleaner/);
  assert.match(advert, /Employer\s+Fixture School/);
  assert.match(advert, /£12,500 - £14,000/);
  assert.match(advert, /https:\/\/teaching-vacancies.service.gov.uk\/jobs\/fixture-cleaner/);
  assert.match(advert, /Full publisher text with responsibilities/);
  assert.doesNotMatch(advert, /85%|AI match/i);
});

test('handoff metadata is understood by the same application-builder parser', () => {
  const parsed = detectApplicationInstructions(advertForApplication(job));
  assert.equal(parsed.roleTitle, 'Cleaner');
  assert.equal(parsed.organisation, 'Fixture School');
});
