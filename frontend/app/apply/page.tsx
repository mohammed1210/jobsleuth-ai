'use client';

import { FormEvent, useEffect, useState } from 'react';
import Link from 'next/link';
import type { Session } from '@supabase/supabase-js';

import HeaderClient from '@/components/HeaderClient';
import {
  analyseVacancy,
  createEvidence,
  fetchEvidence,
  type EvidenceCard,
  type Requirement,
  type VacancyAnalysis,
} from '@/lib/applyApi';
import { getSupabaseClient, isSupabaseConfigured } from '@/lib/supabaseClient';

const lines = (value: string) => value.split('\n').map((item) => item.trim()).filter(Boolean);

export default function ApplyPage() {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [evidence, setEvidence] = useState<EvidenceCard[]>([]);
  const [title, setTitle] = useState('');
  const [skills, setSkills] = useState('');
  const [essential, setEssential] = useState('');
  const [desirable, setDesirable] = useState('');
  const [trainable, setTrainable] = useState('');
  const [practical, setPractical] = useState('');
  const [analysis, setAnalysis] = useState<VacancyAnalysis | null>(null);
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
          setEvidence(await fetchEvidence(data.session));
        } catch {
          setError('Evidence Bank is not available yet.');
        }
      }
      setLoading(false);
    };
    run();
  }, []);

  const addEvidence = async (event: FormEvent) => {
    event.preventDefault();
    if (!session || !title.trim()) return;
    setError(null);
    try {
      const card = await createEvidence(session, {
        title: title.trim(),
        skills: skills.split(',').map((item) => item.trim()).filter(Boolean),
        actions: [],
        tags: [],
        behaviours: [],
        confidence: 70,
      });
      setEvidence((current) => [card, ...current]);
      setTitle('');
      setSkills('');
    } catch {
      setError('Could not save evidence.');
    }
  };

  const runAnalysis = async () => {
    if (!session) return;
    const requirements: Requirement[] = [
      ...lines(essential).map((text) => ({ text, category: 'essential' as const })),
      ...lines(desirable).map((text) => ({ text, category: 'desirable' as const })),
      ...lines(trainable).map((text) => ({ text, category: 'trainable' as const })),
    ];
    setError(null);
    try {
      setAnalysis(await analyseVacancy(session, requirements, evidence, lines(practical)));
    } catch {
      setError('Could not analyse this vacancy.');
    }
  };

  if (!loading && !session) {
    return (
      <div className="min-h-screen">
        <HeaderClient />
        <main className="max-w-3xl mx-auto px-6 py-12">
          <div className="card p-10 text-center">
            <h1 className="text-3xl font-bold text-gray-900 mb-3">Sign in to use JobSleuth Apply</h1>
            <p className="text-gray-600 mb-6">Your Evidence Bank is private to your account.</p>
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
          <p className="text-sm font-semibold text-brand-700 mb-2">JobSleuth Apply</p>
          <h1 className="text-4xl font-bold text-gray-900">Evidence first. Recommendation second.</h1>
          <p className="text-gray-600 mt-3">Build reusable evidence, enter the vacancy criteria, and see what is supported, trainable or genuinely missing.</p>
        </div>

        {error && <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-amber-800">{error}</div>}

        <section className="grid lg:grid-cols-2 gap-6">
          <div className="card p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Evidence Bank</h2>
            <form onSubmit={addEvidence} className="space-y-3">
              <input className="w-full rounded-xl border px-4 py-3" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Example: Led a complex operational decision" />
              <input className="w-full rounded-xl border px-4 py-3" value={skills} onChange={(e) => setSkills(e.target.value)} placeholder="Skills, comma separated" />
              <button className="btn-primary" type="submit">Save evidence</button>
            </form>
            <div className="mt-6 space-y-3">
              {evidence.length === 0 ? <p className="text-gray-500">No evidence cards yet.</p> : evidence.map((card) => (
                <div key={card.id} className="rounded-xl border p-4">
                  <p className="font-semibold text-gray-900">{card.title}</p>
                  <p className="text-sm text-gray-600 mt-1">{card.skills.join(' · ') || 'Add skills to improve matching'}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="card p-6 space-y-4">
            <h2 className="text-2xl font-bold text-gray-900">Vacancy criteria</h2>
            <p className="text-sm text-gray-600">Enter one criterion per line.</p>
            <textarea className="w-full rounded-xl border px-4 py-3 min-h-28" value={essential} onChange={(e) => setEssential(e.target.value)} placeholder="Essential criteria" />
            <textarea className="w-full rounded-xl border px-4 py-3 min-h-24" value={desirable} onChange={(e) => setDesirable(e.target.value)} placeholder="Desirable criteria" />
            <textarea className="w-full rounded-xl border px-4 py-3 min-h-20" value={trainable} onChange={(e) => setTrainable(e.target.value)} placeholder="Trainable requirements" />
            <textarea className="w-full rounded-xl border px-4 py-3 min-h-20" value={practical} onChange={(e) => setPractical(e.target.value)} placeholder="Practical concerns, e.g. working pattern" />
            <button type="button" onClick={runAnalysis} className="btn-primary">Analyse vacancy</button>
          </div>
        </section>

        {analysis && (
          <section className="card p-6">
            <div className="flex flex-wrap items-center gap-4 mb-6">
              <h2 className="text-2xl font-bold text-gray-900">Recommendation</h2>
              <span className="rounded-full bg-gray-900 text-white px-4 py-2 font-bold">{analysis.decision}</span>
              <span className="text-sm text-gray-500">{analysis.analysis_provider}</span>
            </div>
            {analysis.practical_fit.status === 'concern' && (
              <div className="mb-5 rounded-xl border border-amber-200 bg-amber-50 p-4">
                <p className="font-semibold text-amber-900">Practical fit needs checking</p>
                {analysis.practical_fit.issues.map((issue) => <p key={issue} className="text-sm text-amber-800 mt-1">{issue}</p>)}
              </div>
            )}
            <div className="space-y-3">
              {analysis.requirements.map((item, index) => (
                <div key={`${item.requirement}-${index}`} className="rounded-xl border p-4">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className="font-semibold text-gray-900">{item.requirement}</p>
                      <p className="text-xs uppercase tracking-wide text-gray-500 mt-1">{item.category}</p>
                    </div>
                    <span className="text-sm font-bold uppercase">{item.status}</span>
                  </div>
                  {item.evidence.length > 0 && <p className="text-sm text-gray-600 mt-3">Evidence: {item.evidence.map((entry) => entry.title).join(', ')}</p>}
                </div>
              ))}
            </div>
          </section>
        )}
      </main>
    </div>
  );
}
