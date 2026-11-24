'use client';

import { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { fetchJobDetail, type Job } from '@/lib/api';
import { advertForApplication, signInPathForJob } from '@/lib/jobApplicationHandoff';
import type { Session } from '@supabase/supabase-js';

import ApplicationDraftPanel from '@/components/application/ApplicationDraftPanel';
import HeaderClient from '@/components/HeaderClient';
import ExtractionAudit from '@/components/vacancy/ExtractionAudit';
import RequirementMatchCard from '@/components/vacancy/RequirementMatchCard';
import { analyseVacancy, fetchEvidence, type EvidenceCard, type Requirement, type VacancyAnalysis } from '@/lib/applyApi';
import { fetchCandidateProfile, type CandidateProfile } from '@/lib/candidateProfileApi';
import { getFreshSession, getSupabaseClient, isSupabaseConfigured } from '@/lib/supabaseClient';
import { extractVacancyIntelligence, type IntelligenceItem } from '@/lib/vacancyIntelligenceApi';
import { parseVacancyText } from '@/lib/vacancyParser';
import { createExtractionGate } from '@/lib/extractionGate';
import { APPLY_STAGES, canOpenApplyStage, hasUnresolvedJobSwitch, isImportedAdvertEditor, needsApplyStageDowngrade, resumeApplyStage, unansweredMandatoryQuestions, type ApplyStage } from '@/lib/guidedApply';

const lines = (value: string) => value.split('\n').map((item) => item.trim()).filter(Boolean);
const VACANCY_DRAFT_KEY = 'jobsleuth.apply.vacancyDraft.v2';
const EVIDENCE_TARGET_KEY = 'jobsleuth.evidence.target.v1';
const EVIDENCE_REANALYSE_KEY = 'jobsleuth.evidence.reanalyse.v1';
const ANALYSIS_SCHEMA_VERSION = 3;

const evidenceFingerprint = (cards: EvidenceCard[]) => JSON.stringify(cards);
const candidateProfileFingerprint = (profile: CandidateProfile | null) => JSON.stringify(profile ? { summary: profile.summary, skills: profile.skills, experience: profile.experience, qualifications: profile.qualifications, updated_at: profile.updated_at } : null);
type EligibilityAnswer = 'yes' | 'no' | 'unsure';

const analysisInputFingerprint = (
  eligibility: string,
  eligibilityAnswers: Record<string, EligibilityAnswer>,
  essential: string,
  desirable: string,
  trainable: string,
  practical: string,
) => JSON.stringify({
  eligibility: lines(eligibility),
  eligibilityAnswers,
  essential: lines(essential),
  desirable: lines(desirable),
  trainable: lines(trainable),
  practical: lines(practical),
});

type VacancyDraftState = {
  userId: string;
  /** Identifies the imported job even after its text is edited or restored. */
  linkedSourceJobId: number | null;
  needsReExtraction: boolean;
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
  analysisProfileFingerprint: string | null;
  eligibilityAnswers: Record<string, EligibilityAnswer>;
  analysisSchemaVersion: number;
};

export default function VacancyApplyPage() {
  const router = useRouter();
  const [session, setSession] = useState<Session | null>(null);
  const [evidence, setEvidence] = useState<EvidenceCard[]>([]);
  const [candidateProfile, setCandidateProfile] = useState<CandidateProfile | null>(null);
  const [candidateProfileLoaded, setCandidateProfileLoaded] = useState(false);
  const [vacancyText, setVacancyText] = useState('');
  const [eligibility, setEligibility] = useState('');
  const [eligibilityAnswers, setEligibilityAnswers] = useState<Record<string, EligibilityAnswer>>({});
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
  const [analysisProfileFingerprintValue, setAnalysisProfileFingerprintValue] = useState<string | null>(null);
  const [analysisValidated, setAnalysisValidated] = useState(false);
  const sessionUserIdRef = useRef<string | null>(null);
  const extractionGenerationRef = useRef(createExtractionGate());
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [draftStateReady, setDraftStateReady] = useState(false);
  const [showManualDetails, setShowManualDetails] = useState(false);
  const [requestedJobId, setRequestedJobId] = useState<number | null>(null);
  const [sourceJob, setSourceJob] = useState<Job | null>(null);
  const [sourceJobError, setSourceJobError] = useState<string | null>(null);
  const [loadingSourceJob, setLoadingSourceJob] = useState(false);
  const [sourceJobLoadedIntoDraft, setSourceJobLoadedIntoDraft] = useState(false);
  const [linkedSourceJobId, setLinkedSourceJobId] = useState<number | null>(null);
  const [needsReExtraction, setNeedsReExtraction] = useState(false);
  // Display state only: source evidence, eligibility and drafts are preserved
  // independently of which customer-facing step is visible.
  const [activeStage, setActiveStage] = useState<ApplyStage>(1);
  const [builderVisited, setBuilderVisited] = useState(false);
  const [continueExistingDraft, setContinueExistingDraft] = useState(false);
  const stageRestoreRef = useRef(false);

  // A public job ID is carried in the URL, not arbitrary advert text or an
  // external redirect. Always load the official record from our backend.
  useEffect(() => {
    const requested = new URLSearchParams(window.location.search).get('job');
    if (requested === null) return;
    if (!/^[1-9][0-9]{0,14}$/.test(requested)) {
      setSourceJobError('Invalid vacancy link. Return to Jobs and choose a listing.');
      return;
    }
    const id = Number(requested);
    if (!Number.isSafeInteger(id)) {
      setSourceJobError('Invalid vacancy link.');
      return;
    }
    let active = true;
    setRequestedJobId(id);
    setLoadingSourceJob(true);
    void fetchJobDetail(id).then((job) => {
      if (!active) return;
      if (!job) {
        setSourceJobError('The selected vacancy is no longer available. Please choose another.');
      } else {
        setSourceJob(job);
      }
    }).catch(() => {
      if (active) setSourceJobError('Could not load this vacancy. Try again from the Jobs page.');
    }).finally(() => {
      if (active) setLoadingSourceJob(false);
    });
    return () => { active = false; };
  }, []);

  const clearDraftFields = () => {
    setActiveStage(1);
    setBuilderVisited(false);
    setContinueExistingDraft(false);
    // Discard any in-flight response for a previous vacancy or user.
    extractionGenerationRef.current.invalidate();
    setExtracting(false);
    setVacancyText('');
    setEligibility('');
    setEligibilityAnswers({});
    setEssential('');
    setDesirable('');
    setTrainable('');
    setPractical('');
    setExtractedItems([]);
    setExtractionProvider(null);
    setAnalysis(null);
    setAnalysisEvidenceFingerprint(null);
    setAnalysisInputFingerprintValue(null);
    setAnalysisProfileFingerprintValue(null);
    setAnalysisValidated(false);
    setShowManualDetails(false);
    setSourceJobLoadedIntoDraft(false);
    setLinkedSourceJobId(null);
    setNeedsReExtraction(false);
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
      setLinkedSourceJobId(Number.isSafeInteger(saved.linkedSourceJobId) && (saved.linkedSourceJobId ?? 0) > 0 ? saved.linkedSourceJobId! : null);
      setNeedsReExtraction(saved.needsReExtraction === true);
      if (typeof saved.eligibility === 'string') setEligibility(saved.eligibility);
      if (saved.eligibilityAnswers && typeof saved.eligibilityAnswers === 'object') {
        setEligibilityAnswers(saved.eligibilityAnswers as Record<string, EligibilityAnswer>);
      }
      if (typeof saved.essential === 'string') setEssential(saved.essential);
      if (typeof saved.desirable === 'string') setDesirable(saved.desirable);
      if (typeof saved.trainable === 'string') setTrainable(saved.trainable);
      if (typeof saved.practical === 'string') setPractical(saved.practical);
      if (Array.isArray(saved.extractedItems)) setExtractedItems(saved.extractedItems);
      if (typeof saved.extractionProvider === 'string' || saved.extractionProvider === null) {
        setExtractionProvider(saved.extractionProvider ?? null);
      }
      if (
        saved.analysis
        && typeof saved.analysis === 'object'
        && saved.analysisSchemaVersion === ANALYSIS_SCHEMA_VERSION
      ) {
        setAnalysis(saved.analysis as VacancyAnalysis);
        setAnalysisEvidenceFingerprint(
          typeof saved.analysisEvidenceFingerprint === 'string' ? saved.analysisEvidenceFingerprint : null,
        );
        setAnalysisInputFingerprintValue(
          typeof saved.analysisInputFingerprint === 'string' ? saved.analysisInputFingerprint : null,
        );
        setAnalysisProfileFingerprintValue(
          typeof saved.analysisProfileFingerprint === 'string' ? saved.analysisProfileFingerprint : null,
        );
        setAnalysisValidated(false);
      } else if (saved.analysis) {
        setAnalysis(null);
        setAnalysisEvidenceFingerprint(null);
        setAnalysisInputFingerprintValue(null);
        setAnalysisProfileFingerprintValue(null);
        setAnalysisValidated(false);
      }
    } catch {
      window.sessionStorage.removeItem(VACANCY_DRAFT_KEY);
      clearDraftFields();
    }
  };

  // Once the current user's existing draft has been restored, prefill only
  // a genuinely empty workspace. Never silently overwrite saved work.
  useEffect(() => {
    if (!sourceJob || !session || !draftStateReady || sourceJobLoadedIntoDraft) return;
    const hasExistingWork = Boolean(
      vacancyText.trim() || eligibility.trim() || essential.trim() || desirable.trim()
      || trainable.trim() || practical.trim() || extractedItems.length || analysis
    );
    if (!hasExistingWork) {
      setVacancyText(advertForApplication(sourceJob));
      setSourceJobLoadedIntoDraft(true);
      setLinkedSourceJobId(sourceJob.id);
      setNeedsReExtraction(false);
    }
  }, [sourceJob, session, draftStateReady, sourceJobLoadedIntoDraft,
      vacancyText, eligibility, essential, desirable, trainable, practical, extractedItems, analysis]);

  const replaceDraftWithSourceJob = () => {
    if (!sourceJob) return;
    clearDraftFields();
    setVacancyText(advertForApplication(sourceJob));
    setSourceJobLoadedIntoDraft(true);
    setLinkedSourceJobId(sourceJob.id);
    setNeedsReExtraction(false);
    setMessage(null);
  };

  useEffect(() => {
    if (!draftStateReady || !session) return;
    const snapshot: VacancyDraftState = {
      userId: session.user.id,
      linkedSourceJobId,
      needsReExtraction,
      vacancyText,
      eligibility,
      eligibilityAnswers,
      essential,
      desirable,
      trainable,
      practical,
      extractedItems,
      extractionProvider,
      analysis,
      analysisEvidenceFingerprint,
      analysisInputFingerprint: analysisInputFingerprintValue,
      analysisProfileFingerprint: analysisProfileFingerprintValue,
      analysisSchemaVersion: ANALYSIS_SCHEMA_VERSION,
    };
    const hasWork = vacancyText.trim() || eligibility.trim() || essential.trim() || desirable.trim() || trainable.trim() || practical.trim() || extractedItems.length > 0 || analysis;
    if (!hasWork) {
      window.sessionStorage.removeItem(VACANCY_DRAFT_KEY);
      return;
    }
    window.sessionStorage.setItem(VACANCY_DRAFT_KEY, JSON.stringify(snapshot));
  }, [draftStateReady, session, vacancyText, eligibility, eligibilityAnswers, essential, desirable, trainable, practical, extractedItems, extractionProvider, analysis, analysisEvidenceFingerprint, analysisInputFingerprintValue, analysisProfileFingerprintValue, linkedSourceJobId, needsReExtraction]);

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
      setCandidateProfileLoaded(false);

      let nextEvidence: EvidenceCard[];
      try {
        nextEvidence = await fetchEvidence(nextSession);
      } catch (error) {
        if (active && sessionUserIdRef.current === requestedUserId) {
          setEvidence([]);
          setCandidateProfile(null);
          setCandidateProfileLoaded(true);
          setAnalysis(null);
          setAnalysisEvidenceFingerprint(null);
          setAnalysisInputFingerprintValue(null);
          setAnalysisProfileFingerprintValue(null);
          setAnalysisValidated(false);
          setMessage(error instanceof Error ? error.message : 'Could not load your Evidence Bank.');
        }
        return;
      }

      let nextProfile: CandidateProfile | null = null;
      let profileAvailable = true;
      try {
        nextProfile = await fetchCandidateProfile(nextSession);
      } catch {
        profileAvailable = false;
      }

      if (!active || sessionUserIdRef.current !== requestedUserId) return;

      setEvidence(nextEvidence);
      setCandidateProfile(nextProfile);
      if (!profileAvailable) {
        setMessage('Evidence Bank loaded, but your CV profile could not be loaded. Vacancy matching will continue without CV signals.');
      }

      try {
        const raw = window.sessionStorage.getItem(VACANCY_DRAFT_KEY);
        if (raw) {
          const saved = JSON.parse(raw) as Partial<VacancyDraftState>;
          if (saved.userId === requestedUserId && saved.analysis) {
            const savedInputsFingerprint = analysisInputFingerprint(
              typeof saved.eligibility === 'string' ? saved.eligibility : '',
              saved.eligibilityAnswers && typeof saved.eligibilityAnswers === 'object'
                ? saved.eligibilityAnswers as Record<string, EligibilityAnswer>
                : {},
              typeof saved.essential === 'string' ? saved.essential : '',
              typeof saved.desirable === 'string' ? saved.desirable : '',
              typeof saved.trainable === 'string' ? saved.trainable : '',
              typeof saved.practical === 'string' ? saved.practical : '',
            );
            const evidenceStillMatches = saved.analysisEvidenceFingerprint === evidenceFingerprint(nextEvidence);
            const inputsStillMatch = saved.analysisInputFingerprint === savedInputsFingerprint;
            const profileStillMatches = profileAvailable
              && saved.analysisProfileFingerprint === candidateProfileFingerprint(nextProfile);
            if (!evidenceStillMatches || !inputsStillMatch || !profileStillMatches) {
              setAnalysis(null);
              setAnalysisEvidenceFingerprint(null);
              setAnalysisInputFingerprintValue(null);
              setAnalysisProfileFingerprintValue(null);
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
        setAnalysisValidated(false);
      }
      // Only mark profile/evidence hydration complete after any saved
      // assessment has been revalidated against those same records.
      setCandidateProfileLoaded(true);
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
        setCandidateProfile(null);
        setCandidateProfileLoaded(true);
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
      setCandidateProfileLoaded(false);

      if (!nextSession) {
        window.sessionStorage.removeItem(VACANCY_DRAFT_KEY);
        clearDraftFields();
        setEvidence([]);
        setCandidateProfile(null);
        setCandidateProfileLoaded(true);
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
    setEligibilityAnswers({});
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
    const generation = extractionGenerationRef.current.begin();
    const activeSession = await currentSession();
    if (!activeSession || !extractionGenerationRef.current.isCurrent(generation)) return;
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
      if (!extractionGenerationRef.current.isCurrent(generation) ||
          sessionUserIdRef.current !== activeSession.user.id) return;
      const items = [...result.eligibility, ...result.requirements, ...result.practical];
      applyRequirements(items);
      setExtractedItems(items);
      setExtractionProvider(result.provider);
      setNeedsReExtraction(false);
      if (items.length) setActiveStage(2);
      const lowConfidence = result.summary.low_confidence ? ` ${result.summary.low_confidence} requirement(s) may need checking against the original advert.` : '';
      if (!result.summary.requirements && !result.summary.eligibility) {
        setMessage('We could not find enough information about what the employer requires. Open the original advert or add the person specification before continuing.');
      } else {
        setMessage(`We found ${result.summary.items} potential requirements in the advert. Check the mandatory questions below before continuing.${lowConfidence}`);
      }
    } catch {
      if (!extractionGenerationRef.current.isCurrent(generation) ||
          sessionUserIdRef.current !== activeSession.user.id) return;
      const count = localFallback();
      if (!count) setShowManualDetails(true);
      setNeedsReExtraction(false);
      if (count) setActiveStage(2);
      setMessage(count ? `We could not complete the usual advert check. We found ${count} possible requirements; confirm these against the employer’s advert before continuing.` : 'We could not identify the requirements. Open the original advert and add them manually before checking your match.');
    } finally {
      if (extractionGenerationRef.current.isCurrent(generation)) setExtracting(false);
    }
  };

  const strengthenEvidence = (
    item: import('@/lib/applyApi').RequirementAnalysis,
    useCvSignal = false,
  ) => {
    if (!session) return;
    const source = useCvSignal ? item.profile_support?.source : undefined;
    const target = {
      userId: session.user.id,
      requirement: item.requirement,
      category: item.category,
      matchStrength: item.match_strength,
      gaps: Array.isArray(item.gaps) ? item.gaps.filter(Boolean) : [],
      returnTo: '/apply/vacancy',
      createdAt: new Date().toISOString(),
      cvDraft: source
        ? {
            title: source.title,
            situation: source.situation,
            task: source.task,
            actions: source.actions,
            skills: source.skills,
            confidence: 55,
          }
        : null,
    };
    window.sessionStorage.setItem(EVIDENCE_TARGET_KEY, JSON.stringify(target));
    router.push('/apply');
  };

  const analyse = async () => {
    if (needsReExtraction) {
      setMessage('The advert was edited. Return to Your job and read the updated advert before checking your match.');
      return false;
    }
    if (unansweredMandatoryQuestions(lines(eligibility), eligibilityAnswers).length > 0) {
      setMessage('Please choose Yes, No or Not sure for every mandatory requirement first.');
      return false;
    }
    const activeSession = await currentSession();
    if (!activeSession) return;

    const requirements: Requirement[] = [
      ...lines(eligibility).map((text) => ({
        text,
        category: 'eligibility' as const,
        blocker: true,
        eligibility_answer: eligibilityAnswers[text] ?? 'unsure',
      })),
      ...lines(essential).map((text) => ({ text, category: 'essential' as const })),
      ...lines(desirable).map((text) => ({ text, category: 'desirable' as const })),
      ...lines(trainable).map((text) => ({ text, category: 'trainable' as const })),
    ];
    if (!requirements.length) {
      setMessage('No vacancy criteria are available to analyse. Extract or enter criteria first.');
      return false;
    }

    setAnalysing(true);
    setAnalysis(null);
    setAnalysisEvidenceFingerprint(null);
    setAnalysisInputFingerprintValue(null);
    setAnalysisProfileFingerprintValue(null);
    setAnalysisValidated(false);
    setMessage('Analysing your evidence and CV profile against the vacancy…');
    try {
      const result = await analyseVacancy(activeSession, requirements, evidence, lines(practical), candidateProfile);
      if (sessionUserIdRef.current !== activeSession.user.id) return;
      setAnalysis(result);
      setAnalysisEvidenceFingerprint(evidenceFingerprint(evidence));
      setAnalysisInputFingerprintValue(analysisInputFingerprint(eligibility, eligibilityAnswers, essential, desirable, trainable, practical));
      setAnalysisProfileFingerprintValue(candidateProfileFingerprint(candidateProfile));
      setAnalysisValidated(true);
      setActiveStage(3);
      setMessage(null);
      return true;
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Vacancy analysis failed.');
      return false;
    } finally {
      setAnalysing(false);
    }
  };

  useEffect(() => {
    if (!session || !draftStateReady || !candidateProfileLoaded || analysing) return;

    let pending: { userId?: string; requirement?: string } | null = null;
    try {
      const raw = window.sessionStorage.getItem(EVIDENCE_REANALYSE_KEY);
      if (!raw) return;
      pending = JSON.parse(raw) as { userId?: string; requirement?: string };
    } catch {
      window.sessionStorage.removeItem(EVIDENCE_REANALYSE_KEY);
      return;
    }

    if (pending?.userId !== session.user.id) {
      window.sessionStorage.removeItem(EVIDENCE_REANALYSE_KEY);
      return;
    }

    window.sessionStorage.removeItem(EVIDENCE_REANALYSE_KEY);
    const requirement = pending.requirement || 'the strengthened criterion';
    setMessage(`Evidence saved. Re-analysing your fit for “${requirement}”…`);

    void (async () => {
      const ok = await analyse();
      if (ok) {
        setMessage(`Evidence saved and fit re-analysed for “${requirement}”.`);
      }
    })();
  }, [session, draftStateReady, candidateProfileLoaded, analysing, evidence, candidateProfile, eligibility, eligibilityAnswers, essential, desirable, trainable, practical]);

  useEffect(() => {
    if (!analysis || !analysisInputFingerprintValue) return;
    if (analysisInputFingerprintValue !== analysisInputFingerprint(eligibility, eligibilityAnswers, essential, desirable, trainable, practical)) {
      setAnalysis(null);
      setAnalysisEvidenceFingerprint(null);
      setAnalysisInputFingerprintValue(null);
      setAnalysisProfileFingerprintValue(null);
      setAnalysisValidated(false);
    }
  }, [analysis, analysisInputFingerprintValue, eligibility, eligibilityAnswers, essential, desirable, trainable, practical]);

  useEffect(() => {
    if (!analysis || analysisProfileFingerprintValue === null || !candidateProfileLoaded) return;
    if (analysisProfileFingerprintValue !== candidateProfileFingerprint(candidateProfile)) {
      setAnalysis(null);
      setAnalysisEvidenceFingerprint(null);
      setAnalysisInputFingerprintValue(null);
      setAnalysisProfileFingerprintValue(null);
      setAnalysisValidated(false);
    }
  }, [analysis, analysisProfileFingerprintValue, candidateProfile, candidateProfileLoaded]);

  const hasVacancyDetails = Boolean(
    eligibility.trim() || essential.trim() || desirable.trim() || trainable.trim() || practical.trim() || extractedItems.length,
  );
  const careerCriteriaCount = lines(essential).length + lines(desirable).length + lines(trainable).length;
  const hasAnalysableCriteria = careerCriteriaCount + lines(eligibility).length > 0;
  // An imported source is authoritative for the current draft only while
  // its exact text remains in the editor. Manual replacements retire the
  // ownership claim without overwriting or discarding the applicant's work.
  const sourceJobOwnsDraft = Boolean(
    sourceJob && vacancyText.trim() === advertForApplication(sourceJob).trim(),
  );
  // An incoming link may be for job B while sessionStorage contains job A.
  // Do not hide this conflict behind a resumed analysis of the old advert.
  // An intentional edit to an already loaded job is not a new-job conflict.
  const sourceJobImportedToWorkspace = isImportedAdvertEditor({
    sourceJobId: sourceJob?.id ?? null,
    linkedSourceJobId,
    importedThisSession: sourceJobLoadedIntoDraft,
    exactSourceMatch: sourceJobOwnsDraft,
  });
  const sourceJobConflict = hasUnresolvedJobSwitch({
    selectedJobPresent: Boolean(sourceJob),
    exactSourceMatch: sourceJobOwnsDraft,
    importedThisJob: sourceJobImportedToWorkspace,
    hasSavedWork: Boolean(vacancyText.trim() || hasVacancyDetails || analysis),
  });
  const hasCriteriaForGuide = Boolean((hasVacancyDetails || showManualDetails) && !needsReExtraction);
  const hasAnalysisForGuide = Boolean(analysis && analysisValidated && !needsReExtraction);
  const unansweredEligibility = unansweredMandatoryQuestions(lines(eligibility), eligibilityAnswers);
  const guideProgress = { hasCriteria: hasCriteriaForGuide, hasAnalysis: hasAnalysisForGuide };

  const editVacancyText = (nextText: string) => {
    if (nextText === vacancyText) return;
    // Ignore any older extraction completing after a new edit.
    extractionGenerationRef.current.invalidate();
    setExtracting(false);
    // Preserve the origin ID even if the text is edited in the same render.
    if (sourceJob && sourceJobOwnsDraft) setLinkedSourceJobId(sourceJob.id);
    setVacancyText(nextText);
    setNeedsReExtraction(true);
    setMessage('The advert has changed. Read the updated text again before checking your match.');
  };

  const openStage = (stage: ApplyStage) => {
    if (!canOpenApplyStage(stage, guideProgress)) return;
    if (sourceJobConflict && !continueExistingDraft && stage !== 1) return;
    if (stage === 4) setBuilderVisited(true);
    setActiveStage(stage);
  };

  // Restore only after draft and matching state have finished hydration.
  // Do not change the user's step again after their first manual navigation.
  useEffect(() => {
    if (!draftStateReady || loading || !candidateProfileLoaded || stageRestoreRef.current) return;
    stageRestoreRef.current = true;
    setActiveStage(sourceJobConflict && !continueExistingDraft ? 1 : resumeApplyStage(guideProgress));
  }, [draftStateReady, loading, candidateProfileLoaded, hasCriteriaForGuide, hasAnalysisForGuide, sourceJobConflict, continueExistingDraft]);

  useEffect(() => {
    if (!draftStateReady || !candidateProfileLoaded) return;
    if (needsApplyStageDowngrade(activeStage, guideProgress, candidateProfileLoaded)) {
      setActiveStage(hasCriteriaForGuide ? 2 : 1);
    }
  }, [activeStage, hasCriteriaForGuide, hasAnalysisForGuide, draftStateReady, candidateProfileLoaded]);

  useEffect(() => {
    if (!draftStateReady || !candidateProfileLoaded) return;
    if (sourceJobConflict && !continueExistingDraft && activeStage !== 1) {
      setActiveStage(1);
    }
  }, [draftStateReady, candidateProfileLoaded, sourceJobConflict, continueExistingDraft, activeStage]);

  // A long assessment may leave the viewport near the bottom. Bring each
  // new task and its heading into view, including for keyboard users.
  useEffect(() => {
    if (!draftStateReady) return;
    const heading = document.getElementById('guided-apply-stage');
    heading?.focus({ preventScroll: true });
    heading?.scrollIntoView({ block: 'start', behavior: 'auto' });
  }, [activeStage, draftStateReady]);

  if (!loading && !session) {
    return (
      <div className="min-h-screen">
        <HeaderClient />
        <main className="max-w-3xl mx-auto px-6 py-12">
          <div className="card p-10 text-center">
            <h1 className="text-3xl font-bold text-gray-900 mb-3">Sign in to analyse a vacancy</h1>
            <Link href={requestedJobId ? signInPathForJob(requestedJobId) : '/login'}
              className="btn-primary inline-flex">Sign in and continue</Link>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <HeaderClient />
      <main className="mx-auto max-w-5xl space-y-5 px-6 py-8">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-sm font-semibold text-brand-700">JobSleuth Apply</p>
            <h1 className="mt-1 text-3xl font-bold tracking-tight text-gray-900">Your job application, made easier.</h1>
            <p className="mt-2 max-w-2xl text-sm text-gray-600">
              We’ll guide you from the job advert to an evidence-backed match, then help you
              prepare an application you can review before visiting the employer.
            </p>
          </div>
          <Link href="/apply" className="btn-secondary px-4 py-2 text-sm">Evidence Bank</Link>
        </div>

        <nav aria-label="Application steps" className="rounded-2xl border border-gray-200 bg-white p-3 shadow-sm">
          <ol className="grid grid-cols-2 gap-2 sm:grid-cols-4">
            {APPLY_STAGES.map((stage) => {
              const available = canOpenApplyStage(stage.id, guideProgress)
                && (stage.id === 1 || !sourceJobConflict || continueExistingDraft);
              const current = stage.id === activeStage;
              return (
                <li key={stage.id}>
                  <button type="button" onClick={() => openStage(stage.id)} disabled={!available}
                    aria-current={current ? 'step' : undefined}
                    className={`flex h-full w-full items-center gap-2 rounded-xl border px-3 py-3 text-left focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-600 ${
                      current ? 'border-brand-400 bg-brand-50 text-brand-900 shadow-sm'
                        : available ? 'border-transparent text-gray-700 hover:bg-gray-50'
                        : 'cursor-not-allowed border-transparent text-gray-400'
                    }`}>
                    <span aria-hidden="true" className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-sm font-bold ${
                      current ? 'bg-brand-700 text-white'
                        : available && stage.id < activeStage ? 'bg-emerald-100 text-emerald-800'
                        : 'bg-gray-100 text-gray-500'
                    }`}>{stage.id}</span>
                    <span className="min-w-0">
                      <span className="block text-sm font-semibold">{stage.label}</span>
                      <span className="block text-xs opacity-75">{stage.hint}</span>
                    </span>
                  </button>
                </li>
              );
            })}
          </ol>
        </nav>
        <div id="guided-apply-stage" tabIndex={-1} className="scroll-mt-24 outline-none">
          <p className="text-sm font-semibold text-brand-700">Step {activeStage} of 4 · {APPLY_STAGES[activeStage - 1].label}</p>
        </div>
        {loadingSourceJob && (
          <p role="status" className="rounded-xl border bg-white p-4 text-sm text-gray-700">
            Loading selected vacancy from JobSleuth…
          </p>
        )}
        {sourceJobError && (
          <div role="alert" className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
            {sourceJobError} <Link href="/jobs" className="underline">Browse jobs</Link>
          </div>
        )}
        {sourceJob && activeStage === 1 && (
          <section className="rounded-xl border border-brand-200 bg-brand-50 px-5 py-4">
            <p className="text-xs font-semibold uppercase tracking-wide text-brand-700">Selected vacancy</p>
            <div className="mt-2 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-lg font-bold text-gray-900">{sourceJob.title}</h2>
                <p className="text-sm text-gray-600">{sourceJob.company} · {sourceJob.location}</p>
              </div>
              {sourceJob.url && (
                <a href={sourceJob.url} target="_blank" rel="noopener noreferrer"
                  className="text-sm font-semibold text-brand-700 underline">
                  Read full original advert
                </a>
              )}
            </div>
            {sourceJobOwnsDraft ? (
              <p role="status" className="mt-3 text-sm font-medium text-emerald-800">
                {hasAnalysableCriteria && !needsReExtraction
                  ? 'We’ve identified the available requirements. Continue to the next step.'
                  : 'We’ve loaded this vacancy. Read or recheck the advert to identify the requirements.'}
              </p>
            ) : sourceJobConflict ? (
              <div role="alert" className="mt-3 rounded-xl border border-amber-300 bg-amber-50 p-4">
                <p className="font-semibold text-amber-950">Which vacancy do you want to work on?</p>
                <p className="mt-1 text-sm text-amber-900">
                  You opened {sourceJob.title}, but your saved draft contains a different advert.
                  We have not overwritten your work or changed its match results.
                </p>
                <div className="mt-3 flex flex-wrap gap-3">
                  <button type="button" onClick={replaceDraftWithSourceJob} disabled={analysing}
                    className="btn-primary px-4 py-2 text-sm disabled:opacity-50">
                    Use {sourceJob.title} and replace saved draft
                  </button>
                  <button type="button" onClick={() => { setContinueExistingDraft(true); setActiveStage(resumeApplyStage(guideProgress)); }}
                    className="btn-secondary px-4 py-2 text-sm">
                    Keep my existing draft instead
                  </button>
                </div>
              </div>
            ) : sourceJobImportedToWorkspace ? (
              <p role="status" className="mt-3 text-sm text-amber-900">
                You edited the imported advert. Check your changes against the employer's original text before continuing.
              </p>
            ) : (
              <p className="mt-3 text-sm text-gray-600">Loading the selected advert without replacing any saved work…</p>
            )}
            <p className="mt-2 text-xs text-gray-600">
              Publisher-supplied data may not contain every application requirement. Check the original listing before submitting.
            </p>
          </section>
        )}

        {sourceJobImportedToWorkspace && activeStage !== 1 && !sourceJobConflict && (
          <div className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-gray-200 bg-white px-5 py-3 text-sm shadow-sm">
            <span className="font-semibold text-gray-800">Working on: {sourceJob?.title} · {sourceJob?.company}</span>
            <button type="button" onClick={() => openStage(1)} className="font-semibold text-brand-700 underline">View vacancy</button>
          </div>
        )}
        {sourceJobConflict && continueExistingDraft && activeStage !== 1 && (
          <div role="status" className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-amber-300 bg-amber-50 px-5 py-3 text-sm text-amber-950">
            <p><strong>Working on your saved application.</strong> The newly selected {sourceJob?.title} vacancy has not replaced it.</p>
            <button type="button" onClick={() => openStage(1)} className="font-semibold underline">Review job choice</button>
          </div>
        )}
        {message && !(activeStage === 2 && hasVacancyDetails && !hasAnalysableCriteria && message.startsWith('We could not find enough information about what the employer requires.')) && (
          <div role="status" className="rounded-xl border bg-white px-4 py-3 text-sm text-gray-700 shadow-sm">{message}</div>
        )}

        {activeStage === 1 && (
        <section className="card p-6">
          <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
            <div>
               <h2 className="mt-1 text-xl font-bold text-gray-900">Start with the job</h2>
              <p className="mt-1 text-sm text-gray-500">{sourceJobImportedToWorkspace ? 'The job advert is loaded. Read it to identify requirements, then continue.' : 'Paste a vacancy advert, or choose a job from the Jobs page.'}</p>
            </div>
            {hasVacancyDetails && !needsReExtraction && (
              <span className={`rounded-full px-3 py-1 text-xs font-semibold ${hasAnalysableCriteria
                ? 'bg-emerald-50 text-emerald-700'
                : 'bg-amber-50 text-amber-800'}`}>
                {hasAnalysableCriteria ? 'Vacancy criteria found' : 'More criteria needed'}
              </span>
            )}
          </div>

          {sourceJobImportedToWorkspace ? (
            <details className="rounded-xl border border-gray-200 bg-gray-50 p-4">
              <summary className="cursor-pointer font-semibold text-gray-800">View or edit the imported advert <span className="font-normal text-gray-500">(optional)</span></summary>
              <textarea className="mt-3 min-h-56 w-full rounded-xl border bg-white px-4 py-3 leading-6"
                value={vacancyText} onChange={(e) => editVacancyText(e.target.value)}
                aria-label="Imported vacancy advert" />
            </details>
          ) : (
            <textarea
              className={`w-full rounded-xl border px-4 py-3 leading-6 transition-all ${hasVacancyDetails ? 'min-h-36' : 'min-h-56'}`}
              value={vacancyText} onChange={(e) => editVacancyText(e.target.value)}
              placeholder="Paste the full vacancy advert here" aria-label="Vacancy advert"
            />
          )}

          <div className="mt-4 flex flex-wrap items-center gap-3">
            {hasAnalysableCriteria && !needsReExtraction && (
              <button type="button" onClick={() => openStage(2)} disabled={extracting} className="btn-primary disabled:opacity-60">Continue to requirements →</button>
            )}
            <button type="button" onClick={extract} disabled={extracting} className={`${hasAnalysableCriteria && !needsReExtraction ? 'btn-secondary' : 'btn-primary'} disabled:opacity-60`}>
              {extracting ? 'Reading the advert…' : needsReExtraction ? 'Read updated advert' : hasVacancyDetails ? 'Recheck job requirements' : 'Read this advert'}
            </button>
            {hasVacancyDetails && !hasAnalysableCriteria && !needsReExtraction && (
              <button type="button" onClick={() => openStage(2)} className="btn-secondary text-sm">Add missing requirements →</button>
            )}
            {needsReExtraction && <p role="status" className="w-full text-sm font-medium text-amber-800">Read the updated advert to refresh the requirements before continuing.</p>}
            {!hasVacancyDetails && (
              <button type="button" onClick={() => { setShowManualDetails(true); setNeedsReExtraction(false); setActiveStage(2); }} className="btn-ghost text-sm">
                Enter criteria manually
              </button>
            )}
          </div>
        </section>
        )}

        {activeStage === 2 && hasVacancyDetails && !hasAnalysableCriteria && (
          <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
            <p role="status" className="font-semibold">We need more information to check your match.</p>
            <p className="mt-1">Recheck the advert, or add the employer’s missing requirements below. We won’t guess what the employer needs.</p>
            <div className="mt-3 flex flex-wrap gap-2">
              <button type="button" onClick={extract} disabled={extracting} className="btn-primary text-sm disabled:opacity-60">{extracting ? 'Rechecking…' : 'Recheck job requirements'}</button>
              <button type="button" onClick={() => openStage(1)} className="btn-secondary text-sm">View or edit advert</button>
            </div>
          </div>
        )}

        {activeStage === 2 && (hasVacancyDetails || showManualDetails) && (
          <section className="card p-6">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                   <h2 className="mt-1 text-xl font-bold text-gray-900">Check the key requirements</h2>
                <p className="mt-1 text-sm text-gray-500">Confirm mandatory qualifications and practical conditions. We’ll compare your experience with the other criteria.</p>
              </div>
             </div>

            <div className="mt-5 flex flex-wrap gap-2 text-sm">
              <span className="rounded-full bg-brand-50 px-3 py-2 font-medium text-brand-800">{careerCriteriaCount} job requirements</span>
              <span className="rounded-full bg-gray-100 px-3 py-2 font-medium text-gray-700">{lines(eligibility).length} mandatory questions</span>
              <span className="rounded-full bg-gray-100 px-3 py-2 font-medium text-gray-700">{lines(practical).length} practical considerations</span>
            </div>

            {lines(eligibility).length > 0 && (
              <div className="mt-5 rounded-xl border border-amber-200 bg-amber-50/60 p-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="font-semibold text-gray-900">Do you meet these mandatory requirements?</p>
                    <p className="mt-1 text-sm text-gray-600">Choose Yes, No or Not sure for each question. We won't assume you have a qualification or clearance.</p>
                  </div>
                  <span className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-amber-800">
                    {lines(eligibility).length - unansweredEligibility.length} / {lines(eligibility).length} answered · {lines(eligibility).filter((item) => eligibilityAnswers[item] === 'yes').length} met
                  </span>
                </div>
                <div className="mt-4 space-y-3">
                  {lines(eligibility).map((item) => (
                    <div key={item} className="rounded-lg bg-white p-3">
                      <p className="text-sm font-medium text-gray-900">{item}</p>
                      <select
                        value={eligibilityAnswers[item] ?? ''}
                        onChange={(event) => setEligibilityAnswers((current) => ({
                          ...current,
                          [item]: event.target.value as EligibilityAnswer,
                        }))}
                        className="mt-2 w-full rounded-lg border px-3 py-2 text-sm sm:max-w-xs"
                      >
                        <option value="" disabled>Choose an answer</option>
                        <option value="yes">Yes — I meet this</option>
                        <option value="no">No — I do not meet this</option>
                        <option value="unsure">Not sure — I need to check</option>
                      </select>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <details className="mt-5 rounded-xl border bg-white" open={!hasAnalysableCriteria || undefined}>
              <summary className="cursor-pointer list-none px-4 py-3 text-sm font-semibold text-gray-800">
                {hasAnalysableCriteria ? 'Review job requirements' : 'Add missing job requirements'}
                <span className="ml-2 text-xs font-normal text-gray-500">{hasAnalysableCriteria ? 'Optional' : 'Needed to continue'}</span>
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
                    <p className="text-sm text-gray-500">
                      {evidence.length} Evidence Bank {evidence.length === 1 ? 'card' : 'cards'} available for matching
                      {candidateProfile ? ` · CV profile active (${candidateProfile.skills.length} skills)` : ' · no CV profile uploaded'}.
                    </p>
                  </div>
                </div>
              </div>
            </details>
            <div className="mt-6 flex flex-col items-start gap-3 border-t border-gray-100 pt-5 sm:flex-row sm:items-center sm:justify-between">
              <button type="button" onClick={() => openStage(1)} className="btn-secondary">← Back to the job</button>
              <div className="flex flex-col items-start gap-2 sm:items-end">
                {unansweredEligibility.length > 0 && (
                  <p role="status" className="text-sm font-medium text-amber-800">
                    Answer {unansweredEligibility.length} mandatory {unansweredEligibility.length === 1 ? 'question' : 'questions'} to continue.
                  </p>
                )}
                <button type="button" onClick={analyse}
                  disabled={analysing || !hasAnalysableCriteria || unansweredEligibility.length > 0}
                  className="btn-primary disabled:cursor-not-allowed disabled:opacity-50">
                  {analysing ? 'Checking your experience…' : 'Show my match →'}
                </button>
              </div>
            </div>
          </section>
        )}

        {activeStage === 2 && extractedItems.length > 0 && (
          <details className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
            <summary className="cursor-pointer font-semibold text-gray-800">How did JobSleuth find these requirements? <span className="font-normal text-gray-500">(advanced)</span></summary>
            <p className="mt-2 text-sm text-gray-600">See the source wording and confidence behind each requirement. You do not need these technical details to continue.</p>
            <div className="mt-3"><ExtractionAudit items={extractedItems} provider={extractionProvider} /></div>
          </details>
        )}

        {analysis && analysisValidated && activeStage === 3 && (
            <section className="card p-6">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                   <h2 className="mt-1 text-xl font-bold text-gray-900">Here's how your experience compares</h2>
                    <p className="mt-1 text-sm text-gray-600">An evidence-based guide, not an employer’s hiring decision.</p>
                </div>
                <span className="rounded-full bg-gray-900 px-4 py-2 text-sm font-bold text-white">{analysis.decision === 'SKIP' ? 'Eligibility concern' : analysis.decision === 'APPLY' ? 'Promising match' : 'Worth reviewing'}</span>
              </div>

              <div className="mt-5 grid gap-3 sm:grid-cols-3">
                {([
                  ['Strong evidence', analysis.requirements.filter((item) => item.category !== 'eligibility' && item.match_strength === 'strong').length],
                  ['Needs review', analysis.requirements.filter((item) => item.category !== 'eligibility' && ['partial', 'weak'].includes(item.match_strength)).length],
                  ['Not evidenced', analysis.requirements.filter((item) => item.category !== 'eligibility' && item.match_strength === 'missing').length],
                ] as const).map(([label, count]) => (
                  <div key={label} className="rounded-xl bg-gray-50 px-4 py-4">
                    <p className="text-2xl font-bold text-gray-900">{count}</p>
                    <p className="text-sm font-medium text-gray-600">{label}</p>
                  </div>
                ))}
              </div>

              {analysis.decision_reasons && analysis.decision_reasons.length > 0 && (
                <div className="mt-5 rounded-xl bg-gray-50 p-4">
                  <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">Why we reached this recommendation</p>
                  <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-gray-700">
                    {analysis.decision_reasons.map((reason) => <li key={reason}>{reason}</li>)}
                  </ul>
                </div>
              )}

              {analysis.requirements.some((item) => item.category === 'eligibility') && (
                <div className="mt-4 rounded-xl border p-4">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="font-semibold text-gray-900">Eligibility</p>
                    <span className="text-xs font-medium text-gray-500">
                      {analysis.requirements.filter((item) => item.category === 'eligibility' && item.status === 'met').length} met · {analysis.requirements.filter((item) => item.category === 'eligibility' && item.status !== 'unconfirmed').length} answered
                    </span>
                  </div>
                  <div className="mt-3 space-y-2">
                    {analysis.requirements.filter((item) => item.category === 'eligibility').map((item) => (
                      <div key={item.requirement} className="flex flex-wrap items-center justify-between gap-3 rounded-lg bg-gray-50 px-3 py-2 text-sm">
                        <span className="text-gray-800">{item.requirement}</span>
                        <span className={
                          item.status === 'met'
                            ? 'font-semibold text-emerald-700'
                            : item.status === 'not-met'
                              ? 'font-semibold text-red-700'
                              : 'font-semibold text-amber-700'
                        }>
                          {item.status === 'met' ? 'Confirmed' : item.status === 'not-met' ? 'Not met' : 'Needs confirmation'}
                        </span>
                      </div>
                    ))}
                  </div>
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

              <div className="mt-5 rounded-xl border border-gray-200 p-4">
                <h3 className="font-semibold text-gray-900">What may need attention</h3>
                <div className="mt-3 space-y-2">
                  {analysis.requirements.filter((item) => item.category === 'essential' && ['missing', 'weak'].includes(item.match_strength)).slice(0,3).map((item) => (
                    <p key={item.requirement} className="rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-900">{item.requirement}</p>
                  ))}
                  {!analysis.requirements.some((item) => item.category === 'essential' && ['missing', 'weak'].includes(item.match_strength)) && (
                    <p className="text-sm text-gray-600">No essential requirements are marked weak or missing, but partial matches still need checking.</p>
                  )}
                </div>
              </div>

              <details className="mt-5 rounded-xl border border-gray-200 bg-white p-4">
                <summary className="cursor-pointer font-semibold text-gray-800">
                  Review all requirements and matched evidence <span className="font-normal text-gray-500">(optional)</span>
                </summary>
                <p className="mt-2 text-sm text-gray-600">Expand an individual requirement to see the supporting evidence and gaps.</p>
                <div className="mt-3 space-y-2">
                  {analysis.requirements.filter((item) => item.category !== 'eligibility').map((item, index) => (
                    <RequirementMatchCard
                      key={`${item.requirement}-${index}`}
                      item={item}
                      onStrengthen={strengthenEvidence}
                      onUseCvSignal={(requirement) => strengthenEvidence(requirement, true)}
                    />
                  ))}
                </div>
              </details>

              <div className="mt-6 flex flex-wrap justify-between gap-3 border-t pt-5">
                <button type="button" onClick={() => openStage(2)} className="btn-secondary">← Review requirements</button>
                <button type="button" onClick={() => openStage(4)} className="btn-primary">
                  {analysis.decision === 'SKIP' ? 'See my next options →' : 'Continue to my application →'}
                </button>
              </div>
            </section>
        )}

        {analysis && analysisValidated && (activeStage === 4 || builderVisited) && (
          <div className={activeStage === 4 ? 'space-y-4' : 'hidden'} aria-hidden={activeStage !== 4}>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <button type="button" onClick={() => openStage(3)} className="btn-secondary">← Back to my match</button>
              <span className="text-sm text-gray-500">{analysis.decision === 'SKIP' ? 'You still have options' : 'Review your draft and the employer’s instructions before applying'}</span>
            </div>
            {analysis.decision === 'SKIP' ? (
              <section className="card p-6">
                 <h2 className="mt-1 text-xl font-bold text-gray-900">A required qualification is missing</h2>
                <p className="mt-2 max-w-2xl text-sm text-gray-600">
                  You marked a mandatory requirement as not met. JobSleuth won't write an application that implies you meet it.
                </p>
                <p className="mt-3 text-sm font-medium text-gray-800">
                  You can change your answer if it was incorrect, read the employer’s advert or explore other vacancies.
                </p>
                <div className="mt-5 flex flex-wrap gap-3">
                  <button type="button" onClick={() => openStage(2)} className="btn-primary">Review my answer</button>
                  <Link href="/jobs" className="btn-secondary">Find another job</Link>
                  {sourceJob?.url && (
                    <a href={sourceJob.url} target="_blank" rel="noopener noreferrer"
                      className="btn-secondary">View employer advert</a>
                  )}
                </div>
              </section>
            ) : (
              session && <ApplicationDraftPanel session={session} analysis={analysis} evidence={evidence} vacancyText={vacancyText} originalAdvertUrl={sourceJobOwnsDraft ? sourceJob?.url : null} />
            )}
          </div>
        )}
      </main>
    </div>
  );
}
