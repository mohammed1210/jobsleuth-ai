import type { Requirement } from '@/lib/applyApi';

export type ParsedVacancy = {
  provider: 'local-parser';
  requirements: Requirement[];
  practicalIssues: string[];
};

const cleanLine = (value: string) => value.replace(/^\s*(?:[-*•]|\d+[.)](?!\d))\s*/, '').trim();

const employerOnlyLine = (text: string): boolean => [
  /^(?:closing date(?: for applications)?|application deadline|applications? close|interviews?\s*[:–—-]|we reserve the right)\b/i,
  /^(?:free gym membership|heavily subsidised childcare|employee assistance programme|eye care voucher scheme|bike\s*(?:2|to)\s*work scheme|cycle to work scheme)\b/i,
  /^(?:transport links? (?:are|is) excellent|if you would like to discuss the role|please contact\b|we offer support and training)\b/i,
].some((pattern) => pattern.test(text));

const ignoredSection = /^(?:benefits?|employee benefits|what we offer|what we can offer|our benefits|perks(?: and benefits)?|why join us|how to apply|application process|closing date|interviews?|contact(?: us)?)\s*:?\s*$/i;

export function parseVacancyText(text: string): ParsedVacancy {
  const requirements: Requirement[] = [];
  const practicalIssues: string[] = [];
  // Unlabelled lines are not necessarily requirements.
  let section: 'essential' | 'desirable' | 'practical' | 'ignore' | null = null;
  let practicalHeading: 'location' | 'schedule' = 'schedule';

  for (const raw of text.replace(/\.\s+(?=(?:Experience|Ability|Knowledge|Strong\s+|Previous experience)\b)/gi, '.\n').split(/\r?\n/)) {
    const line = cleanLine(raw);
    if (!line) continue;
    const lowered = line.toLowerCase().replace(/:$/, '');

    if (ignoredSection.test(line)) {
      section = 'ignore';
      continue;
    }
    if (employerOnlyLine(line)) continue;

    if (line.length <= 90 && (lowered.includes('desirable') || lowered.includes('nice to have'))) {
      section = 'desirable';
      continue;
    }
    if (line.length <= 90 && [
      'essential criteria', 'essential requirements', 'person specification',
      'what you will need', 'what you need to do the job', 'about you',
      'requirements', 'requirements of the role', 'role requirements',
      'what we are looking for', "what we're looking for", "what you'll bring",
      'your skills and experience',
    ].some((cue) => lowered === cue || lowered === cue + ':')) {
      section = 'essential';
      continue;
    }
    if (line.length <= 90 && /^(?:working pattern|working arrangements|hours|location|travel requirements)(?:\s*:\s*.*)?$/.test(lowered)) {
      section = 'practical';
      practicalHeading = /^location/.test(lowered) ? 'location' : 'schedule';
      continue;
    }

    if (section === 'ignore') continue;
    if (section === 'practical') {
      const explicitPractical = /\b(?:hours? per week|days? per week|shift|part[- ]time|full[- ]time|hybrid|weekend|travel|location|work(?:ing)? pattern)\b/i.test(line);
      const days = /^(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)(?:\s+(?:to|and|[-–])\s+(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday))?/i.test(line);
      const place = practicalHeading === 'location' && /^[\p{L}\p{N} ,.'\-]{2,100}$/u.test(line);
      if (explicitPractical || days || place) practicalIssues.push(line);
      continue;
    }

    if (['training will be provided', 'training is provided', 'full training provided'].some((cue) => lowered.includes(cue))) {
      requirements.push({ text: line, category: 'trainable' });
      continue;
    }

    const isBullet = /^\s*(?:[-*•]|\d+[.)](?!\d))/.test(raw);
    const looksLikeCriterion = ['experience', 'knowledge', 'ability to', 'able to', 'skill', 'required', 'essential', 'desirable', 'qualification'].some((cue) => lowered.includes(cue));
    if (section === null && !looksLikeCriterion) continue;
    if (!isBullet && !looksLikeCriterion) continue;
    if (line.length > 350) continue;

    const category: Requirement['category'] = section === 'desirable' || lowered.includes('desirable') || lowered.includes('ideally')
      ? 'desirable'
      : 'essential';
    requirements.push({ text: line, category });
  }

  const seen = new Set<string>();
  const uniqueRequirements = requirements.filter((item) => {
    const key = item.text.toLowerCase();
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });

  return {
    provider: 'local-parser',
    requirements: uniqueRequirements.slice(0, 24),
    practicalIssues: Array.from(new Set(practicalIssues)).slice(0, 10),
  };
}
