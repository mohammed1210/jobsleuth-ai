import type { Session } from '@supabase/supabase-js';

import type { EvidenceCard, RequirementAnalysis } from '@/lib/applyApi';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

export type ApplicationType = 'statement_of_suitability' | 'criteria_response';

export type ApplicationCoverage = {
  requirement: string;
  category: string;
  match_strength: string;
  status: 'covered' | 'partially-covered' | 'evidence-gap' | 'not-used';
  evidence_ids: string[];
};

export type ApplicationParagraph = {
  text: string;
  requirement_indices: number[];
  evidence_ids: string[];
  supporting_facts: Array<{ evidence_id: string; field: string; text: string }>;
  grounding_status: 'grounded';
};

export type ApplicationDraftResult = {
  ok: boolean;
  can_generate: boolean;
  provider: string;
  application_type: ApplicationType;
  word_limit: number;
  word_count: number;
  draft: string;
  paragraphs: ApplicationParagraph[];
  coverage: ApplicationCoverage[];
  warnings: string[];
};

function authHeaders(session: Session) {
  return {
    Authorization: `Bearer ${session.access_token}`,
    'Content-Type': 'application/json',
  };
}

function evidenceIdsForRequirement(requirement: RequirementAnalysis) {
  return requirement.evidence
    .filter((item) => item.id && (item.strength === 'strong' || item.strength === 'partial'))
    .map((item) => item.id as string);
}

export async function buildApplication(
  session: Session,
  input: {
    roleTitle: string;
    organisation: string;
    applicationType: ApplicationType;
    wordLimit: number;
    requirements: RequirementAnalysis[];
    evidenceCards: EvidenceCard[];
  },
): Promise<ApplicationDraftResult> {
  const requirements = input.requirements.map((requirement) => ({
    text: requirement.requirement,
    category: requirement.category,
    match_strength: requirement.match_strength,
    evidence_ids: evidenceIdsForRequirement(requirement),
  }));

  const usedIds = new Set(requirements.flatMap((requirement) => requirement.evidence_ids));
  const evidenceCards = input.evidenceCards.filter((card) => usedIds.has(card.id));

  const response = await fetch(`${BACKEND_URL}/application-builder`, {
    method: 'POST',
    headers: authHeaders(session),
    body: JSON.stringify({
      job: {
        title: input.roleTitle.trim() || 'the role',
        organisation: input.organisation.trim(),
      },
      application_type: input.applicationType,
      word_limit: input.wordLimit,
      requirements,
      evidence_cards: evidenceCards,
    }),
  });

  if (!response.ok) throw new Error('Application draft failed');
  return response.json();
}
