import type { ApplicationType } from '@/lib/applicationBuilderApi';

export type ApplicationPart = {
  id: string;
  kind: 'statement' | 'cover_letter' | 'criteria' | 'behaviour';
  label: string;
  wordLimit: number | null;
  behaviourName?: string;
};

export type ApplicationInstructions = {
  roleTitle: string;
  organisation: string;
  applicationType: ApplicationType;
  applicationTypeLabel: string;
  wordLimit: number | null;
  requiredDocuments: string[];
  applicationParts: ApplicationPart[];
};

const cleanLines = (text: string) => text
  .split(/\r?\n/)
  .map((line) => line.trim())
  .filter(Boolean);

function firstMatch(text: string, patterns: RegExp[]): string | null {
  for (const pattern of patterns) {
    const match = text.match(pattern);
    if (match?.[1]) return match[1].trim();
  }
  return null;
}

function hasNegatedDocumentInstruction(text: string, documentPattern: string): boolean {
  const segments = text
    .split(/(?<=[.!?;])\s+|\r?\n+|[,;]\s*(?=(?:instead|but|however)\b)|\s+(?=(?:instead|but|however)\b)|\s+and\s+(?=(?:(?:do\s+not|don't|must\s+not|should\s+not)\s+)?(?:submit|provide|include|attach|upload|complete)\b)/i)
    .map((segment) => segment.replace(/^(?:instead|but|however)\s*,?\s*/i, '').trim())
    .filter(Boolean);

  let sawNegatedMention = false;
  let sawPositiveAction = false;

  const documentMention = new RegExp(`(?:${documentPattern})\\b`, 'i');
  const requirementNegation = new RegExp(
    `(?:${documentPattern})\\b\\s*(?:(?:is|are)\\s*)?(?:not\\s+required|not\\s+necessary|optional)\\b`,
    'i',
  );

  const knownDocument = '(?:CV|curriculum\\s+vitae|personal\\s+statement|statement\\s+of\\s+suitability|cover(?:ing)?\\s+letter)';
  const documentSeparator = '(?:\\s*,\\s*(?:(?:and|or)\\s+)?|\\s+(?:and|or)\\s+)';
  const documentObject = `(?:(?:an?|the|your)\\s+)?${knownDocument}`;
  const documentObjectList = `(?:either\\s+)?${documentObject}(?:${documentSeparator}${documentObject})*`;
  const actionVerb = '(?:submit|provide|include|attach|upload|complete)';
  const passiveActionVerb = '(?:submitted|provided|included|attached|uploaded|completed)';

  const negatedAction = new RegExp(
    `(?:(?:do\\s+not|don't|must\\s+not|should\\s+not)\\s+${actionVerb}|(?:you\\s+)?(?:do|does)\\s+not\\s+(?:need|have)\\s+to\\s+${actionVerb}|(?:you\\s+)?(?:will\\s+)?not\\s+be\\s+(?:required|expected|needed)\\s+to\\s+${actionVerb}|(?:you\\s+)?(?:are|is)\\s+not\\s+(?:required|expected|needed)\\s+to\\s+${actionVerb})\\s+(${documentObjectList})`,
    'ig',
  );
  const positiveAction = new RegExp(
    `${actionVerb}\\s+(${documentObjectList})`,
    'ig',
  );
  const passivePositiveAction = new RegExp(
    `(${documentObjectList})\\s+(?:(?:must|should)\\s+be|(?:is|are)\\s+required\\s+to\\s+be)\\s+${passiveActionVerb}\\b`,
    'ig',
  );
  const listRequirementNegation = new RegExp(
    `(${documentObjectList})\\s+(?:is|are)\\s+(?:optional|not\\s+required|not\\s+necessary)\\b`,
    'ig',
  );
  const leadingNoRequirement = new RegExp(
    `\\bno\\s+(${documentObjectList})\\s+(?:is|are)\\s+(?:required|necessary)\\b`,
    'ig',
  );

  for (const segment of segments) {
    if (!documentMention.test(segment)) continue;

    if (requirementNegation.test(segment)) {
      sawNegatedMention = true;
    }

    listRequirementNegation.lastIndex = 0;
    for (const match of segment.matchAll(listRequirementNegation)) {
      if (documentMention.test(match[1] ?? '')) {
        sawNegatedMention = true;
      }
    }

    leadingNoRequirement.lastIndex = 0;
    for (const match of segment.matchAll(leadingNoRequirement)) {
      if (documentMention.test(match[1] ?? '')) {
        sawNegatedMention = true;
      }
    }

    // Remove fully-negated action phrases before looking for affirmative
    // instructions. Otherwise a phrase such as "not required to submit a CV"
    // would also be rediscovered as the bare positive substring "submit a CV".
    let positiveCandidate = segment;
    negatedAction.lastIndex = 0;
    positiveCandidate = positiveCandidate.replace(negatedAction, (match, objectList: string) => {
      if (documentMention.test(objectList ?? '')) {
        sawNegatedMention = true;
      }
      return ' '.repeat(match.length);
    });

    positiveAction.lastIndex = 0;
    for (const match of positiveCandidate.matchAll(positiveAction)) {
      const objectList = match[1] ?? '';
      if (documentMention.test(objectList)) {
        sawPositiveAction = true;
      }
    }

    passivePositiveAction.lastIndex = 0;
    for (const match of positiveCandidate.matchAll(passivePositiveAction)) {
      const objectList = match[1] ?? '';
      if (documentMention.test(objectList)) {
        sawPositiveAction = true;
      }
    }
  }

  // Neutral references must not override an explicit prohibition. If the
  // advert also contains a genuine positive action for the same document,
  // keep it as required.
  return sawNegatedMention && !sawPositiveAction;
}

function hasOptionalAtsDocumentField(text: string, documentPattern: string): boolean {
  if (!/indicates a required field/i.test(text)) return false;
  const lines = cleanLines(text);
  const optionalField = new RegExp(`^(?:${documentPattern})\\s*$`, 'i');
  const requiredField = new RegExp(`^(?:${documentPattern})\\s*\\*\\s*$`, 'i');
  return lines.some((line) => optionalField.test(line)) && !lines.some((line) => requiredField.test(line));
}

export function detectApplicationInstructions(vacancyText: string): ApplicationInstructions {
  const text = vacancyText.trim();
  const lines = cleanLines(text);

  const explicitTitle = firstMatch(text, [
    /(?:^|\n)Job title\s*\n\s*([^\n]+)/i,
    /(?:^|\n)Role title\s*\n\s*([^\n]+)/i,
    /\bis seeking (?:an?\s+)?(?:experienced\s+)?([^,.\n]{3,100}?)\s+to\s+join\b/i,
  ]);

  const genericLeadLine = /^(?:skip to content|job details|here['’]s how the job details align with your profile\.?|pay|job type|shift and schedule|location|estimated commute|job address|benefits|pulled from the full job description|full job description|about the role|home office logo|details|reference number|salary|contents|about the job)$/i;
  const roleTitle = explicitTitle || lines.find((line) => !genericLeadLine.test(line)) || '';

  const explicitOrganisation = firstMatch(text, [
    /(?:^|\n)(?:Organisation|Employer|Department)\s*\n\s*([^\n]+)/i,
    /(?:^|\n)([A-Z][^,\n]{2,100}),[^\n]{0,160}\bis seeking\b/i,
    /(?:^|\n)At\s+([A-Z][A-Za-z0-9&'’.,\- ]{1,80}),\s+(?:our|we)\b/i,
    /(?:^|\n)([A-Z][A-Za-z0-9&'’.,\- ]{1,80})\s+is\s+(?:the|a|an)\b/i,
  ]);
  const organisationCandidate = explicitOrganisation
    || lines.find((line, index) => index > 0 && /home office|nhs|council|university|department|agency|service|company|limited|ltd\.?$/i.test(line))
    || '';
  const organisation = /^(?:this|role|job|position|location|team|company)$/i.test(organisationCandidate.trim())
    ? ''
    : organisationCandidate.trim();

  const personalStatementMentioned = /personal statement/i.test(text);
  const personalStatementNegated = hasNegatedDocumentInstruction(text, 'personal\\s+statement');
  const personalStatementOptionalField = hasOptionalAtsDocumentField(text, 'personal\\s+statement');
  const personalStatement = personalStatementMentioned && !personalStatementNegated;
  const personalStatementRequired = personalStatement && !personalStatementOptionalField;
  const criteriaResponse = /essential criteria response|criteria response/i.test(text);
  const coverLetterMentioned = /cover(?:ing)? letter/i.test(text);
  const coverLetterNegated = hasNegatedDocumentInstruction(text, 'cover(?:ing)?\\s+letter');
  const coverLetterOptionalField = hasOptionalAtsDocumentField(text, 'cover(?:ing)?\\s+letter');
  const coverLetter = coverLetterMentioned && !coverLetterNegated;
  const coverLetterRequired = coverLetter && !coverLetterOptionalField;
  const applicationType: ApplicationType = criteriaResponse
    ? 'criteria_response'
    : personalStatement
      ? 'statement_of_suitability'
      : coverLetter
        ? 'cover_letter'
        : 'statement_of_suitability';
  const applicationTypeLabel = personalStatement
    ? personalStatementOptionalField ? 'Personal statement (optional)' : 'Personal statement'
    : criteriaResponse
      ? 'Essential criteria response'
      : coverLetter
        ? coverLetterOptionalField ? 'Cover letter (optional)' : 'Cover letter'
        : 'Statement of suitability';

  const wordLimitText = firstMatch(text, [
    /personal statement[^\n]{0,120}?maximum\s+(\d{2,4})\s+words/i,
    /personal statement[^\n]{0,120}?up to\s+(\d{2,4})\s+words/i,
    /statement of suitability[^\n]{0,120}?maximum\s+(\d{2,4})\s+words/i,
    /cover(?:ing)? letter[^\n]{0,120}?maximum\s+(\d{2,4})\s+words/i,
    /cover(?:ing)? letter[^\n]{0,120}?up to\s+(\d{2,4})\s+words/i,
    /maximum\s+(\d{2,4})\s+words/i,
    /word limit\s*[:\-]?\s*(\d{2,4})/i,
  ]);
  const parsedLimit = wordLimitText ? Number(wordLimitText) : null;
  const wordLimit = parsedLimit && parsedLimit >= 100 && parsedLimit <= 5000 ? parsedLimit : null;

  const requiredDocuments: string[] = [];
  const applicationParts: ApplicationPart[] = [];

  applicationParts.push({
    id: applicationType === 'criteria_response' ? 'criteria-response' : applicationType === 'cover_letter' ? 'cover-letter' : 'main-statement',
    kind: applicationType === 'criteria_response' ? 'criteria' : applicationType === 'cover_letter' ? 'cover_letter' : 'statement',
    label: applicationTypeLabel,
    wordLimit,
  });

  // Some adverts request more than one drafted document. Keep each as its own
  // selectable component instead of only listing the second document as metadata.
  if (personalStatement && applicationType !== 'statement_of_suitability') {
    applicationParts.push({
      id: 'main-statement',
      kind: 'statement',
      label: 'Personal statement',
      wordLimit,
    });
  }
  if (coverLetter && applicationType !== 'cover_letter') {
    applicationParts.push({
      id: 'cover-letter',
      kind: 'cover_letter',
      label: 'Cover letter',
      wordLimit: null,
    });
  }
  const cvMentioned = /\b(?:a\s+)?CV\b/i.test(text);
  const cvNegated = hasNegatedDocumentInstruction(text, '(?:a\\s+)?CV');
  if (cvMentioned && !cvNegated && /application process|asked to complete|submit|sift|scored/i.test(text)) {
    requiredDocuments.push('CV');
  }
  if (personalStatementRequired) requiredDocuments.push('Personal Statement');

  if (coverLetterRequired) requiredDocuments.push('Cover Letter');

  // Civil Service vacancies can require one or more separately-scored behaviour
  // examples in addition to the CV/personal statement. Preserve the behaviour
  // name and its own word budget so the user does not mistake it for part of the
  // main statement allowance.
  const behaviourPattern = /Behaviour(?:s)?\s*:\s*([^\n(]+?)\s*\(\s*maximum\s+(\d{2,4})\s+words\s*\)/gi;
  for (const match of text.matchAll(behaviourPattern)) {
    const behaviourName = match[1]?.trim();
    const behaviourLimit = Number(match[2]);
    if (!behaviourName || !Number.isFinite(behaviourLimit)) continue;
    requiredDocuments.push(`Behaviour: ${behaviourName} (${behaviourLimit} words)`);
    applicationParts.push({
      id: `behaviour-${behaviourName.toLowerCase().replace(/[^a-z0-9]+/g, '-')}`,
      kind: 'behaviour',
      label: `Behaviour: ${behaviourName}`,
      wordLimit: behaviourLimit,
      behaviourName,
    });
  }

  return {
    roleTitle,
    organisation,
    applicationType,
    applicationTypeLabel,
    wordLimit,
    requiredDocuments: [...new Set(requiredDocuments)],
    applicationParts: applicationParts.filter((part, index, parts) => parts.findIndex((candidate) => candidate.id === part.id) === index),
  };
}
