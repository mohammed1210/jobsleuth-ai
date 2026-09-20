'use client';

import { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import type { Session } from '@supabase/supabase-js';

import ApplicationDraftPanel from '@/components/application/ApplicationDraftPanel';
import HeaderClient from '@/components/HeaderClient';
import ExtractionAudit from '@/components/vacancy/ExtractionAudit';
import RequirementMatchCard from '@/components/vacancy/RequirementMatchCard';
import { analyseVacancy, fetchEvidence, type EvidenceCard, type Requirement, type VacancyAnalysis } from '@/lib/applyApi';
import { getFreshSession, getSupabaseClient, isSupabaseConfigured } from '@/lib/supabaseClient';
import { extractVacancyIntelligence, type IntelligenceItem } from '@/lib/vacancyIntelligenceApi';
import { parseVacancyText } from '@/lib/vacancyParser';

const lines = (value: string) => value.split('\n').map((item) => item.trim()).filter(Boolean);
const VACANCY_DRAFT_KEY = 'jobsleuth.apply.vacancyDraft.v2';
const EVIDENCE_TARGET_KEY = 'jobsleuth.evidence.target.v1';

const evidenceFingerprint = (cards: EvidenceCard[]) => JSON.stringify(cards);
const analysisInputFingerprint = (essential: string, desirable: string, trainable: string, practical: string) => JSON.stringify({
  essential: lines(essential),
  desirable: lines(desirable),
  trainable: lines(trainable),
  practical: lines(practical),
});

type VacancyDraftState = {
  userId: string;
  vacancyText: string;
  eligibility: string;
  essential: string;
  desirable: string;
  trainable: string;
  practical: string;
  extractedItems: IntelligenceItem[];
  extractionProvider: string | null;
  analysis: VacancyAnalysis | null;
  analysisEvidenceFingerprint: string | null;
  analysisInputFingerprint: string | null;
};

export default function VacancyApplyPage() {
  const router = useRouter();
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
  const [analysing, setAnalysing] = useState(false);
  const [analysis, setAnalysis] = useState<VacancyAnalysis | null>(null);
  const [analysisEvidenceFingerprint, setAnalysisEvidenceFingerprint] = useState<string | null>(null);
  const [analysisInputFingerprintValue, setAnalysisInputFingerprintValue] = useState<string | null>(null);
  const [analysisValidated, setAnalysisValidated] = useState(false);
  const sessionUserIdRef = useRef<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [draftStateReady, setDraftStateReady] = useState(false);

  const clearDraftFields = () => {
    setVacancyText('');
    setEligibility('');
    setEssential('');
    setDesirable('');
    setTrainable('');
    setPractical('');
    setExtractedItems([]);
    setExtractionProvider(null);
    setAnalysis(null);
    setAnalysisEvidenceFingerprint(null);
    setAnalysisInputFingerprintValue(null);
    setAnalysisValidated(false);
  };

  const restoreDraftForUser = (userId: string) => {
    try {
      const raw = window.sessionStorage.getItem(VACANCY_DRAFT_KEY);
      if (!raw) return;
      const saved = JSON.parse(raw) as Partial<VacancyDraftState>;
      if (saved.userId !== userId) {
        window.sessionStorage.removeItem(VACANCY_DRAFT_KEY);
        clearDraftFields();
        return;
      }
      if (typeof saved.vacancyText === 'string') setVacancyText(saved.vacancyText);
      if (typeof saved.eligibility === 'string') setEligibility(saved.eligibility);
      if (typeof saved.essential === 'string') setEssential(saved.essential);
      if (typeof saved.desirable === 'string') setDesirable(saved.desirable);
      if (typeof saved.trainable === 'string') setTrainable(saved.trainable);
      if (typeof saved.practical === 'string') setPractical(saved.practical);
      if (Array.isArray(saved.extractedItems)) setExtractedItems(saved.extractedItems);
      if (typeof saved.extractionProvider === 'string' || saved.extractionProvider === null) {
        setExtractionProvider(saved.extractionProvider ?? null);
      }
      if (saved.analysis && typeof saved.analysis === 'object') {
        setAnalysis(saved.analysis as VacancyAnalysis);
        setAnalysisEvidenceFingerprint(
          typeof saved.analysisEvidenceFingerprint === 'string' ? saved.analysisEvidenceFingerprint : null,
        );
        setAnalysisInputFingerprintValue(
          typeof saved.analysisInputFingerprint === 'string' ? saved.analysisInputFingerprint : null,
        );
        setAnalysisValidated(false);
      }
    } catch {
      window.sessionStorage.removeItem(VACANCY_DRAFT_KEY);
      clearDraftFields();
    }
  };

  useEffect(() => {
    if (!draftStateReady || !session) return;
    const snapshot: VacancyDraftState = {
      userId: session.user.id,
      vacancyText,
      eligibility,
      essential,
      desirable,
      trainable,
      practical,
      extractedItems,
      extractionProvider,
      analysis,
      analysisEvidenceFingerprint,
      analysisInputFingerprint: analysisInputFingerprintValue,
    };
    const hasWork = vacancyText.trim() || eligibility.trim() || essential.trim() || desirable.trim() || trainable.trim() || practical.trim() || extractedItems.length > 0 || analysis;
    if (!hasWork) {
      window.sessionStorage.removeItem(VACANCY_DRAFT_KEY);
      return;
    }
    window.sessionStorage.setItem(VACANCY_DRAFT_KEY, JSON.stringify(snapshot));
  }, [draftStateReady, session, vacancyText, eligibility, essential, desirable, trainable, practical, extractedItems, extractionProvider, analysis, analysisEvidenceFingerprint, analysisInputFingerprintValue]);

  useEffect(() => {
    if (!isSupabaseConfigured()) {
      setMessage('Supabase is not configured yet.');
      setLoading(false);
      setDraftStateReady(true);
      return;
    }

    const supabase = getSupabaseClient();
    let active = true;

    const loadEvidenceForSession = async (nextSession: Session) => {
      const requestedUserId = nextSession.user.id;
      try {
        const nextEvidence = await fetchEvidence(nextSession);
        if (!active || sessionUserIdRef.current !== requestedUserId) return;

        setEvidence(nextEvidence);

        try {
          const raw = window.sessionStorage.getItem(VACANCY_DRAFT_KEY);
          if (raw) {
            const saved = JSON.parse(raw) as Partial<VacancyDraftState>;
            if (saved.userId === requestedUserId && saved.analysis) {
              const savedInputsFingerprint = analysisInputFingerprint(
                typeof saved.essential === 'string' ? saved.essential : '',
                typeof saved.desirable === 'string' ? saved.desirable : '',
                typeof saved.trainable === 'string' ? saved.trainable : '',
                typeof saved.practical === 'string' ? saved.practical : '',
              );
              const evidenceStillMatches = saved.analysisEvidenceFingerprint === evidenceFingerprint(nextEvidence);
              const inputsStillMatch = saved.analysisInputFingerprint === savedInputsFingerprint;
              if (!evidenceStillMatches || !inputsStillMatch) {
                setAnalysis(null);
                setAnalysisEvidenceFingerprint(null);
                setAnalysisInputFingerprintValue(null);
                setAnalysisValidated(false);
              } else {
                setAnalysisValidated(true);
              }
            } else {
              setAnalysisValidated(false);
            }
          }
        } catch {
          setAnalysis(null);
          setAnalysisEvidenceFingerprint(null);
        }
      } catch (error) {
        if (active && sessionUserIdRef.current === requestedUserId) {
          setEvidence([]);
          setAnalysis(null);
          setAnalysisEvidenceFingerprint(null);
          setAnalysisInputFingerprintValue(null);
          setAnalysisValidated(false);
          setMessage(error instanceof Error ? error.message : 'Could not load your Evidence Bank.');
        }
      }
    };

    const load = async () => {
      const current = await getFreshSession();
      if (!active) return;
      sessionUserIdRef.current = current?.user.id ?? null;
      setSession(current);
      if (current) {
        restoreDraftForUser(current.user.id);
        await loadEvidenceForSession(current);
      } else {
        window.sessionStorage.removeItem(VACANCY_DRAFT_KEY);
        clearDraftFields();
        setEvidence([]);
      }
      if (!active) return;
      setDraftStateReady(true);
      setLoading(false);
    };

    void load();

    const { data: authListener } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      if (!active) return;
      sessionUserIdRef.current = nextSession?.user.id ?? null;
      setSession(nextSession);
      setDraftStateReady(false);

      if (!nextSession) {
        window.sessionStorage.removeItem(VACANCY_DRAFT_KEY);
        clearDraftFields();
        setEvidence([]);
        setDraftStateReady(true);
        return;
      }

      try {
        const raw = window.sessionStorage.getItem(VACANCY_DRAFT_KEY);
        if (raw) {
          const saved = JSON.parse(raw) as Partial<VacancyDraftState>;
          if (saved.userId !== nextSession.user.id) {
            window.sessionStorage.removeItem(VACANCY_DRAFT_KEY);
            clearDraftFields();
          } else {
            restoreDraftForUser(nextSession.user.id);
          }
        } else {
          clearDraftFields();
        }
      } catch {
        window.sessionStorage.removeItem(VACANCY_DRAFT_KEY);
        clearDraftFields();
      }

      setEvidence([]);
      void loadEvidenceForSession(nextSession);
      setDraftStateReady(true);
    });

    return () => {
      active = false;
      authListener.subscription.unsubscribe();
    };
  }, []);

  const currentSession = async () => {
    const fresh = await getFreshSession();
    sessionUserIdRef.current = fresh?.user.id ?? null;
    setSession(fresh);
    if (!fresh) setMessage('Your session has expired. Sign in again to continue.');
    return fresh;
  };

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
    const activeSession = await currentSession();
    if (!activeSession) return;
    if (vacancyText.trim().length < 40) {
      setMessage('Paste more of the vacancy advert before extracting.');
      return;
    }

    setExtracting(true);
    setAnalysis(null);
    setAnalysisEvidenceFingerprint(null);
    setAnalysisInputFingerprintValue(null);
    setAnalysisValidated(false);
    setMessage(null);
    try {
      const result = await extractVacancyIntelligence(activeSession, vacancyText);
      if (sessionUserIdRef.current !== activeSession.user.id) return;
      const items = [...result.eligibility, ...result.requirements, ...result.practical];
      applyRequirements(items);
      setExtractedItems(items);
      setExtractionProvider(result.provider);
      const lowConfidence = result.summary.low_confidence ? ` ${result.summary.low_confidence} item(s) need extra review.` : '';
      setMessage(`Extracted ${result.summary.items} grounded item(s). Review and edit before analysing.${lowConfidence}`);
    } catch {
      if (sessionUserIdRef.current !== activeSession.user.id) return;
      const count = localFallback();
      setMessage(count ? `The intelligence service was unavailable, so JobSleuth used the local fallback and found ${count} item(s). Review carefully.` : 'No clear criteria found. Edit the fields manually below.');
    } finally {
      setExtracting(false);
    }
  };

  const strengthenEvidence = (item: import('@/lib/applyApi').RequirementAnalysis) => {
    if (!session) return;
    const target = {
      userId: session.user.id,
      requirement: item.requirement,
      category: item.category,
      matchStrength: item.match_strength,
      gaps: Array.isArray(item.gaps) ? item.gaps.filter(Boolean) : [],
      returnTo: '/apply/vacancy',
      createdAt: new Date().toISOString(),
    };
    window.sessionStorage.setItem(EVIDENCE_TARGET_KEY, JSON.stringify(target));
    router.push('/apply');
  };

  const analyse = async () => {
    const activeSession = await currentSession();
    if (!activeSession) return;

    const requirements: Requirement[] = [
      ...lines(essential).map((text) => ({ text, category: 'essential' as const })),
      ...lines(desirable).map((text) => ({ text, category: 'desirable' as const })),
      ...lines(trainable).map((text) => ({ text, category: 'trainable' as const })),
    ];
    if (!requirements.length) {
      setMessage('No vacancy criteria are available to analyse. Extract or enter criteria first.');
      return;
    }

    setAnalysing(true);
    setAnalysis(null);
    setAnalysisEvidenceFingerprint(null);
    setAnalysisInputFingerprintValue(null);
    setAnalysisValidated(false);
    setMessage('Analysing your evidence against the vacancy…');
    try {
      const result = await analyseVacancy(activeSession, requirements, evidence, lines(practical));
      if (sessionUserIdRef.current !== activeSession.user.id) return;
      setAnalysis(result);
      setAnalysisEvidenceFingerprint(evidenceFingerprint(evidence));
      setAnalysisInputFingerprintValue(analysisInputFingerprint(essential, desirable, trainable, practical));
      setAnalysisValidated(true);
      setMessage(null);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Vacancy analysis failed.');
    } finally {
      setAnalysing(false);
    }
  };

  useEffect(() => {
    if (!analysis || !analysisInputFingerprintValue) return;
    if (analysisInputFingerprintValue !== analysisInputFingerprint(essential, desirable, trainable, practical)) {
      setAnalysis(null);
      setAnalysisEvidenceFingerprint(null);
      setAnalysisInputFingerprintValue(null);
      setAnalysisValidated(false);
    }
  }, [analysis, analysisInputFingerprintValue, essential, desirable, trainable, practical]);

  if (!loading && !session) {
    return (
      <div className="min-h-screen">
        <HeaderClient />
        <main className="max-w-3xl mx-auto px-6 py-12">
          <div className="card p-10 text-center">
            <h1 className="text-3xl font-bold text-gray-900 mb-3">Sign in to analyse a vacancy</h1>
            <Link href="/login" className="btn-primary inline-flex">Sign in</Link>
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
            <button type="button" onClick={analyse} disabled={analysing} className="btn-primary disabled:cursor-wait disabled:opacity-60">{analysing ? 'Analysing…' : 'Analyse vacancy'}</button>
          </div>
        </section>

        <ExtractionAudit items={extractedItems} provider={extractionProvider} />

        {analysis && analysisValidated && (
          <>
            <section className="card p-6 space-y-5">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div className="flex items-center gap-4">
                  <h2 className="text-2xl font-bold text-gray-900">Recommendation</h2>
                  <span className="rounded-full bg-gray-900 px-4 py-2 font-bold text-white">{analysis.decision}</span>
                </div>
                <span className="text-xs text-gray-500">{analysis.analysis_provider}</span>
              </div>

              {analysis.decision_reasons && analysis.decision_reasons.length > 0 && (
                <div className="rounded-xl bg-gray-50 p-4">
                  <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">Why this recommendation</p>
                  <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-gray-700">
                    {analysis.decision_reasons.map((reason) => <li key={reason}>{reason}</li>)}
                  </ul>
                </div>
              )}

              {analysis.practical_fit.issues.length > 0 && (
                <div className="rounded-xl border border-amber-200 bg-amber-50 p-4">
                  <p className="font-semibold text-amber-900">Practical fit needs checking</p>
                  {analysis.practical_fit.issues.map((issue) => <p key={issue} className="text-sm text-amber-800 mt-1">{issue}</p>)}
                </div>
              )}

              <div className="space-y-3">
                {analysis.requirements.map((item, index) => (
                  <RequirementMatchCard key={`${item.requirement}-${index}`} item={item} onStrengthen={strengthenEvidence} />
                ))}
              </div>
            </section>

            {session && <ApplicationDraftPanel session={session} analysis={analysis} evidence={evidence} vacancyText={vacancyText} />}
          </>
        )}
      </main>
    </div>
  );
}
