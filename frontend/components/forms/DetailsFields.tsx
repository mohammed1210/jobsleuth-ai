import type { EvidenceCard } from '@/lib/applyApi';

export default function DetailsFields({ initial }: { initial?: EvidenceCard | null }) {
  return (
    <div className="space-y-4">
      <label className="block">
        <span className="text-sm font-semibold text-gray-800">Decision ownership / authority</span>
        <textarea name="authority_context" defaultValue={initial?.authority_context ?? ''} className="mt-1 min-h-20 w-full rounded-xl border px-4 py-3" />
      </label>
      <label className="block">
        <span className="text-sm font-semibold text-gray-800">Outcome</span>
        <textarea name="outcome" defaultValue={initial?.outcome ?? ''} className="mt-1 min-h-20 w-full rounded-xl border px-4 py-3" />
      </label>
      <label className="block">
        <span className="text-sm font-semibold text-gray-800">Reflection / learning</span>
        <textarea name="reflection" defaultValue={initial?.reflection ?? ''} className="mt-1 min-h-20 w-full rounded-xl border px-4 py-3" />
      </label>
    </div>
  );
}
