import type { RequirementAnalysis } from '@/lib/applyApi';

const strengthLabel: Record<RequirementAnalysis['match_strength'], string> = {
  strong: 'Strong',
  partial: 'Partial',
  weak: 'Weak',
  missing: 'Missing',
  trainable: 'Trainable',
};

const strengthClass: Record<RequirementAnalysis['match_strength'], string> = {
  strong: 'bg-emerald-50 text-emerald-800 border-emerald-200',
  partial: 'bg-amber-50 text-amber-800 border-amber-200',
  weak: 'bg-orange-50 text-orange-800 border-orange-200',
  missing: 'bg-red-50 text-red-800 border-red-200',
  trainable: 'bg-blue-50 text-blue-800 border-blue-200',
};

function normaliseGaps(value: RequirementAnalysis['gaps'] | string | null | undefined): string[] {
  if (Array.isArray(value)) return value.filter((gap): gap is string => typeof gap === 'string' && gap.trim().length > 0);
  if (typeof value === 'string' && value.trim()) return [value.trim()];
  return [];
}

type Props = {
  item: RequirementAnalysis;
  onStrengthen?: (item: RequirementAnalysis) => void;
  onUseCvSignal?: (item: RequirementAnalysis) => void;
};

export default function RequirementMatchCard({ item, onStrengthen, onUseCvSignal }: Props) {
  const top = item.evidence[0];
  const confidence = Math.round((item.confidence ?? 0) * 100);
  const gaps = normaliseGaps(item.gaps);

  return (
    <details className="rounded-xl border bg-white">
      <summary className="cursor-pointer list-none px-4 py-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="min-w-0 flex-1">
            <p className="font-semibold text-gray-900">{item.requirement}</p>
            <p className="mt-1 text-xs uppercase tracking-wide text-gray-500">
              {item.category}{item.blocker ? ' · explicit blocker' : ''}
              {item.profile_support ? ' · CV signal' : ''}
              {gaps.length > 0 ? ` · ${gaps.length} gap${gaps.length === 1 ? '' : 's'}` : ''}
            </p>
          </div>
          <span className={`inline-flex shrink-0 rounded-full border px-3 py-1 text-sm font-bold ${strengthClass[item.match_strength]}`}>
            {strengthLabel[item.match_strength]}
          </span>
        </div>
      </summary>

      <div className="space-y-4 border-t px-4 py-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <p className="max-w-3xl text-sm text-gray-700">{item.why}</p>
          {item.match_strength !== 'trainable' && (
            <p className="text-xs text-gray-500">Confidence {confidence}%</p>
          )}
        </div>

        {item.profile_support && (
          <div className="rounded-xl border border-blue-200 bg-blue-50 p-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-blue-700">CV profile signal</p>
                <p className="mt-1 font-semibold text-blue-950">{item.profile_support.title}</p>
              </div>
              <span className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-blue-800">
                {item.profile_support.strength === 'partial' ? 'Related' : 'Weak signal'}
              </span>
            </div>
            <p className="mt-2 text-sm text-blue-900">{item.profile_support.why}</p>
            {item.profile_support.matched_terms.length > 0 && (
              <p className="mt-2 text-xs text-blue-800">
                Matched: {item.profile_support.matched_terms.slice(0, 6).join(', ')}
              </p>
            )}
          </div>
        )}

        {item.profile_support?.source && onUseCvSignal && (
          <div className="rounded-xl border border-blue-200 bg-blue-50 p-4">
            <p className="text-sm font-semibold text-blue-950">Turn this CV experience into verified evidence</p>
            <p className="mt-1 text-sm text-blue-900">
              JobSleuth can prefill the role, dates, CV highlights and skills. Review the facts and add the missing context, ownership, outcome and learning before saving it to your Evidence Bank.
            </p>
            <button type="button" className="btn-secondary mt-3 px-4 py-2 text-sm" onClick={() => onUseCvSignal(item)}>
              Turn this CV experience into evidence
            </button>
          </div>
        )}

        {top && (
          <div className="rounded-xl bg-gray-50 p-4 space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">Best evidence</p>
                <p className="font-semibold text-gray-900">{top.title}</p>
              </div>
              <p className="text-sm font-semibold text-gray-600">{Math.round(top.score)} / 100</p>
            </div>

            {top.supporting_facts.length > 0 && (
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">Grounded support</p>
                <ul className="mt-2 space-y-2 text-sm text-gray-700">
                  {top.supporting_facts.map((fact, index) => (
                    <li key={`${fact.field}-${index}`} className="border-l-2 border-gray-200 pl-3">
                      <span className="font-medium capitalize">{fact.field.replace('_', ' ')}:</span> {fact.text}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {gaps.length > 0 && (
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">What is still missing</p>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-gray-700">
              {gaps.map((gap, index) => <li key={`${gap}-${index}`}>{gap}</li>)}
            </ul>
          </div>
        )}

        {onStrengthen && !item.profile_support?.source && item.match_strength !== 'strong' && item.match_strength !== 'trainable' && (
          <div className="border-t pt-4">
            <button type="button" className="btn-secondary px-4 py-2 text-sm" onClick={() => onStrengthen(item)}>
              {item.match_strength === 'missing' ? 'Add evidence for this criterion' : 'Strengthen evidence for this criterion'}
            </button>
          </div>
        )}
      </div>
    </details>
  );
}
