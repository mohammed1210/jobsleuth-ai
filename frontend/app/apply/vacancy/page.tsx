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
  const [showManualDetails, setShowManualDetails] = useState(false);

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
    setShowManualDetails(false);
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
      if (!count) setShowManualDetails(true);
      setMessage(count ? `The intelligence service was unavailable, so JobSleuth used the local fallback and found ${count} item(s). Review carefully.` : 'No clear criteria found. Open the vacancy details and enter the criteria manually.');
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

  const hasVacancyDetails = Boolean(
    eligibility.trim() || essential.trim() || desirable.trim() || trainable.trim() || practical.trim() || extractedItems.length,
  );
  const careerCriteriaCount = lines(essential).length + lines(desirable).length + lines(trainable).length;

  return (
    <div className="min-h-screen">
      <HeaderClient />
      <main className="mx-auto max-w-5xl space-y-5 px-6 py-8">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-sm font-semibold text-brand-700">JobSleuth Apply</p>
            <h1 className="mt-1 text-3xl font-bold tracking-tight text-gray-900">Check the fit. Build the application.</h1>
            <p className="mt-2 max-w-2xl text-sm text-gray-600">Paste the vacancy once. JobSleuth turns it into a focused fit check, with deeper evidence available only when you want it.</p>
          </div>
          <Link href="/apply" className="btn-secondary px-4 py-2 text-sm">Evidence Bank</Link>
        </div>

        {message && <div className="rounded-xl border bg-white px-4 py-3 text-sm text-gray-700 shadow-sm">{message}</div>}

        <section className="card p-6">
          <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-gray-400">Step 1</p>
              <h2 className="mt-1 text-xl font-bold text-gray-900">Vacancy</h2>
              <p className="mt-1 text-sm text-gray-500">Paste the full advert so requirements, practical constraints and application instructions stay grounded in the source.</p>
            </div>
            {hasVacancyDetails && (
              <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700">Vacancy structured</span>
            )}
          </div>

          <textarea
            className={`w-full rounded-xl border px-4 py-3 leading-6 transition-all ${hasVacancyDetails ? 'min-h-36' : 'min-h-56'}`}
            value={vacancyText}
            onChange={(e) => setVacancyText(e.target.value)}
            placeholder="Paste the full vacancy advert here"
          />

          <div className="mt-4 flex flex-wrap items-center gap-3">
            <button type="button" onClick={extract} disabled={extracting} className="btn-primary disabled:opacity-60">
              {extracting ? 'Extracting…' : hasVacancyDetails ? 'Re-extract vacancy' : 'Extract vacancy'}
            </button>
            {!hasVacancyDetails && (
              <button type="button" onClick={() => setShowManualDetails((current) => !current)} className="btn-ghost text-sm">
                Enter criteria manually
              </button>
            )}
          </div>
        </section>

        {(hasVacancyDetails || showManualDetails) && (
          <section className="card p-6">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-gray-400">Step 2</p>
                <h2 className="mt-1 text-xl font-bold text-gray-900">Vacancy snapshot</h2>
                <p className="mt-1 text-sm text-gray-500">The essentials stay visible. Editing and audit detail are tucked away until you need them.</p>
              </div>
              <button type="button" onClick={analyse} disabled={analysing} className="btn-primary disabled:cursor-wait disabled:opacity-60">
                {analysing ? 'Analysing…' : 'Analyse my fit'}
              </button>
            </div>

            <div className="mt-5 grid gap-3 sm:grid-cols-3">
              <div className="rounded-xl bg-gray-50 px-4 py-3">
                <p className="text-2xl font-bold text-gray-900">{careerCriteriaCount}</p>
                <p className="text-xs font-medium uppercase tracking-wide text-gray-500">Career criteria</p>
              </div>
              <div className="rounded-xl bg-gray-50 px-4 py-3">
                <p className="text-2xl font-bold text-gray-900">{lines(eligibility).length}</p>
                <p className="text-xs font-medium uppercase tracking-wide text-gray-500">Eligibility checks</p>
              </div>
              <div className="rounded-xl bg-gray-50 px-4 py-3">
                <p className="text-2xl font-bold text-gray-900">{lines(practical).length}</p>
                <p className="text-xs font-medium uppercase tracking-wide text-gray-500">Practical points</p>
              </div>
            </div>

            <details className="mt-5 rounded-xl border bg-white">
              <summary className="cursor-pointer list-none px-4 py-3 text-sm font-semibold text-gray-800">
                Review or edit extracted vacancy details
                <span className="ml-2 text-xs font-normal text-gray-500">Optional</span>
              </summary>
              <div className="border-t p-4">
                <div className="grid gap-5 md:grid-cols-2">
                  <div className="space-y-4">
                    <label className="block text-sm font-semibold text-gray-800">
                      Essential criteria
                      <textarea className="mt-2 min-h-32 w-full rounded-xl border px-4 py-3 font-normal" value={essential} onChange={(e) => setEssential(e.target.value)} placeholder="Essential criteria" />
                    </label>
                    <label className="block text-sm font-semibold text-gray-800">
                      Desirable criteria
                      <textarea className="mt-2 min-h-24 w-full rounded-xl border px-4 py-3 font-normal" value={desirable} onChange={(e) => setDesirable(e.target.value)} placeholder="Desirable criteria" />
                    </label>
                    <label className="block text-sm font-semibold text-gray-800">
                      Trainable requirements
                      <textarea className="mt-2 min-h-20 w-full rounded-xl border px-4 py-3 font-normal" value={trainable} onChange={(e) => setTrainable(e.target.value)} placeholder="Trainable requirements" />
                    </label>
                  </div>
                  <div className="space-y-4">
                    <label className="block text-sm font-semibold text-gray-800">
                      Eligibility
                      <textarea className="mt-2 min-h-24 w-full rounded-xl border px-4 py-3 font-normal" value={eligibility} onChange={(e) => setEligibility(e.target.value)} placeholder="Right to work, clearance, mandatory licences or other eligibility requirements" />
                    </label>
                    <label className="block text-sm font-semibold text-gray-800">
                      Practical fit
                      <textarea className="mt-2 min-h-32 w-full rounded-xl border px-4 py-3 font-normal" value={practical} onChange={(e) => setPractical(e.target.value)} placeholder="Working pattern, travel, location, training or other practical constraints" />
                    </label>
                    <p className="text-sm text-gray-500">{evidence.length} Evidence Bank {evidence.length === 1 ? 'card' : 'cards'} available for matching.</p>
                  </div>
                </div>
              </div>
            </details>
          </section>
        )}

        <ExtractionAudit items={extractedItems} provider={extractionProvider} />

        {analysis && analysisValidated && (
          <>
            <section className="card p-6">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.16em] text-gray-400">Step 3</p>
                  <h2 className="mt-1 text-xl font-bold text-gray-900">Fit summary</h2>
                </div>
                <span className="rounded-full bg-gray-900 px-4 py-2 text-sm font-bold text-white">{analysis.decision}</span>
              </div>

              <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-5">
                {([
                  ['Strong', analysis.requirements.filter((item) => item.match_strength === 'strong').length],
                  ['Partial', analysis.requirements.filter((item) => item.match_strength === 'partial').length],
                  ['Weak', analysis.requirements.filter((item) => item.match_strength === 'weak').length],
                  ['Missing', analysis.requirements.filter((item) => item.match_strength === 'missing').length],
                  ['Trainable', analysis.requirements.filter((item) => item.match_strength === 'trainable').length],
                ] as const).map(([label, count]) => (
                  <div key={label} className="rounded-xl bg-gray-50 px-4 py-3">
                    <p className="text-xl font-bold text-gray-900">{count}</p>
                    <p className="text-xs font-medium uppercase tracking-wide text-gray-500">{label}</p>
                  </div>
                ))}
              </div>

              {analysis.decision_reasons && analysis.decision_reasons.length > 0 && (
                <div className="mt-5 rounded-xl bg-gray-50 p-4">
                  <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">Why</p>
                  <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-gray-700">
                    {analysis.decision_reasons.map((reason) => <li key={reason}>{reason}</li>)}
                  </ul>
                </div>
              )}

              {analysis.practical_fit.issues.length > 0 && (
                <div className="mt-4 rounded-xl border border-amber-200 bg-amber-50 p-4">
                  <p className="font-semibold text-amber-900">Practical fit needs checking</p>
                  <p className="mt-1 text-sm text-amber-800">{analysis.practical_fit.issues.length} point{analysis.practical_fit.issues.length === 1 ? '' : 's'} to review before applying.</p>
                  <details className="mt-2">
                    <summary className="cursor-pointer text-sm font-semibold text-amber-900">Show practical points</summary>
                    <div className="mt-2 space-y-1">
                      {analysis.practical_fit.issues.map((issue) => <p key={issue} className="text-sm text-amber-800">{issue}</p>)}
                    </div>
                  </details>
                </div>
              )}

              <div className="mt-5">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <h3 className="font-semibold text-gray-900">Criteria match</h3>
                    <p className="text-sm text-gray-500">Scan the result, then expand only the criteria you want to inspect.</p>
                  </div>
                  <span className="text-xs text-gray-400">{analysis.analysis_provider}</span>
                </div>
                <div className="space-y-2">
                  {analysis.requirements.map((item, index) => (
                    <RequirementMatchCard key={`${item.requirement}-${index}`} item={item} onStrengthen={strengthenEvidence} />
                  ))}
                </div>
              </div>
            </section>

            {session && <ApplicationDraftPanel session={session} analysis={analysis} evidence={evidence} vacancyText={vacancyText} />}
          </>
        )}
      </main>
    </div>
  );
}
