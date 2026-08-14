'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import type { Session } from '@supabase/supabase-js';

import HeaderClient from '@/components/HeaderClient';
import ExtractionAudit from '@/components/vacancy/ExtractionAudit';
import { analyseVacancy, fetchEvidence, type EvidenceCard, type Requirement, type VacancyAnalysis } from '@/lib/applyApi';
import { getSupabaseClient, isSupabaseConfigured } from '@/lib/supabaseClient';
import { extractVacancyIntelligence, type IntelligenceItem } from '@/lib/vacancyIntelligenceApi';
import { parseVacancyText } from '@/lib/vacancyParser';

const lines = (value: string) => value.split('\n').map((item) => item.trim()).filter(Boolean);

export default function VacancyApplyPage() {
  const [session, setSession] = useState<Session | null>(null);
  const [evidence, setEvidence] = useState<EvidenceCard[]>([]);
  const [vacancyText, setVacancyText] = useState('');
  const [eligibility, setEligibility] = useState('');
  const [essential, setEssential] = useState('');
  const [desirable, setDesirable] = useState('');
  const [trainable, setTrainable] = useState('');
  const [practical, setPractical] = useState('');
  const [extractedItems, setExtractedItems] = useState<IntelligenceItem[]>([]);
  const [extractionProvider, setExtractionProvider] = useState<string | null>(null);
  const [extracting, setExtracting] = useState(false);
  const [analysis, setAnalysis] = useState<VacancyAnalysis | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const run = async () => {
      if (!isSupabaseConfigured()) {
        setMessage('Supabase is not configured yet.');
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
          setMessage('Could not load your Evidence Bank.');
        }
      }
      setLoading(false);
    };
    run();
  }, []);

  const applyRequirements = (items: IntelligenceItem[]) => {
    const list = (category: Requirement['category']) => items
      .filter((item) => item.category === category)
      .map((item) => item.text)
      .join('\n');
    setEligibility(items.filter((item) => item.category === 'eligibility').map((item) => item.text).join('\n'));
    setEssential(list('essential'));
    setDesirable(list('desirable'));
    setTrainable(list('trainable'));
    setPractical(items.filter((item) => item.category === 'practical').map((item) => item.text).join('\n'));
  };

  const localFallback = () => {
    const parsed = parseVacancyText(vacancyText);
    const items: IntelligenceItem[] = [
      ...parsed.requirements.map((item) => ({
        text: item.text,
        category: item.category,
        source_text: item.text,
        confidence: 0.55,
        explicit_blocker: false,
      })),
      ...parsed.practicalIssues.map((text) => ({
        text,
        category: 'practical' as const,
        source_text: text,
        confidence: 0.55,
        explicit_blocker: false,
      })),
    ];
    applyRequirements(items);
    setExtractedItems(items);
    setExtractionProvider('local-parser-fallback');
    return items.length;
  };

  const extract = async () => {
    if (!session) return;
    if (vacancyText.trim().length < 40) {
      setMessage('Paste more of the vacancy advert before extracting.');
      return;
    }

    setExtracting(true);
    setAnalysis(null);
    setMessage(null);
    try {
      const result = await extractVacancyIntelligence(session, vacancyText);
      const items = [...result.eligibility, ...result.requirements, ...result.practical];
      applyRequirements(items);
      setExtractedItems(items);
      setExtractionProvider(result.provider);
      const lowConfidence = result.summary.low_confidence ? ` ${result.summary.low_confidence} item(s) need extra review.` : '';
      setMessage(`Extracted ${result.summary.items} grounded item(s). Review and edit before analysing.${lowConfidence}`);
    } catch {
      const count = localFallback();
      setMessage(count ? `The intelligence service was unavailable, so JobSleuth used the local fallback and found ${count} item(s). Review carefully.` : 'No clear criteria found. Edit the fields manually below.');
    } finally {
      setExtracting(false);
    }
  };

  const analyse = async () => {
    if (!session) return;
    const requirements: Requirement[] = [
      ...lines(essential).map((text) => ({ text, category: 'essential' as const })),
      ...lines(desirable).map((text) => ({ text, category: 'desirable' as const })),
      ...lines(trainable).map((text) => ({ text, category: 'trainable' as const })),
    ];
    try {
      setAnalysis(await analyseVacancy(session, requirements, evidence, lines(practical)));
      setMessage(null);
    } catch {
      setMessage('Vacancy analysis failed.');
    }
  };

  if (!loading && !session) {
    return (
      <div className="min-h-screen">
        <HeaderClient />
        <main className="max-w-3xl mx-auto px-6 py-12">
          <div className="card p-10 text-center">
            <h1 className="text-3xl font-bold text-gray-900 mb-3">Sign in to analyse a vacancy</h1>
            <Link href="/magic-login" className="btn-primary inline-flex">Sign in</Link>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <HeaderClient />
      <main className="max-w-5xl mx-auto px-6 py-10 space-y-6">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="text-sm font-semibold text-brand-700 mb-2">JobSleuth Apply</p>
            <h1 className="text-4xl font-bold text-gray-900">Paste a vacancy. Test the fit.</h1>
            <p className="text-gray-600 mt-2">JobSleuth grounds extracted requirements in the advert. You stay in control and can edit everything before analysis.</p>
          </div>
          <Link href="/apply" className="btn-secondary">Manage Evidence Bank</Link>
        </div>

        {message && <div className="rounded-xl border bg-white px-4 py-3 text-sm text-gray-700">{message}</div>}

        <section className="card p-6 space-y-4">
          <textarea className="w-full min-h-56 rounded-xl border px-4 py-3" value={vacancyText} onChange={(e) => setVacancyText(e.target.value)} placeholder="Paste the full vacancy advert here" />
          <button type="button" onClick={extract} disabled={extracting} className="btn-primary disabled:opacity-60">{extracting ? 'Extracting…' : 'Extract vacancy intelligence'}</button>
        </section>

        <section className="card p-5 space-y-3">
          <div>
            <h2 className="text-xl font-bold text-gray-900">Eligibility checks</h2>
            <p className="mt-1 text-sm text-gray-500">Check these yourself. JobSleuth does not treat eligibility as experience evidence.</p>
          </div>
          <textarea className="w-full min-h-24 rounded-xl border px-4 py-3" value={eligibility} onChange={(e) => setEligibility(e.target.value)} placeholder="Right to work, clearance, mandatory licences or other eligibility requirements" />
        </section>

        <section className="grid md:grid-cols-2 gap-5">
          <div className="card p-5 space-y-3">
            <h2 className="text-xl font-bold text-gray-900">Career fit</h2>
            <textarea className="w-full min-h-32 rounded-xl border px-4 py-3" value={essential} onChange={(e) => setEssential(e.target.value)} placeholder="Essential criteria" />
            <textarea className="w-full min-h-28 rounded-xl border px-4 py-3" value={desirable} onChange={(e) => setDesirable(e.target.value)} placeholder="Desirable criteria" />
            <textarea className="w-full min-h-24 rounded-xl border px-4 py-3" value={trainable} onChange={(e) => setTrainable(e.target.value)} placeholder="Trainable requirements" />
          </div>
          <div className="card p-5 space-y-3">
            <h2 className="text-xl font-bold text-gray-900">Practical fit</h2>
            <textarea className="w-full min-h-40 rounded-xl border px-4 py-3" value={practical} onChange={(e) => setPractical(e.target.value)} placeholder="Working pattern, travel, location, training or other practical constraints" />
            <p className="text-sm text-gray-500">{evidence.length} Evidence Bank {evidence.length === 1 ? 'card' : 'cards'} available for matching.</p>
            <button type="button" onClick={analyse} className="btn-primary">Analyse vacancy</button>
          </div>
        </section>

        <ExtractionAudit items={extractedItems} provider={extractionProvider} />

        {analysis && (
          <section className="card p-6 space-y-5">
            <div className="flex items-center gap-4">
              <h2 className="text-2xl font-bold text-gray-900">Recommendation</h2>
              <span className="rounded-full bg-gray-900 px-4 py-2 font-bold text-white">{analysis.decision}</span>
            </div>
            {analysis.practical_fit.issues.length > 0 && (
              <div className="rounded-xl border border-amber-200 bg-amber-50 p-4">
                <p className="font-semibold text-amber-900">Practical fit needs checking</p>
                {analysis.practical_fit.issues.map((issue) => <p key={issue} className="text-sm text-amber-800 mt-1">{issue}</p>)}
              </div>
            )}
            <div className="space-y-3">
              {analysis.requirements.map((item, index) => (
                <div key={`${item.requirement}-${index}`} className="rounded-xl border p-4">
                  <div className="flex justify-between gap-4">
                    <div>
                      <p className="font-semibold text-gray-900">{item.requirement}</p>
                      <p className="text-xs uppercase tracking-wide text-gray-500 mt-1">{item.category}</p>
                    </div>
                    <span className="text-sm font-bold uppercase">{item.status}</span>
                  </div>
                  {item.evidence.length > 0 && <p className="mt-2 text-sm text-gray-600">Evidence: {item.evidence.map((entry) => entry.title).join(', ')}</p>}
                </div>
              ))}
            </div>
          </section>
        )}
      </main>
    </div>
  );
}
