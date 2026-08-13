import type { EvidenceCard } from '@/lib/applyApi';

export default function CoreFields({ initial }: { initial?: EvidenceCard | null }) {
  return (
    <div className="space-y-4">
      <input name="title" required maxLength={140} defaultValue={initial?.title ?? ''} className="w-full rounded-xl border px-4 py-3" placeholder="Title" />
      <textarea name="situation" defaultValue={initial?.situation ?? ''} className="min-h-24 w-full rounded-xl border px-4 py-3" placeholder="Context" />
      <textarea name="task" defaultValue={initial?.task ?? ''} className="min-h-20 w-full rounded-xl border px-4 py-3" placeholder="Responsibility" />
      <textarea name="actions" defaultValue={initial?.actions.join('\n') ?? ''} className="min-h-28 w-full rounded-xl border px-4 py-3" placeholder="Actions, one per line" />
    </div>
  );
}
