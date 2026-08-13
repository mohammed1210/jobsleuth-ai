'use client';

import type { EvidenceCard } from '@/lib/applyApi';
import EvidenceCompleteness from './EvidenceCompleteness';

type Props = {
  card: EvidenceCard;
  onEdit: (card: EvidenceCard) => void;
  onRemove?: (card: EvidenceCard) => void;
};

export default function EvidenceCardView({ card, onEdit, onRemove }: Props) {
  return (
    <article className="card p-5 space-y-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="text-lg font-bold text-gray-900">{card.title}</h3>
          <p className="mt-1 text-xs text-gray-500">Confidence {card.confidence}%</p>
        </div>
        <div className="flex gap-2">
          <button type="button" className="btn-secondary px-3 py-2 text-sm" onClick={() => onEdit(card)}>
            Edit
          </button>
          {onRemove && (
            <button type="button" className="px-3 py-2 text-sm font-semibold text-red-700" onClick={() => onRemove(card)}>
              Delete
            </button>
          )}
        </div>
      </div>

      <EvidenceCompleteness card={card} />

      {card.situation && (
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">Context</p>
          <p className="mt-1 text-sm text-gray-700">{card.situation}</p>
        </div>
      )}

      {card.actions.length > 0 && (
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">Personal actions</p>
          <ul className="mt-1 list-disc space-y-1 pl-5 text-sm text-gray-700">
            {card.actions.map((action, index) => <li key={`${card.id}-action-${index}`}>{action}</li>)}
          </ul>
        </div>
      )}

      {card.outcome && (
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">Outcome</p>
          <p className="mt-1 text-sm text-gray-700">{card.outcome}</p>
        </div>
      )}

      {card.authority_context && (
        <div className="rounded-xl bg-gray-50 px-4 py-3">
          <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">Authority accuracy</p>
          <p className="mt-1 text-sm text-gray-700">{card.authority_context}</p>
        </div>
      )}

      {(card.behaviours.length > 0 || card.skills.length > 0) && (
        <div className="flex flex-wrap gap-2">
          {[...card.behaviours, ...card.skills].map((label) => (
            <span key={`${card.id}-${label}`} className="rounded-full bg-brand-50 px-3 py-1 text-xs font-medium text-brand-700">
              {label}
            </span>
          ))}
        </div>
      )}
    </article>
  );
}
