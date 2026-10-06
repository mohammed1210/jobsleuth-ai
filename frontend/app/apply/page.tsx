'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import type { Session } from '@supabase/supabase-js';
import HeaderClient from '@/components/HeaderClient';
import CandidateProfilePanel from '@/components/profile/CandidateProfilePanel';
import RecordForm from '@/components/RecordForm';
import EvidenceCardView from '@/components/evidence/EvidenceCardView';
import { fetchCandidateProfile, type CandidateProfile } from '@/lib/candidateProfileApi';
import type { EvidenceCard } from '@/lib/applyApi';
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
  cvDraft?: {
    title: string;
    situation: string;
    task: string;
    actions: string[];
    skills: string[];
    confidence: number;
  } | null;
};

export default function ApplyPage() {
  const router = useRouter();
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [target, setTarget] = useState<EvidenceTarget | null>(null);
  const [candidateProfile, setCandidateProfile] = useState<CandidateProfile | null>(null);
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
          setCandidateProfile(await fetchCandidateProfile(data.session));
        } catch {
          setCandidateProfile(null);
        }
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
                cvDraft: saved.cvDraft && typeof saved.cvDraft === 'object'
                  ? {
                      title: typeof saved.cvDraft.title === 'string' ? saved.cvDraft.title : '',
                      situation: typeof saved.cvDraft.situation === 'string' ? saved.cvDraft.situation : '',
                      task: typeof saved.cvDraft.task === 'string' ? saved.cvDraft.task : '',
                      actions: Array.isArray(saved.cvDraft.actions) ? saved.cvDraft.actions.filter((item): item is string => typeof item === 'string') : [],
                      skills: Array.isArray(saved.cvDraft.skills) ? saved.cvDraft.skills.filter((item): item is string => typeof item === 'string') : [],
                      confidence: typeof saved.cvDraft.confidence === 'number' ? saved.cvDraft.confidence : 55,
                    }
                  : null,
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

  const cvPrefill: EvidenceCard | null = target?.cvDraft
    ? {
        id: 'cv-prefill',
        title: target.cvDraft.title || 'CV experience',
        situation: target.cvDraft.situation,
        task: target.cvDraft.task,
        actions: target.cvDraft.actions,
        outcome: '',
        reflection: '',
        tags: [],
        behaviours: [],
        skills: target.cvDraft.skills,
        authority_context: null,
        confidence: target.cvDraft.confidence,
      }
    : null;

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
          <p className="text-gray-600 mt-3">Capture reusable proof from any role or sector. JobSleuth matches the same evidence to different vacancies without inventing experience.</p>
        </div>
        {(error || bank.recordError) && <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-amber-800">{error || bank.recordError}</div>}

        {session && (
          <CandidateProfilePanel
            session={session}
            profile={candidateProfile}
            onProfileChange={setCandidateProfile}
          />
        )}

        {target && !bank.editing && (
          <section className="rounded-2xl border border-brand-200 bg-brand-50 p-5">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div className="max-w-3xl">
                <p className="text-xs font-semibold uppercase tracking-wide text-brand-700">Strengthen this vacancy match</p>
                <h2 className="mt-2 text-xl font-bold text-gray-900">{target.requirement}</h2>
                <p className="mt-2 text-sm text-gray-700">
                  {target.cvDraft
                    ? 'JobSleuth has prefilled grounded facts from your CV. Review them carefully, then add the context, your personal responsibility, outcome and learning before saving.'
                    : 'Add a real example from your own experience that proves this criterion. Do not copy the vacancy wording or invent details.'}
                </p>
                {target.gaps.length > 0 && (
                  <div className="mt-3">
                    <p className="text-sm font-semibold text-gray-800">Focus on what JobSleuth could not yet prove:</p>
                    <ul className="mt-1 list-disc space-y-1 pl-5 text-sm text-gray-700">
                      {target.gaps.map((gap, index) => <li key={`${gap}-${index}`}>{gap}</li>)}
                    </ul>
                  </div>
                )}
                <div className="mt-4 rounded-xl border border-brand-100 bg-white/70 p-4">
                  <p className="text-sm font-semibold text-gray-900">Use a real example and answer these prompts in the Evidence Card:</p>
                  <ol className="mt-2 list-decimal space-y-1 pl-5 text-sm text-gray-700">
                    <li>What was happening, and why did it matter?</li>
                    <li>What were you personally responsible for?</li>
                    <li>What did you personally do? Include decisions, tools, checks, stakeholders or processes where relevant.</li>
                    <li>What changed because of your actions? Use a concrete result where possible.</li>
                    <li>What did you learn, improve or do differently afterwards?</li>
                  </ol>
                  <p className="mt-2 text-xs text-gray-500">JobSleuth will reuse the verified facts later; you do not need to copy the vacancy wording.</p>
                </div>
              </div>
              <div className="flex gap-2">
                <Link href={target.returnTo || '/apply/vacancy'} className="btn-secondary text-sm">Back to vacancy</Link>
                <button type="button" onClick={dismissTarget} className="text-sm font-semibold text-gray-600 hover:text-gray-900">Dismiss</button>
              </div>
            </div>
          </section>
        )}

        <div className="grid gap-8 lg:grid-cols-[420px_1fr]">
          <RecordForm
            key={bank.editing?.id ?? `new-${bank.records.length}-${target?.requirement ?? 'general'}-${target?.cvDraft ? 'cv' : 'blank'}`}
            initial={bank.editing ?? cvPrefill}
            busy={bank.savingRecord}
            onSave={saveEvidence}
            onCancel={() => {
              bank.setEditing(null);
              if (target?.cvDraft) dismissTarget();
            }}
          />
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
