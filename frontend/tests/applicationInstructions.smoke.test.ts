import test from 'node:test';
import assert from 'node:assert/strict';

import { detectApplicationInstructions } from '../lib/applicationInstructions';

test('Greenhouse-style optional cover letter stays draftable but is not required', () => {
  const vacancy = `
Customer Success Manager
London

The Company You'll Join
Carta is the connected platform for private capital.

About You
- 5+ years of experience in Customer Success or Account Management.

* indicates a required field
Resume/CV*
Cover Letter
Submit application
`;

  const result = detectApplicationInstructions(vacancy);

  assert.equal(result.roleTitle, 'Customer Success Manager');
  assert.equal(result.organisation, 'Carta');
  assert.equal(result.applicationType, 'cover_letter');
  assert.equal(result.applicationTypeLabel, 'Cover letter (optional)');
  assert.ok(result.applicationParts.some((part) => part.kind === 'cover_letter'));
  assert.ok(result.requiredDocuments.includes('CV'));
  assert.ok(!result.requiredDocuments.includes('Cover Letter'));
});

test('explicitly requested cover letter remains required', () => {
  const vacancy = `
Operations Manager
Example Security Ltd

To apply, please submit your CV and cover letter.
`;

  const result = detectApplicationInstructions(vacancy);

  assert.equal(result.applicationType, 'cover_letter');
  assert.equal(result.applicationTypeLabel, 'Cover letter');
  assert.ok(result.requiredDocuments.includes('CV'));
  assert.ok(result.requiredDocuments.includes('Cover Letter'));
});


test('descriptive role sentence cannot override a valid employer fallback', () => {
  const vacancy = `
Operations Manager
Example Security Ltd

The role is a permanent position supporting regional operations.
`;

  const result = detectApplicationInstructions(vacancy);

  assert.equal(result.roleTitle, 'Operations Manager');
  assert.equal(result.organisation, 'Example Security Ltd');
});


test('generic company heading does not block the real employer fallback', () => {
  const vacancy = `
Operations Manager
The Company
Example Security Ltd

About the role
We support regional operations.
`;

  const result = detectApplicationInstructions(vacancy);

  assert.equal(result.roleTitle, 'Operations Manager');
  assert.equal(result.organisation, 'Example Security Ltd');
});


test('DfE-style employer excerpt without application instructions labels 500 words as a draft default', () => {
  const text = `Job title
Head of School
Employer
Example Primary Academy
Salary: £68,000–£77,000
Applications close: 10 December
About You
• Qualified Teacher Status
• Leadership experience within a primary school setting
`;
  const result = detectApplicationInstructions(text);
  assert.equal(result.wordLimit, null);
  assert.equal(result.wordLimitConfirmed, false);
  assert.equal(result.applicationFormatConfirmed, false);
  assert.deepEqual(result.requiredDocuments, []);
});

test('explicit employer requirements are distinguished from generic statements', () => {
  const result = detectApplicationInstructions(
    'Operations Manager\nPlease submit your CV and a personal statement. Maximum 750 words.'
  );
  assert.equal(result.applicationFormatConfirmed, true);
  assert.equal(result.wordLimitConfirmed, true);
  assert.equal(result.wordLimit, 750);
  assert.ok(result.requiredDocuments.includes('Personal Statement'));
});

test('passing mention of personal statements cannot imply employer has requested one', () => {
  const result = detectApplicationInstructions(
    'We help staff with personal statement coaching during their professional development. No application guidance is provided.'
  );
  assert.equal(result.applicationFormatConfirmed, false);
  assert.ok(!result.requiredDocuments.includes('Personal Statement'));
});

test('optional cover letter field is known optional, not an employer requirement', () => {
  const result = detectApplicationInstructions(
    'Role\n* indicates a required field\nResume/CV*\nCover Letter\nSubmit application'
  );
  assert.equal(result.applicationFormatConfirmed, true);
  assert.ok(!result.requiredDocuments.includes('Cover Letter'));
});

test('explicitly negated document instructions are not required documents', () => {
  const result = detectApplicationInstructions('Do not submit a cover letter. Please send a CV only.');
  assert.ok(!result.requiredDocuments.includes('Cover Letter'));
});


test('starred ATS cover letter and statement fields are required without action verbs', () => {
  const required = detectApplicationInstructions(`Office Administrator
* indicates a required field
Resume/CV*
Cover Letter*
Personal Statement*
Submit application`);
  assert.equal(required.applicationFormatConfirmed, true);
  assert.ok(required.requiredDocuments.includes('Cover Letter'));
  assert.ok(required.requiredDocuments.includes('Personal Statement'));
  assert.ok(required.requiredDocuments.includes('CV'));
});

test('unstarred ATS document field stays optional alongside starred CV', () => {
  const optional = detectApplicationInstructions(`Operations Coordinator
* indicates a required field
Resume/CV*
Personal Statement
Submit application`);
  assert.equal(optional.applicationFormatConfirmed, true);
  assert.ok(!optional.requiredDocuments.includes('Personal Statement'));
});
