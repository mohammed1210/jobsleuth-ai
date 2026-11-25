import test from 'node:test';
import assert from 'node:assert/strict';

import { parseVacancyText } from '../lib/vacancyParser';

test('local fallback excludes benefits, recruitment dates, and employer contacts', () => {
  const advert = `Afternoon Receptionist
Essential criteria
- Excellent organisational skills
- Administration experience
- Outstanding telephone communication skills
- Free gym membership to all employees
- Eye Care Voucher Scheme
- Closing Date for applications: Tuesday 1st December 2026
- We reserve the right to make an appointment before the closing date
Benefits
- Heavily subsidised childcare at the nursery
- Bike 2 work scheme
- Interviews: TBC`;
  const result = parseVacancyText(advert);
  assert.deepEqual(result.requirements.map((item) => item.text), [
    'Excellent organisational skills',
    'Administration experience',
    'Outstanding telephone communication skills',
  ]);
});

test('local fallback does not treat an advert with no candidate criteria as a positive match', () => {
  const advert = `Exam Invigilator
Working pattern
Part Time
12.5 hours per week
Benefits
Free gym membership
Closing Date for applications: 5 December 2026`;
  const result = parseVacancyText(advert);
  assert.equal(result.requirements.length, 0);
  assert.ok(result.practicalIssues.some((item) => item.includes('12.5 hours')));
});

test('real experience and support skills are retained when explicitly advertised', () => {
  const advert = `Essential criteria
- Experience supporting vulnerable children
- Ability to organise transport for pupils
- Strong communication skills`;
  assert.equal(parseVacancyText(advert).requirements.length, 3);
});

test('local fallback resumes after Benefits with a new About you heading', () => {
  const advert = `Benefits
- Free gym membership
About you
- Experience supporting vulnerable children
- Ability to arrange transport for pupils`;
  const result = parseVacancyText(advert);
  assert.equal(result.requirements.length, 2);
  assert.deepEqual(result.requirements.map((item) => item.text), [
    'Experience supporting vulnerable children',
    'Ability to arrange transport for pupils',
  ]);
});

test('local fallback retains metadata values under their headings', () => {
  const advert = `Location
London
Working pattern
Monday to Friday
12.5 hours per week
Essential criteria
- Strong communication skills`;
  const result = parseVacancyText(advert);
  assert.deepEqual(result.practicalIssues, ['London', 'Monday to Friday', '12.5 hours per week']);
  assert.equal(result.requirements.length, 1);
});
