'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import type { Session } from '@supabase/supabase-js';
import HeaderClient from '@/components/HeaderClient';
import RecordForm from '@/components/RecordForm';
import EvidenceCardView from '@/components/evidence/EvidenceCardView';
import { getSupabaseClient, isSupabaseConfigured } from '@/lib/supabaseClient';
import { removeRecord } from '@/lib/removeRecord';
import { useRecords } from '@/lib/useRecords';

const EVIDENCE_TARGET_KEY = 'jobsleuth.evidence.target.v1';

type EvidenceTarget = {
  userId: string;
  requirement: string;
  category: string;
  matchStrength: string;
  gaps: string[];
  returnTo: string;
  createdAt: string;
};

export default function ApplyPage() {
  const router = useRouter();
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [target, setTarget] = useState<EvidenceTarget | null>(null);
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
      if (data.session) {
        try {
          const raw = window.sessionStorage.getItem(EVIDENCE_TARGET_KEY);
          if (raw) {
            const saved = JSON.parse(raw) as Partial<EvidenceTarget>;
            if (saved.userId === data.session.user.id && typeof saved.requirement === 'string') {
              setTarget({
                userId: saved.userId,
                requirement: saved.requirement,
                category: typeof saved.category === 'string' ? saved.category : 'criterion',
                matchStrength: typeof saved.matchStrength === 'string' ? saved.matchStrength : 'weak',
                gaps: Array.isArray(saved.gaps) ? saved.gaps.filter((gap): gap is string => typeof gap === 'string') : [],
                returnTo: typeof saved.returnTo === 'string' ? saved.returnTo : '/apply/vacancy',
                createdAt: typeof saved.createdAt === 'string' ? saved.createdAt : new Date().toISOString(),
              });
            } else {
              window.sessionStorage.removeItem(EVIDENCE_TARGET_KEY);
            }
          }
        } catch {
          window.sessionStorage.removeItem(EVIDENCE_TARGET_KEY);
        }
      }
      setLoading(false);
    };
    run();
  }, []);

  const saveEvidence = async (input: Parameters<typeof bank.saveRecord>[0]) => {
    const saved = await bank.saveRecord(input);
    if (!saved || !target) return;
    window.sessionStorage.removeItem(EVIDENCE_TARGET_KEY);
    setTarget(null);
    router.push(target.returnTo || '/apply/vacancy');
  };

  const dismissTarget = () => {
    window.sessionStorage.removeItem(EVIDENCE_TARGET_KEY);
    setTarget(null);
  };

  const remove = async (id: string) => {
    if (!session || !window.confirm('Delete this saved example?')) return;
    try {
      await removeRecord(session, id);
      window.location.reload();
    } catch {
      setError('Could not remove this record.');
    }
  };

  if (!loading && !session) {
    return (
      <div className="min-h-screen">
        <HeaderClient />
        <main className="max-w-3xl mx-auto px-6 py-12">
          <div className="card p-10 text-center">
            <h1 className="text-3xl font-bold text-gray-900 mb-3">Sign in required</h1>
            <Link href="/login" className="btn-primary inline-flex">Sign in</Link>
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

        {target && !bank.editing && (
          <section className="rounded-2xl border border-brand-200 bg-brand-50 p-5">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div className="max-w-3xl">
                <p className="text-xs font-semibold uppercase tracking-wide text-brand-700">Strengthen this vacancy match</p>
                <h2 className="mt-2 text-xl font-bold text-gray-900">{target.requirement}</h2>
                <p className="mt-2 text-sm text-gray-700">
                  Add a real example from your own experience that proves this criterion. Do not copy the vacancy wording or invent details.
                </p>
                {target.gaps.length > 0 && (
                  <div className="mt-3">
                    <p className="text-sm font-semibold text-gray-800">Focus on what JobSleuth could not yet prove:</p>
                    <ul className="mt-1 list-disc space-y-1 pl-5 text-sm text-gray-700">
                      {target.gaps.map((gap, index) => <li key={`${gap}-${index}`}>{gap}</li>)}
                    </ul>
                  </div>
                )}
              </div>
              <div className="flex gap-2">
                <Link href={target.returnTo || '/apply/vacancy'} className="btn-secondary text-sm">Back to vacancy</Link>
                <button type="button" onClick={dismissTarget} className="text-sm font-semibold text-gray-600 hover:text-gray-900">Dismiss</button>
              </div>
            </div>
          </section>
        )}

        <div className="grid gap-8 lg:grid-cols-[420px_1fr]">
          <RecordForm key={bank.editing?.id ?? `new-${bank.records.length}-${target?.requirement ?? 'general'}`} initial={bank.editing} busy={bank.savingRecord} onSave={saveEvidence} onCancel={() => bank.setEditing(null)} />
          <div className="space-y-4">
            {bank.loadingRecords && <div className="card p-8 text-center text-gray-600">Loading…</div>}
            {!bank.loadingRecords && bank.records.length === 0 && <div className="card p-8 text-center text-gray-600">No saved examples yet.</div>}
            {bank.records.map((card) => <EvidenceCardView key={card.id} card={card} onEdit={bank.setEditing} onRemove={() => remove(card.id)} />)}
          </div>
        </div>
      </main>
    </div>
  );
}
