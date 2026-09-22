import type { IntelligenceItem } from '@/lib/vacancyIntelligenceApi';

type Props = {
  items: IntelligenceItem[];
  provider: string | null;
};

const label = (value: string) => value.replace('-', ' ');

export default function ExtractionAudit({ items, provider }: Props) {
  if (!items.length) return null;

  return (
    <details className="card">
      <summary className="cursor-pointer list-none px-5 py-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="font-semibold text-gray-900">Extraction audit</p>
            <p className="mt-1 text-sm text-gray-500">{items.length} grounded item{items.length === 1 ? '' : 's'} · open only if you want to inspect the source mapping.</p>
          </div>
          <div className="flex items-center gap-3">
            {provider && <span className="text-xs font-medium text-gray-400">{provider}</span>}
            <span className="rounded-full bg-gray-100 px-3 py-1 text-xs font-semibold text-gray-600">Details</span>
          </div>
        </div>
      </summary>

      <div className="border-t p-5">
        <div className="space-y-3">
          {items.map((item, index) => (
            <div key={`${item.category}-${index}-${item.text}`} className="rounded-xl border p-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="font-semibold text-gray-900">{item.text}</p>
                  <p className="mt-1 text-xs uppercase tracking-wide text-gray-500">{label(item.category)}</p>
                </div>
                <div className="text-right text-xs text-gray-500">
                  <p>{Math.round(item.confidence * 100)}% confidence</p>
                  {item.explicit_blocker && <p className="mt-1 font-semibold text-gray-700">Explicit requirement</p>}
                </div>
              </div>
              <div className="mt-3 rounded-lg bg-gray-50 px-3 py-2 text-sm text-gray-600">
                <span className="font-medium text-gray-700">Source:</span> {item.source_text}
              </div>
            </div>
          ))}
        </div>
      </div>
    </details>
  );
}
