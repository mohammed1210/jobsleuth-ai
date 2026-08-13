import type { EvidenceCard } from '@/lib/applyApi';
import CompletenessBar from './CompletenessBar';

export function getEvidenceCompleteness(card: Partial<EvidenceCard>) {
  const checks = [
    Boolean(card.title?.trim()),
    Boolean(card.situation?.trim()),
    Boolean(card.task?.trim()),
    Boolean(card.actions?.length),
    Boolean(card.outcome?.trim()),
    Boolean(card.authority_context?.trim()),
    Boolean(card.tags?.length),
    Boolean(card.reflection?.trim()),
  ];

  return Math.round((checks.filter(Boolean).length / checks.length) * 100);
}

export default function EvidenceCompleteness({ card }: { card: Partial<EvidenceCard> }) {
  return <CompletenessBar value={getEvidenceCompleteness(card)} />;
}
