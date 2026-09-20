import type { ApplicationType } from '@/lib/applicationBuilderApi';

export type ApplicationInstructions = {
  roleTitle: string;
  organisation: string;
  applicationType: ApplicationType;
  applicationTypeLabel: string;
  wordLimit: number | null;
  requiredDocuments: string[];
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
  const documentObjectList = `(?:(?:an?|the|your)\\s+)?${knownDocument}(?:${documentSeparator}(?:(?:an?|the|your)\\s+)?${knownDocument})*`;
  const actionVerb = '(?:submit|provide|include|attach|upload|complete)';

  const negatedAction = new RegExp(
    `(?:(?:do\\s+not|don't|must\\s+not|should\\s+not)\\s+${actionVerb}|(?:you\\s+)?(?:will\\s+)?not\\s+be\\s+(?:required|expected|needed)\\s+to\\s+${actionVerb}|(?:you\\s+)?(?:are|is)\\s+not\\s+(?:required|expected|needed)\\s+to\\s+${actionVerb})\\s+(${documentObjectList})`,
    'ig',
  );
  const positiveAction = new RegExp(
    `${actionVerb}\\s+(${documentObjectList})`,
    'ig',
  );

  for (const segment of segments) {
    if (!documentMention.test(segment)) continue;

    if (requirementNegation.test(segment)) {
      sawNegatedMention = true;
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
  }

  // Neutral references must not override an explicit prohibition. If the
  // advert also contains a genuine positive action for the same document,
  // keep it as required.
  return sawNegatedMention && !sawPositiveAction;
}

export function detectApplicationInstructions(vacancyText: string): ApplicationInstructions {
  const text = vacancyText.trim();
  const lines = cleanLines(text);

  const explicitTitle = firstMatch(text, [
    /(?:^|\n)Job title\s*\n\s*([^\n]+)/i,
    /(?:^|\n)Role title\s*\n\s*([^\n]+)/i,
  ]);

  const roleTitle = explicitTitle || lines.find((line) =>
    !/^(skip to content|home office logo|details|reference number|salary|contents|location|about the job)$/i.test(line)
  ) || '';

  const explicitOrganisation = firstMatch(text, [
    /(?:^|\n)(?:Organisation|Employer|Department)\s*\n\s*([^\n]+)/i,
  ]);
  const organisation = explicitOrganisation
    || lines.find((line, index) => index > 0 && /home office|nhs|council|university|department|agency|service|company|limited|ltd\.?$/i.test(line))
    || '';

  const personalStatementMentioned = /personal statement/i.test(text);
  const personalStatementNegated = hasNegatedDocumentInstruction(text, 'personal\\s+statement');
  const personalStatement = personalStatementMentioned && !personalStatementNegated;
  const criteriaResponse = /essential criteria response|criteria response/i.test(text);
  const applicationType: ApplicationType = criteriaResponse ? 'criteria_response' : 'statement_of_suitability';
  const applicationTypeLabel = personalStatement
    ? 'Personal statement'
    : criteriaResponse
      ? 'Essential criteria response'
      : 'Statement of suitability';

  const wordLimitText = firstMatch(text, [
    /personal statement[^\n]{0,120}?maximum\s+(\d{2,4})\s+words/i,
    /personal statement[^\n]{0,120}?up to\s+(\d{2,4})\s+words/i,
    /statement of suitability[^\n]{0,120}?maximum\s+(\d{2,4})\s+words/i,
    /maximum\s+(\d{2,4})\s+words/i,
    /word limit\s*[:\-]?\s*(\d{2,4})/i,
  ]);
  const parsedLimit = wordLimitText ? Number(wordLimitText) : null;
  const wordLimit = parsedLimit && parsedLimit >= 100 && parsedLimit <= 5000 ? parsedLimit : null;

  const requiredDocuments: string[] = [];
  const cvMentioned = /\b(?:a\s+)?CV\b/i.test(text);
  const cvNegated = hasNegatedDocumentInstruction(text, '(?:a\\s+)?CV');
  if (cvMentioned && !cvNegated && /application process|asked to complete|submit|sift|scored/i.test(text)) {
    requiredDocuments.push('CV');
  }
  if (personalStatement) requiredDocuments.push('Personal Statement');

  const coverLetterMentioned = /cover(?:ing)? letter/i.test(text);
  const coverLetterNegated = hasNegatedDocumentInstruction(text, 'cover(?:ing)?\\s+letter');
  if (coverLetterMentioned && !coverLetterNegated) requiredDocuments.push('Cover Letter');

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
  }

  return {
    roleTitle,
    organisation,
    applicationType,
    applicationTypeLabel,
    wordLimit,
    requiredDocuments: [...new Set(requiredDocuments)],
  };
}
