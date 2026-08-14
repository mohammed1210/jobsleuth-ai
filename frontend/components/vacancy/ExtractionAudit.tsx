import type { IntelligenceItem } from '@/lib/vacancyIntelligenceApi';

type Props = {
  items: IntelligenceItem[];
  provider: string | null;
};

const label = (value: string) => value.replace('-', ' ');

export default function ExtractionAudit({ items, provider }: Props) {
  if (!items.length) return null;

  return (
    <section className="card p-5 space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-xl font-bold text-gray-900">Extraction audit</h2>
          <p className="text-sm text-gray-500">Each item stays tied to supporting text from the vacancy.</p>
        </div>
        {provider && <span className="text-xs font-medium text-gray-500">{provider}</span>}
      </div>
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
    </section>
  );
}
