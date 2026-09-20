import type { EvidenceCard } from '@/lib/applyApi';

export default function TagsFields({ initial }: { initial?: EvidenceCard | null }) {
  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-2">
        <label className="block">
          <span className="text-sm font-semibold text-gray-800">Civil Service behaviours</span>
          <input
            name="behaviours"
            defaultValue={initial?.behaviours.join(', ') ?? ''}
            className="mt-1 w-full rounded-xl border px-4 py-3"
            placeholder="Managing a Quality Service, Making Effective Decisions"
          />
          <span className="mt-1 block text-xs text-gray-500">Use the exact behaviour names where possible so JobSleuth can reuse this example for behaviour components.</span>
        </label>
        <label className="block">
          <span className="text-sm font-semibold text-gray-800">Skills / capabilities</span>
          <input
            name="skills"
            defaultValue={initial?.skills.join(', ') ?? ''}
            className="mt-1 w-full rounded-xl border px-4 py-3"
            placeholder="stakeholder management, analysis, investigation"
          />
        </label>
      </div>

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
    </div>
  );
}
