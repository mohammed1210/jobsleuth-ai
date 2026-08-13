'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import type { Session } from '@supabase/supabase-js';
import HeaderClient from '@/components/HeaderClient';
import RecordForm from '@/components/RecordForm';
import EvidenceCardView from '@/components/evidence/EvidenceCardView';
import { getSupabaseClient, isSupabaseConfigured } from '@/lib/supabaseClient';
import { useRecords } from '@/lib/useRecords';

export default function ApplyPage() {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const bank = useRecords(session);

  useEffect(() => {
    const run = async () => {
      if (!isSupabaseConfigured()) {
        setError('Service is not configured yet.');
        setLoading(false);
        return;
      }
      const supabase = getSupabaseClient();
      const { data } = await supabase.auth.getSession();
      setSession(data.session);
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
            <h1 className="text-3xl font-bold text-gray-900 mb-3">Sign in required</h1>
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
          <p className="text-sm font-semibold text-brand-700 mb-2">Evidence Bank</p>
          <h1 className="text-4xl font-bold text-gray-900">Saved examples</h1>
          <p className="text-gray-600 mt-3">Capture structured details and keep them consistent.</p>
        </div>
        {(error || bank.recordError) && <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-amber-800">{error || bank.recordError}</div>}
        <div className="grid gap-8 lg:grid-cols-[420px_1fr]">
          <RecordForm key={bank.editing?.id ?? 'new'} initial={bank.editing} busy={bank.savingRecord} onSave={bank.saveRecord} onCancel={() => bank.setEditing(null)} />
          <div className="space-y-4">
            {bank.loadingRecords && <div className="card p-8 text-center text-gray-600">Loading…</div>}
            {!bank.loadingRecords && bank.records.length === 0 && <div className="card p-8 text-center text-gray-600">No saved examples yet.</div>}
            {bank.records.map((card) => <EvidenceCardView key={card.id} card={card} onEdit={bank.setEditing} />)}
          </div>
        </div>
      </main>
    </div>
  );
}
