import type { Session } from '@supabase/supabase-js';

import { apiError, getBackendUrl } from '@/lib/backendConfig';

export type PaymentSignal = 'yes' | 'maybe' | 'no';

export type PilotFeedbackPayload = {
  provider: string;
  recommendation: string;
  application_type: string;
  word_count: number;
  usefulness: number;
  would_submit: boolean;
  recommendation_trust: boolean;
  material_time_saving: boolean;
  would_use_again: boolean;
  payment_signal: PaymentSignal;
};

export async function savePilotFeedback(session: Session, payload: PilotFeedbackPayload) {
  const response = await fetch(`${getBackendUrl()}/pilot-feedback`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${session.access_token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw await apiError(response, 'Could not save pilot feedback');
  return response.json();
}
