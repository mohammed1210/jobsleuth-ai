import type { EvidenceCard } from '@/lib/applyApi';

export default function DetailsFields({ initial }: { initial?: EvidenceCard | null }) {
  return (
    <div className="space-y-4">
      <textarea name="authority_context" defaultValue={initial?.authority_context ?? ''} className="min-h-20 w-full rounded-xl border px-4 py-3" placeholder="Decision ownership / authority" />
      <textarea name="outcome" defaultValue={initial?.outcome ?? ''} className="min-h-20 w-full rounded-xl border px-4 py-3" placeholder="Outcome" />
      <textarea name="reflection" defaultValue={initial?.reflection ?? ''} className="min-h-20 w-full rounded-xl border px-4 py-3" placeholder="Reflection / learning" />
    </div>
  );
}
