import type { Session } from '@supabase/supabase-js';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

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

export type VacancyAnalysis = {
  ok: boolean;
  analysis_provider: string;
  decision: 'APPLY' | 'CONSIDER' | 'SKIP';
  requirements: Array<{
    requirement: string;
    category: string;
    blocker: boolean;
    status: string;
    evidence: Array<{ id?: string; title: string; matched_terms: string[] }>;
  }>;
  practical_fit: { status: string; issues: string[] };
};

function authHeaders(session: Session) {
  return {
    Authorization: `Bearer ${session.access_token}`,
    'Content-Type': 'application/json',
  };
}

export async function fetchEvidence(session: Session): Promise<EvidenceCard[]> {
  const response = await fetch(`${BACKEND_URL}/evidence`, {
    headers: authHeaders(session),
    cache: 'no-store',
  });
  if (!response.ok) throw new Error('Failed to load evidence');
  return response.json();
}

export async function createEvidence(
  session: Session,
  input: Pick<EvidenceCard, 'title'> & Partial<EvidenceCard>,
): Promise<EvidenceCard> {
  const response = await fetch(`${BACKEND_URL}/evidence`, {
    method: 'POST',
    headers: authHeaders(session),
    body: JSON.stringify(input),
  });
  if (!response.ok) throw new Error('Failed to save evidence');
  return response.json();
}

export async function analyseVacancy(
  session: Session,
  requirements: Requirement[],
  evidenceCards: EvidenceCard[],
  practicalIssues: string[],
): Promise<VacancyAnalysis> {
  const response = await fetch(`${BACKEND_URL}/vacancy-analysis`, {
    method: 'POST',
    headers: authHeaders(session),
    body: JSON.stringify({
      job: { title: 'User supplied vacancy' },
      requirements,
      evidence_cards: evidenceCards,
      practical_issues: practicalIssues,
    }),
  });
  if (!response.ok) throw new Error('Vacancy analysis failed');
  return response.json();
}
