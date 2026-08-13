import type { Session } from '@supabase/supabase-js';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

export async function removeRecord(session: Session, id: string) {
  const response = await fetch(`${BACKEND_URL}/evidence/${id}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${session.access_token}` },
  });
  if (!response.ok) throw new Error('Failed to remove record');
}
