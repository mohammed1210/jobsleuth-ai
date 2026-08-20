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

  const personalStatement = /personal statement/i.test(text);
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
  if (/\b(?:a\s+)?CV\b/i.test(text) && /application process|asked to complete|submit|sift|scored/i.test(text)) {
    requiredDocuments.push('CV');
  }
  if (personalStatement) requiredDocuments.push('Personal Statement');
  if (/cover(?:ing)? letter/i.test(text)) requiredDocuments.push('Cover Letter');

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
