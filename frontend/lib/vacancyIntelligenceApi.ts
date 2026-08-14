import type { Session } from '@supabase/supabase-js';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

export type IntelligenceCategory = 'eligibility' | 'essential' | 'desirable' | 'trainable' | 'practical';

export type IntelligenceItem = {
  text: string;
  category: IntelligenceCategory;
  source_text: string;
  confidence: number;
  explicit_blocker: boolean;
};

export type VacancyIntelligence = {
  ok: boolean;
  provider: string;
  eligibility: IntelligenceItem[];
  requirements: IntelligenceItem[];
  practical: IntelligenceItem[];
  summary: {
    items: number;
    eligibility: number;
    requirements: number;
    practical: number;
    low_confidence: number;
  };
};

export async function extractVacancyIntelligence(session: Session, vacancyText: string): Promise<VacancyIntelligence> {
  const response = await fetch(`${BACKEND_URL}/vacancy-intelligence`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${session.access_token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ vacancy_text: vacancyText }),
  });
  if (!response.ok) throw new Error('Vacancy intelligence unavailable');
  return response.json();
}
