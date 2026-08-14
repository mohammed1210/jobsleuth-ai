import type { Session } from '@supabase/supabase-js';
import type { EvidenceCard } from '@/lib/applyApi';
import { apiError, getBackendUrl } from '@/lib/backendConfig';

export async function updateEvidence(session: Session, id: string, input: Partial<EvidenceCard>) {
  const response = await fetch(`${getBackendUrl()}/evidence/${id}`, {
    method: 'PATCH',
    headers: {
      Authorization: `Bearer ${session.access_token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(input),
  });
  if (!response.ok) throw await apiError(response, 'Failed to update evidence');
  return response.json() as Promise<EvidenceCard>;
}
