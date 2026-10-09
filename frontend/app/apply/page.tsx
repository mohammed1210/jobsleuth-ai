'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import type { Session } from '@supabase/supabase-js';
import HeaderClient from '@/components/HeaderClient';
import CandidateProfilePanel from '@/components/profile/CandidateProfilePanel';
import RecordForm from '@/components/RecordForm';
import EvidenceCardView from '@/components/evidence/EvidenceCardView';
import EvidenceImportPanel from '@/components/evidence/EvidenceImportPanel';
import { fetchCandidateProfile, type CandidateProfile } from '@/lib/candidateProfileApi';
import type { EvidenceCard } from '@/lib/applyApi';
import type { EvidenceImportSuggestion } from '@/lib/evidenceImportApi';
import { getSupabaseClient, isSupabaseConfigured } from '@/lib/supabaseClient';
import { removeRecord } from '@/lib/removeRecord';
import { useRecords } from '@/lib/useRecords';

const EVIDENCE_TARGET_KEY = 'jobsleuth.evidence.target.v1';
const EVIDENCE_REANALYSE_KEY = 'jobsleuth.evidence.reanalyse.v1';

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
  const [manualEntry, setManualEntry] = useState(false);
  const [importDraft, setImportDraft] = useState<EvidenceImportSuggestion | null>(null);
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
    const payload = importDraft && !bank.editing
      ? { ...input, source: 'statement_import', confidence: input.confidence ?? importDraft.confidence }
      : input;
    const saved = await bank.saveRecord(payload);
    if (!saved) return;

    if (importDraft) {
      setImportDraft(null);
      setManualEntry(false);
    }

    if (!target) return;
    window.sessionStorage.setItem(
      EVIDENCE_REANALYSE_KEY,
      JSON.stringify({
        userId: target.userId,
        requirement: target.requirement,
        createdAt: new Date().toISOString(),
      }),
    );
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

  const importPrefill: EvidenceCard | null = importDraft
    ? {
        id: 'statement-import-prefill',
        title: importDraft.title,
        situation: importDraft.situation,
        task: importDraft.task,
        actions: importDraft.actions,
        outcome: importDraft.outcome,
        reflection: importDraft.reflection,
        tags: importDraft.tags,
        behaviours: importDraft.behaviours,
        skills: importDraft.skills,
        authority_context: importDraft.authority_context ?? null,
        source: 'statement_import',
        confidence: importDraft.confidence,
      }
    : null;

  const cvPrefill: EvidenceCard | null = target?.cvDraft
    ? {
        id: 'cv-prefill',
        title: target.cvDraft.title || 'CV experience',
        situation: '',
        task: '',
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

        {session && !target?.cvDraft && (
          <CandidateProfilePanel
            session={session}
            profile={candidateProfile}
            onProfileChange={setCandidateProfile}
          />
        )}

        {session && !target && (
          <EvidenceImportPanel
            session={session}
            onReview={(draft) => {
              bank.setEditing(null);
              setManualEntry(false);
              setImportDraft(draft);
            }}
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
                    ? 'JobSleuth has prefilled only grounded CV facts that are relevant to this criterion. Add the real situation, your personal responsibility, outcome and learning before saving.'
                    : 'Add a real example from your own experience that proves this criterion. Do not copy the vacancy wording or invent details.'}
                </p>
                {target.cvDraft && (
                  <div className="mt-3 rounded-xl border border-brand-100 bg-white/80 p-4 text-sm text-gray-700">
                    <p className="font-semibold text-gray-900">CV source</p>
                    <p className="mt-1">{target.cvDraft.title}</p>
                    {target.cvDraft.situation && <p className="mt-1 text-gray-500">{target.cvDraft.situation}</p>}
                    {target.cvDraft.actions.length > 0 && (
                      <div className="mt-3">
                        <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">Relevant CV highlights prefilled below</p>
                        <ul className="mt-1 list-disc space-y-1 pl-5">
                          {target.cvDraft.actions.map((action, index) => <li key={`${action}-${index}`}>{action}</li>)}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
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

        {!target && !bank.editing && !manualEntry && !importDraft && (
          <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border bg-white p-5">
            <div>
              <p className="font-semibold text-gray-900">Prefer to add one yourself?</p>
              <p className="mt-1 text-sm text-gray-600">Manual entry is still available, but you only need it when you do not already have the example written elsewhere.</p>
            </div>
            <button type="button" className="btn-secondary" onClick={() => setManualEntry(true)}>Add an example manually</button>
          </div>
        )}

        {importDraft && (
          <section className="mx-auto max-w-3xl rounded-2xl border border-brand-200 bg-brand-50 p-5">
            <p className="text-xs font-semibold uppercase tracking-wide text-brand-700">Review imported evidence</p>
            <h2 className="mt-1 text-xl font-bold text-gray-900">{importDraft.title}</h2>
            <p className="mt-1 text-sm text-gray-600">Check JobSleuth's extraction against the original wording before saving it as verified evidence.</p>
            {importDraft.source_excerpt && (
              <blockquote className="mt-4 rounded-xl border bg-white p-4 text-sm leading-6 text-gray-700">
                {importDraft.source_excerpt}
              </blockquote>
            )}
            <p className="mt-2 text-xs text-gray-500">Source: {importDraft.source_filename}</p>
          </section>
        )}

        {(target || bank.editing || manualEntry || importDraft) && (
          <div className={(target?.cvDraft || importDraft) ? 'mx-auto max-w-3xl' : 'grid gap-8 lg:grid-cols-[420px_1fr]'}>
            <RecordForm
              key={bank.editing?.id ?? importDraft?.title ?? `new-${bank.records.length}-${target?.requirement ?? 'general'}-${target?.cvDraft ? 'cv' : 'blank'}`}
              initial={bank.editing ?? importPrefill ?? cvPrefill}
              busy={bank.savingRecord}
              onSave={saveEvidence}
              onCancel={() => {
                bank.setEditing(null);
                setImportDraft(null);
                setManualEntry(false);
                if (target?.cvDraft) dismissTarget();
              }}
            />
            {!target?.cvDraft && !importDraft && (
              <div className="space-y-4">
                {bank.loadingRecords && <div className="card p-8 text-center text-gray-600">Loading…</div>}
                {!bank.loadingRecords && bank.records.length === 0 && <div className="card p-8 text-center text-gray-600">No saved examples yet.</div>}
                {bank.records.map((card) => (
                  <EvidenceCardView
                    key={card.id}
                    card={card}
                    onEdit={(selected) => {
                      setManualEntry(false);
                      setImportDraft(null);
                      bank.setEditing(selected);
                    }}
                    onRemove={() => remove(card.id)}
                  />
                ))}
              </div>
            )}
          </div>
        )}

        {!target && !manualEntry && !importDraft && !bank.editing && (
          <section className="space-y-4">
            <div>
              <h2 className="text-xl font-bold text-gray-900">Saved evidence</h2>
              <p className="mt-1 text-sm text-gray-600">Reusable examples JobSleuth can match to future vacancies.</p>
            </div>
            {bank.loadingRecords && <div className="card p-8 text-center text-gray-600">Loading…</div>}
            {!bank.loadingRecords && bank.records.length === 0 && <div className="card p-8 text-center text-gray-600">No saved examples yet. Import a past application above to get started quickly.</div>}
            {bank.records.map((card) => (
              <EvidenceCardView
                key={card.id}
                card={card}
                onEdit={(selected) => {
                  setManualEntry(false);
                  setImportDraft(null);
                  bank.setEditing(selected);
                }}
                onRemove={() => remove(card.id)}
              />
            ))}
          </section>
        )}
      </main>
    </div>
  );
}
