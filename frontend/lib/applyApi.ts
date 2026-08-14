import type { Session } from '@supabase/supabase-js';

import { apiError, getBackendUrl } from '@/lib/backendConfig';

export type EvidenceCard = {
  id: string;
  title: string;
  situation?: string;
  task?: string;
  actions: string[];
  outcome?: string;
  reflection?: string;
  tags: string[];
  behaviours: string[];
  skills: string[];
  authority_context?: string | null;
  confidence: number;
};

export type Requirement = {
  text: string;
  category: 'essential' | 'desirable' | 'trainable';
  blocker?: boolean;
};

export type EvidenceMatch = {
  id?: string;
  title: string;
  strength: 'strong' | 'partial' | 'weak' | 'missing';
  score: number;
  confidence: number;
  why: string;
  gaps: string[];
  supporting_facts: Array<{ field: string; text: string }>;
  signals: { concepts?: string[]; matched_terms?: string[]; evidence_quality?: number; semantic?: boolean };
  matched_terms: string[];
};

export type RequirementAnalysis = {
  requirement: string;
  category: string;
  blocker: boolean;
  status: string;
  match_strength: 'strong' | 'partial' | 'weak' | 'missing' | 'trainable';
  confidence: number;
  why: string;
  gaps: string[];
  evidence: EvidenceMatch[];
};

export type VacancyAnalysis = {
  ok: boolean;
  analysis_provider: string;
  decision: 'APPLY' | 'CONSIDER' | 'SKIP';
  decision_reasons?: string[];
  requirements: RequirementAnalysis[];
  practical_fit: { status: string; issues: string[] };
};

function authHeaders(session: Session) {
  return {
    Authorization: `Bearer ${session.access_token}`,
    'Content-Type': 'application/json',
  };
}

export async function fetchEvidence(session: Session): Promise<EvidenceCard[]> {
  const response = await fetch(`${getBackendUrl()}/evidence`, {
    headers: authHeaders(session),
    cache: 'no-store',
  });
  if (!response.ok) throw await apiError(response, 'Failed to load evidence');
  return response.json();
}

export async function createEvidence(
  session: Session,
  input: Pick<EvidenceCard, 'title'> & Partial<EvidenceCard>,
): Promise<EvidenceCard> {
  const response = await fetch(`${getBackendUrl()}/evidence`, {
    method: 'POST',
    headers: authHeaders(session),
    body: JSON.stringify(input),
  });
  if (!response.ok) throw await apiError(response, 'Failed to save evidence');
  return response.json();
}

export async function analyseVacancy(
  session: Session,
  requirements: Requirement[],
  evidenceCards: EvidenceCard[],
  practicalIssues: string[],
): Promise<VacancyAnalysis> {
  const response = await fetch(`${getBackendUrl()}/vacancy-analysis`, {
    method: 'POST',
    headers: authHeaders(session),
    body: JSON.stringify({
      job: { title: 'User supplied vacancy' },
      requirements,
      evidence_cards: evidenceCards,
      practical_issues: practicalIssues,
    }),
  });
  if (!response.ok) throw await apiError(response, 'Vacancy analysis failed');
  return response.json();
}
