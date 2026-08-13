'use client';

import { FormEvent } from 'react';
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

const text = (value: FormDataEntryValue | null) => String(value ?? '').trim();
const list = (value: FormDataEntryValue | null) => text(value).split(/\n|,/).map((item) => item.trim()).filter(Boolean);

export default function RecordForm({ initial, busy = false, onSave, onCancel }: Props) {
  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const title = text(data.get('title'));
    if (!title) return;
    await onSave({
      title,
      situation: text(data.get('situation')),
      task: text(data.get('task')),
      actions: list(data.get('actions')),
      authority_context: text(data.get('authority_context')) || null,
      outcome: text(data.get('outcome')),
      reflection: text(data.get('reflection')),
      tags: list(data.get('tags')),
      confidence: Number(data.get('confidence') ?? 70),
    });
  };

  return (
    <form onSubmit={submit} className="card p-6 space-y-5">
      <CoreFields initial={initial} />
      <DetailsFields initial={initial} />
      <TagsFields initial={initial} />
      <div className="flex gap-3">
        <button type="submit" disabled={busy} className="btn-primary disabled:opacity-60">{busy ? 'Saving…' : 'Save evidence'}</button>
        {initial && onCancel && <button type="button" onClick={onCancel} className="btn-secondary">Cancel</button>}
      </div>
    </form>
  );
}
