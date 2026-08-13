'use client';

import { useEffect, useState } from 'react';
import type { Session } from '@supabase/supabase-js';
import { fetchEvidence, type EvidenceCard } from '@/lib/applyApi';

export function useRecords(session: Session | null) {
  const [records, setRecords] = useState<EvidenceCard[]>([]);
  const [loadingRecords, setLoadingRecords] = useState(false);
  const [recordError, setRecordError] = useState<string | null>(null);

  useEffect(() => {
    if (!session) return;
    setLoadingRecords(true);
    fetchEvidence(session)
      .then(setRecords)
      .catch(() => setRecordError('Could not load saved records.'))
      .finally(() => setLoadingRecords(false));
  }, [session]);

  return { records, setRecords, loadingRecords, recordError, setRecordError };
}
