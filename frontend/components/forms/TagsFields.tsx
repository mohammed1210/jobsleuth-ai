import type { EvidenceCard } from '@/lib/applyApi';

export default function TagsFields({ initial }: { initial?: EvidenceCard | null }) {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <label className="block">
        <span className="text-sm font-semibold text-gray-800">Tags</span>
        <input name="tags" defaultValue={initial?.tags.join(', ') ?? ''} className="mt-1 w-full rounded-xl border px-4 py-3" placeholder="leadership, investigation, risk" />
      </label>
      <label className="block">
        <span className="text-sm font-semibold text-gray-800">Confidence</span>
        <input name="confidence" type="number" min="0" max="100" step="5" defaultValue={initial?.confidence ?? 70} className="mt-1 w-full rounded-xl border px-4 py-3" />
      </label>
    </div>
  );
}
