'use client';

import { useEffect, useState } from 'react';
import type { Session } from '@supabase/supabase-js';
import { createEvidence, fetchEvidence, type EvidenceCard } from '@/lib/applyApi';
import { updateEvidence } from '@/lib/updateEvidence';

export function useRecords(session: Session | null) {
  const [records, setRecords] = useState<EvidenceCard[]>([]);
  const [editing, setEditing] = useState<EvidenceCard | null>(null);
  const [loadingRecords, setLoadingRecords] = useState(false);
  const [savingRecord, setSavingRecord] = useState(false);
  const [recordError, setRecordError] = useState<string | null>(null);

  useEffect(() => {
    if (!session) return;
    setLoadingRecords(true);
    fetchEvidence(session)
      .then(setRecords)
      .catch(() => setRecordError('Could not load saved records.'))
      .finally(() => setLoadingRecords(false));
  }, [session]);

  const saveRecord = async (input: Pick<EvidenceCard, 'title'> & Partial<EvidenceCard>) => {
    if (!session) return;
    setSavingRecord(true);
    setRecordError(null);
    try {
      if (editing) {
        const saved = await updateEvidence(session, editing.id, input);
        setRecords((current) => current.map((card) => card.id === saved.id ? saved : card));
        setEditing(null);
      } else {
        const saved = await createEvidence(session, input);
        setRecords((current) => [saved, ...current]);
      }
    } catch {
      setRecordError('Could not save this record.');
    } finally {
      setSavingRecord(false);
    }
  };

  return { records, editing, setEditing, loadingRecords, savingRecord, recordError, setRecordError, saveRecord };
}
