'use client';

import type { EvidenceCard } from '@/lib/applyApi';
import CoreFields from '@/components/forms/CoreFields';
import DetailsFields from '@/components/forms/DetailsFields';
import TagsFields from '@/components/forms/TagsFields';

type Props = {
  initial?: EvidenceCard | null;
  busy?: boolean;
  onSave: (input: Pick<EvidenceCard, 'title'> & Partial<EvidenceCard>) => Promise<void> | void;
  onCancel?: () => void;
};

export default function RecordForm({ initial, busy = false, onCancel }: Props) {
  return (
    <form className="card p-6 space-y-5">
      <CoreFields initial={initial} />
      <DetailsFields initial={initial} />
      <TagsFields initial={initial} />
      <div className="flex gap-3">
        <button type="submit" disabled={busy} className="btn-primary disabled:opacity-60">Save</button>
        {initial && onCancel && <button type="button" onClick={onCancel} className="btn-secondary">Cancel</button>}
      </div>
    </form>
  );
}
