import type { Requirement } from '@/lib/applyApi';

export type ParsedVacancy = {
  provider: 'local-parser';
  requirements: Requirement[];
  practicalIssues: string[];
};

const cleanLine = (value: string) => value.replace(/^\s*(?:[-*•]|\d+[.)])\s*/, '').trim();

export function parseVacancyText(text: string): ParsedVacancy {
  const requirements: Requirement[] = [];
  const practicalIssues: string[] = [];
  let section: 'essential' | 'desirable' | 'practical' = 'essential';

  for (const raw of text.split(/\r?\n/)) {
    const line = cleanLine(raw);
    if (!line) continue;
    const lowered = line.toLowerCase().replace(/:$/, '');

    if (line.length <= 90 && (lowered.includes('desirable') || lowered.includes('nice to have'))) {
      section = 'desirable';
      continue;
    }
    if (line.length <= 90 && ['essential criteria', 'essential requirements', 'person specification', 'what you will need'].some((cue) => lowered.includes(cue))) {
      section = 'essential';
      continue;
    }
    if (line.length <= 90 && ['working pattern', 'working arrangements', 'hours', 'location', 'travel requirements'].some((cue) => lowered.includes(cue))) {
      section = 'practical';
      continue;
    }

    if (section === 'practical') {
      practicalIssues.push(line);
      continue;
    }

    if (['training will be provided', 'training is provided', 'full training provided'].some((cue) => lowered.includes(cue))) {
      requirements.push({ text: line, category: 'trainable' });
      continue;
    }

    const isBullet = /^\s*(?:[-*•]|\d+[.)])/.test(raw);
    const looksLikeCriterion = ['experience', 'knowledge', 'ability to', 'able to', 'skill', 'required', 'essential', 'desirable', 'qualification'].some((cue) => lowered.includes(cue));
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
