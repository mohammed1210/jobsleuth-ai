'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import type { Session } from '@supabase/supabase-js';
import HeaderClient from '@/components/HeaderClient';
import RecordForm from '@/components/RecordForm';
import EvidenceCardView from '@/components/evidence/EvidenceCardView';
import { fetchEvidence, type EvidenceCard } from '@/lib/applyApi';
import { getSupabaseClient, isSupabaseConfigured } from '@/lib/supabaseClient';

export default function ApplyPage() {
  const [session, setSession] = useState<Session | null>(null);
  const [records, setRecords] = useState<EvidenceCard[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const run = async () => {
      if (!isSupabaseConfigured()) {
        setError('Supabase is not configured yet.');
        setLoading(false);
        return;
      }
      const supabase = getSupabaseClient();
      const { data } = await supabase.auth.getSession();
      setSession(data.session);
      if (data.session) {
        try {
          setRecords(await fetchEvidence(data.session));
        } catch {
          setError('Could not load your Evidence Bank.');
        }
      }
      setLoading(false);
    };
    run();
  }, []);

  if (!loading && !session) {
    return (
      <div className="min-h-screen">
        <HeaderClient />
        <main className="max-w-3xl mx-auto px-6 py-12">
          <div className="card p-10 text-center">
            <h1 className="text-3xl font-bold text-gray-900 mb-3">Sign in to use your Evidence Bank</h1>
            <p className="text-gray-600 mb-6">Your saved examples are private to your account.</p>
            <Link href="/magic-login" className="btn-primary inline-flex">Sign in</Link>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <HeaderClient />
      <main className="max-w-6xl mx-auto px-6 py-10 space-y-8">
        <div>
          <p className="text-sm font-semibold text-brand-700 mb-2">JobSleuth Evidence Bank</p>
          <h1 className="text-4xl font-bold text-gray-900">Capture facts once. Reuse them well.</h1>
          <p className="text-gray-600 mt-3">Build a private library of examples that can support vacancy analysis and application drafting.</p>
        </div>
        {error && <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-amber-800">{error}</div>}
        <div className="grid gap-8 lg:grid-cols-[420px_1fr]">
          <RecordForm onSave={async () => {}} />
          <div className="space-y-4">
            {records.map((card) => <EvidenceCardView key={card.id} card={card} onEdit={() => {}} onRemove={() => {}} />)}
          </div>
        </div>
      </main>
    </div>
  );
}
