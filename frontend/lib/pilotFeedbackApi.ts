import type { Session } from '@supabase/supabase-js';
import { apiFetch } from '@/lib/applyApi';

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
  return apiFetch('/pilot-feedback', session, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}
