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
