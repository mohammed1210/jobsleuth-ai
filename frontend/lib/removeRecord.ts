import type { Session } from '@supabase/supabase-js';

import { apiError, getBackendUrl } from '@/lib/backendConfig';

export async function removeRecord(session: Session, id: string) {
  const response = await fetch(`${getBackendUrl()}/evidence/${id}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${session.access_token}` },
  });
  if (!response.ok) throw await apiError(response, 'Failed to remove record');
}
