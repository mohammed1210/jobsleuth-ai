import type { EvidenceCard } from '@/lib/applyApi';

export default function CoreFields({ initial }: { initial?: EvidenceCard | null }) {
  return (
    <div className="space-y-4">
      <label className="block">
        <span className="text-sm font-semibold text-gray-800">Title</span>
        <input name="title" required maxLength={140} defaultValue={initial?.title ?? ''} className="mt-1 w-full rounded-xl border px-4 py-3" />
      </label>
      <label className="block">
        <span className="text-sm font-semibold text-gray-800">Context</span>
        <textarea name="situation" defaultValue={initial?.situation ?? ''} className="mt-1 min-h-24 w-full rounded-xl border px-4 py-3" />
      </label>
      <label className="block">
        <span className="text-sm font-semibold text-gray-800">Responsibility</span>
        <textarea name="task" defaultValue={initial?.task ?? ''} className="mt-1 min-h-20 w-full rounded-xl border px-4 py-3" />
      </label>
      <label className="block">
        <span className="text-sm font-semibold text-gray-800">Actions</span>
        <textarea name="actions" defaultValue={initial?.actions.join('\n') ?? ''} className="mt-1 min-h-28 w-full rounded-xl border px-4 py-3" placeholder="One action per line" />
      </label>
    </div>
  );
}
