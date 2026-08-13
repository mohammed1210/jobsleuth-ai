import type { EvidenceCard } from '@/lib/applyApi';

export default function TagsFields({ initial }: { initial?: EvidenceCard | null }) {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <input name="tags" defaultValue={initial?.tags.join(', ') ?? ''} className="w-full rounded-xl border px-4 py-3" placeholder="Tags" />
      <input name="confidence" type="number" min="0" max="100" step="5" defaultValue={initial?.confidence ?? 70} className="w-full rounded-xl border px-4 py-3" />
    </div>
  );
}
