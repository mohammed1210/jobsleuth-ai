import type { PaymentSignal } from '@/lib/pilotFeedbackApi';

export type BinaryPilotAnswer = '' | 'yes' | 'no';

export type PilotFeedbackDraft = {
  usefulness: number | null;
  wouldSubmit: BinaryPilotAnswer;
  recommendationTrust: BinaryPilotAnswer;
  materialTimeSaving: BinaryPilotAnswer;
  wouldUseAgain: BinaryPilotAnswer;
  paymentSignal: PaymentSignal | '';
};

export const EMPTY_PILOT_FEEDBACK: PilotFeedbackDraft = {
  usefulness: null,
  wouldSubmit: '',
  recommendationTrust: '',
  materialTimeSaving: '',
  wouldUseAgain: '',
  paymentSignal: '',
};

export function isPilotFeedbackComplete(value: PilotFeedbackDraft): boolean {
  return value.usefulness !== null
    && value.wouldSubmit !== ''
    && value.recommendationTrust !== ''
    && value.materialTimeSaving !== ''
    && value.wouldUseAgain !== ''
    && value.paymentSignal !== '';
}

export function binaryPilotAnswer(value: BinaryPilotAnswer): boolean {
  if (value === '') throw new Error('Pilot feedback answer is required.');
  return value === 'yes';
}
