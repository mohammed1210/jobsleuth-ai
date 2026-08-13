import type { Session } from '@supabase/supabase-js';
import type { EvidenceCard } from '@/lib/applyApi';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

export async function updateEvidence(session: Session, id: string, input: Partial<EvidenceCard>) {
  const response = await fetch(`${BACKEND_URL}/evidence/${id}`, {
    method: 'PATCH',
    headers: {
      Authorization: `Bearer ${session.access_token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(input),
  });
  if (!response.ok) throw new Error('Failed to update evidence');
  return response.json() as Promise<EvidenceCard>;
}
