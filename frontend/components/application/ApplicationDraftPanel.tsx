'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import type { Session } from '@supabase/supabase-js';

import type { EvidenceCard, RequirementAnalysis, VacancyAnalysis } from '@/lib/applyApi';
import { buildApplication, type ApplicationDraftResult, type ApplicationType } from '@/lib/applicationBuilderApi';
import { detectApplicationInstructions } from '@/lib/applicationInstructions';
import { savePilotFeedback } from '@/lib/pilotFeedbackApi';
import {
  binaryPilotAnswer,
  EMPTY_PILOT_FEEDBACK,
  isPilotFeedbackComplete,
  type BinaryPilotAnswer,
  type PilotFeedbackDraft,
} from '@/lib/pilotFeedbackForm';

type Props = { session: Session; analysis: VacancyAnalysis; evidence: EvidenceCard[]; vacancyText: string };

const EVIDENCE_TARGET_KEY = 'jobsleuth.evidence.target.v1';

const statusLabel: Record<string, string> = {
  covered: 'Covered',
  'partially-covered': 'Partial',
  'evidence-gap': 'Evidence gap',
  'not-used': 'Not used',
};

const normalise = (value: string) => value.toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();

export default function ApplicationDraftPanel({ session, analysis, evidence, vacancyText }: Props) {
  const instructions = useMemo(() => detectApplicationInstructions(vacancyText), [vacancyText]);
  const [roleTitle, setRoleTitle] = useState('');
  const [organisation, setOrganisation] = useState('');
  const [selectedPartId, setSelectedPartId] = useState('');
  const [applicationType, setApplicationType] = useState<ApplicationType>('statement_of_suitability');
  const [wordLimitInput, setWordLimitInput] = useState('500');
  const [draftAnyway, setDraftAnyway] = useState(false);
  const [result, setResult] = useState<ApplicationDraftResult | null>(null);
  const [draft, setDraft] = useState('');
  const [building, setBuilding] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [pilotFeedback, setPilotFeedback] = useState<PilotFeedbackDraft>(() => ({ ...EMPTY_PILOT_FEEDBACK }));
  const [feedbackSaved, setFeedbackSaved] = useState(false);
  const [savingFeedback, setSavingFeedback] = useState(false);

  const selectedPart = useMemo(
    () => instructions.applicationParts.find((part) => part.id === selectedPartId) ?? instructions.applicationParts[0],
    [instructions.applicationParts, selectedPartId],
  );

  useEffect(() => {
    setRoleTitle(instructions.roleTitle);
    setOrganisation(instructions.organisation);
    const first = instructions.applicationParts[0];
    setSelectedPartId(first?.id ?? '');
    setApplicationType(first?.kind === 'criteria' ? 'criteria_response' : first?.kind === 'cover_letter' ? 'cover_letter' : 'statement_of_suitability');
    setWordLimitInput(String(first?.wordLimit ?? instructions.wordLimit ?? 500));
    setDraftAnyway(false);
    setResult(null);
    setDraft('');
  }, [instructions]);

  useEffect(() => {
    if (!selectedPart) return;
    setApplicationType(
      selectedPart.kind === 'criteria' || selectedPart.kind === 'behaviour'
        ? 'criteria_response'
        : selectedPart.kind === 'cover_letter'
          ? 'cover_letter'
          : 'statement_of_suitability',
    );
    setWordLimitInput(String(selectedPart.wordLimit ?? (selectedPart.kind === 'behaviour' ? 250 : instructions.wordLimit ?? 500)));
    setDraftAnyway(false);
    setResult(null);
    setDraft('');
    setMessage(null);
  }, [selectedPart?.id]);

  const wordLimit = useMemo(() => {
    const parsed = Number(wordLimitInput);
    if (!Number.isFinite(parsed)) return 500;
    return Math.min(5000, Math.max(100, Math.round(parsed)));
  }, [wordLimitInput]);

  const activeRequirements = useMemo<RequirementAnalysis[]>(() => {
    if (selectedPart?.kind !== 'behaviour' || !selectedPart.behaviourName) return analysis.requirements;

    const behaviourKey = normalise(selectedPart.behaviourName);
    const matchedCards = evidence.filter((card) =>
      (card.behaviours || []).some((label) => {
        const key = normalise(label);
        return key === behaviourKey || key.includes(behaviourKey) || behaviourKey.includes(key);
      }),
    );

    return [{
      requirement: `Civil Service behaviour: ${selectedPart.behaviourName}`,
      category: 'essential',
      blocker: false,
      status: matchedCards.length ? 'matched' : 'evidence-gap',
      match_strength: matchedCards.length ? 'strong' : 'missing',
      confidence: matchedCards.length ? 1 : 0.96,
      why: matchedCards.length
        ? 'Evidence Bank examples are explicitly tagged to this behaviour.'
        : 'No Evidence Bank example is explicitly tagged to this behaviour yet.',
      gaps: matchedCards.length ? [] : [`Add a genuine example demonstrating ${selectedPart.behaviourName}.`],
      evidence: matchedCards.map((card) => ({
        id: card.id,
        title: card.title,
        strength: 'strong' as const,
        score: 100,
        confidence: 1,
        why: `Tagged to ${selectedPart.behaviourName}.`,
        gaps: [],
        supporting_facts: [],
        signals: { concepts: [selectedPart.behaviourName], evidence_quality: 1 },
        matched_terms: [selectedPart.behaviourName],
      })),
    }];
  }, [analysis.requirements, evidence, selectedPart]);

  const liveWordCount = useMemo(() => draft.trim() ? draft.trim().split(/\s+/).length : 0, [draft]);

  const readiness = useMemo(() => {
    const essential = activeRequirements.filter((item) => item.category === 'essential');
    const counts = { strong: 0, partial: 0, weak: 0, missing: 0 };
    for (const item of essential) {
      if (item.match_strength === 'strong') counts.strong += 1;
      if (item.match_strength === 'partial') counts.partial += 1;
      if (item.match_strength === 'weak') counts.weak += 1;
      if (item.match_strength === 'missing') counts.missing += 1;
    }
    return {
      total: essential.length,
      ...counts,
      needsStrengthening: counts.partial + counts.weak + counts.missing > 0,
    };
  }, [activeRequirements]);

  const build = async () => {
    if (readiness.needsStrengthening && !draftAnyway) {
      setMessage('Review the evidence-readiness warning first. Strengthen your Evidence Bank or explicitly choose to draft with current evidence.');
      return;
    }
    setBuilding(true); setMessage(null); setFeedbackSaved(false);
    setPilotFeedback({ ...EMPTY_PILOT_FEEDBACK });
    try {
      const next = await buildApplication(session, {
        roleTitle,
        organisation,
        applicationType,
        wordLimit,
        requirements: activeRequirements,
        evidenceCards: evidence,
      });
      setResult(next); setDraft(next.draft);
      if (!next.can_generate) setMessage('JobSleuth did not find enough supported evidence to draft safely. Strengthen the Evidence Bank first.');
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Application Builder could not generate a draft. Please try again.');
    } finally { setBuilding(false); }
  };

  const prepareEvidenceTarget = () => {
    const weakest = activeRequirements.find((item) => item.match_strength !== 'strong' && item.match_strength !== 'trainable')
      ?? activeRequirements[0];
    if (!weakest) return;
    window.sessionStorage.setItem(EVIDENCE_TARGET_KEY, JSON.stringify({
      userId: session.user.id,
      requirement: weakest.requirement,
      category: weakest.category,
      matchStrength: weakest.match_strength,
      gaps: Array.isArray(weakest.gaps) ? weakest.gaps : [],
      returnTo: '/apply/vacancy',
      createdAt: new Date().toISOString(),
    }));
  };

  const copyDraft = async () => {
    if (!draft) return;
    await navigator.clipboard.writeText(draft);
    setMessage('Draft copied to clipboard.');
  };

  const submitFeedback = async () => {
    if (!result) return;
    if (!isPilotFeedbackComplete(pilotFeedback)) {
      setMessage('Please answer every pilot feedback question before saving.');
      return;
    }
    setSavingFeedback(true); setMessage(null);
    try {
      await savePilotFeedback(session, {
        provider: result.provider,
        recommendation: analysis.decision,
        application_type: applicationType,
        word_count: liveWordCount,
        usefulness: pilotFeedback.usefulness as number,
        would_submit: binaryPilotAnswer(pilotFeedback.wouldSubmit),
        recommendation_trust: binaryPilotAnswer(pilotFeedback.recommendationTrust),
        material_time_saving: binaryPilotAnswer(pilotFeedback.materialTimeSaving),
        would_use_again: binaryPilotAnswer(pilotFeedback.wouldUseAgain),
        payment_signal: pilotFeedback.paymentSignal as 'yes' | 'maybe' | 'no',
      });
      setFeedbackSaved(true);
      setMessage('Pilot feedback saved. Thank you — no vacancy, evidence or draft text was stored with this feedback.');
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Could not save pilot feedback.');
    } finally { setSavingFeedback(false); }
  };

  return (
    <section className="card p-6 space-y-5">
      <div>
        <p className="text-sm font-semibold text-brand-700">Application Builder</p>
        <h2 className="mt-1 text-2xl font-bold text-gray-900">Turn matched evidence into supported application components</h2>
        <p className="mt-2 text-sm text-gray-600">JobSleuth keeps separate word limits separate and only drafts from evidence it can support.</p>
      </div>

      <div className="rounded-2xl border bg-gray-50 p-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">Detected application instructions</p>
            <div className="mt-2 flex flex-wrap gap-2">
              {instructions.applicationParts.map((part) => (
                <span key={part.id} className="rounded-full bg-white px-3 py-1 text-sm font-medium text-gray-800">
                  {part.label}{part.wordLimit ? ` · ${part.wordLimit} words` : ''}
                </span>
              ))}
            </div>
          </div>
          {instructions.requiredDocuments.length > 0 && <p className="max-w-xl text-sm text-gray-600">Required: {instructions.requiredDocuments.join(' + ')}</p>}
        </div>
        <p className="mt-2 text-xs text-gray-500">Each detected component keeps its own word budget. CV requirements are shown but are not drafted here.</p>
      </div>

      {instructions.applicationParts.length > 1 && (
        <label className="block text-sm font-medium text-gray-700">
          Application component
          <select value={selectedPart?.id ?? ''} onChange={(e) => setSelectedPartId(e.target.value)} className="mt-1 w-full rounded-xl border px-3 py-2">
            {instructions.applicationParts.map((part) => (
              <option key={part.id} value={part.id}>{part.label}{part.wordLimit ? ` — ${part.wordLimit} words` : ''}</option>
            ))}
          </select>
        </label>
      )}

      {selectedPart?.kind === 'behaviour' && (
        <div className="rounded-xl border border-blue-200 bg-blue-50 p-4 text-sm text-blue-900">
          <strong>Behaviour component:</strong> JobSleuth will only use Evidence Bank examples explicitly tagged <strong>{selectedPart.behaviourName}</strong>.
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        <label className="text-sm font-medium text-gray-700">Role title<input value={roleTitle} onChange={(e) => setRoleTitle(e.target.value)} className="mt-1 w-full rounded-xl border px-3 py-2" placeholder="e.g. Counter Fraud Officer" /></label>
        <label className="text-sm font-medium text-gray-700">Organisation<input value={organisation} onChange={(e) => setOrganisation(e.target.value)} className="mt-1 w-full rounded-xl border px-3 py-2" placeholder="Optional" /></label>
        <label className="text-sm font-medium text-gray-700">Draft format<select value={applicationType} onChange={(e) => setApplicationType(e.target.value as ApplicationType)} className="mt-1 w-full rounded-xl border px-3 py-2"><option value="statement_of_suitability">Personal statement / statement of suitability</option><option value="cover_letter">Cover letter</option><option value="criteria_response">Criteria / behaviour response</option></select></label>
        <label className="text-sm font-medium text-gray-700">Word limit<input inputMode="numeric" value={wordLimitInput} onChange={(e) => setWordLimitInput(e.target.value.replace(/[^0-9]/g, ''))} onBlur={() => setWordLimitInput(String(wordLimit))} className="mt-1 w-full rounded-xl border px-3 py-2" placeholder="e.g. 750" /></label>
      </div>

      {readiness.needsStrengthening ? (
        <div className="rounded-2xl border border-amber-300 bg-amber-50 p-5">
          <h3 className="font-semibold text-amber-950">Evidence needs strengthening before drafting this component</h3>
          <p className="mt-2 text-sm text-amber-900">Of {readiness.total} essential criteria: {readiness.strong} Strong, {readiness.partial} Partial, {readiness.weak} Weak, {readiness.missing} Missing.</p>
          <p className="mt-2 text-sm text-amber-900">A draft can only use evidence JobSleuth can support. Missing or weak criteria stay uncovered rather than being invented.</p>
          <div className="mt-4 flex flex-wrap gap-3">
            <Link href="/apply" onClick={prepareEvidenceTarget} className="btn-secondary">Strengthen Evidence Bank</Link>
            {!draftAnyway ? (
              <button type="button" onClick={() => setDraftAnyway(true)} className="btn-secondary">Draft with current evidence anyway</button>
            ) : (
              <span className="inline-flex items-center rounded-xl border border-amber-300 bg-white px-4 py-2 text-sm font-semibold text-amber-900">Current-evidence drafting enabled</span>
            )}
          </div>
        </div>
      ) : (
        <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-900"><strong>Evidence ready to draft.</strong> All {readiness.total} essential criteria for this component have Strong support.</div>
      )}

      <button type="button" onClick={build} disabled={building || (readiness.needsStrengthening && !draftAnyway)} className="btn-primary disabled:cursor-not-allowed disabled:opacity-50">{building ? 'Building evidence-backed draft…' : `Build ${selectedPart?.label ?? 'application'} draft`}</button>
      {message && <div className="rounded-xl border bg-white px-4 py-3 text-sm text-gray-700">{message}</div>}

      {result && (
        <div className="space-y-5">
          {result.warnings.length > 0 && <div className="rounded-xl border border-amber-200 bg-amber-50 p-4"><p className="font-semibold text-amber-900">Review before submitting</p><ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-amber-900">{result.warnings.map((w) => <li key={w}>{w}</li>)}</ul></div>}

          <div>
            <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
              <div><h3 className="font-semibold text-gray-900">{selectedPart?.label ?? 'Editable'} draft</h3><p className="text-xs text-gray-500">Provider: {result.provider}{result.fallback_reason ? ` · fallback: ${result.fallback_reason}` : ''}</p></div>
              <div className="flex items-center gap-3"><span className="text-sm text-gray-600">{liveWordCount} / {wordLimit} words</span><button type="button" onClick={copyDraft} className="btn-secondary">Copy</button></div>
            </div>
            <textarea value={draft} onChange={(e) => setDraft(e.target.value)} className="min-h-[28rem] w-full rounded-xl border px-4 py-3 leading-7" placeholder="A supported draft will appear here." />
            <p className="mt-2 text-xs text-gray-500">The evidence audit below describes the generated version. Re-check facts after substantial manual edits.</p>
          </div>

          <div><h3 className="font-semibold text-gray-900">Criteria coverage</h3><div className="mt-3 space-y-2">{result.coverage.map((item, index) => <div key={`${item.requirement}-${index}`} className="rounded-xl border p-3"><div className="flex flex-wrap items-start justify-between gap-3"><div><p className="text-sm font-medium text-gray-900">{item.requirement}</p><p className="mt-1 text-xs uppercase tracking-wide text-gray-500">{item.category} · {item.match_strength}</p></div><span className="rounded-full bg-gray-100 px-3 py-1 text-xs font-semibold text-gray-700">{statusLabel[item.status] || item.status}</span></div></div>)}</div></div>

          {result.paragraphs.length > 0 && <div><h3 className="font-semibold text-gray-900">Evidence audit</h3><div className="mt-3 space-y-3">{result.paragraphs.map((paragraph, index) => <details key={`${paragraph.evidence_ids.join('-')}-${index}`} className="rounded-xl border p-4"><summary className="cursor-pointer text-sm font-semibold text-gray-900">Paragraph {index + 1} · {paragraph.grounding_status}</summary><div className="mt-3 space-y-2 text-sm text-gray-600">{paragraph.supporting_facts.map((fact, factIndex) => <div key={`${fact.evidence_id}-${fact.field}-${factIndex}`} className="rounded-lg bg-gray-50 p-3"><p className="text-xs font-semibold uppercase tracking-wide text-gray-500">{fact.field}</p><p className="mt-1">{fact.text}</p></div>)}</div></details>)}</div></div>}

          <div className="rounded-2xl border border-brand-100 bg-brand-50/40 p-5 space-y-4">
            <div><h3 className="font-semibold text-gray-900">Tester feedback</h3><p className="mt-1 text-sm text-gray-600">Help us validate JobSleuth. We store these ratings only — not your vacancy, evidence or draft text.</p></div>
            <label className="block text-sm font-medium text-gray-700">How useful was this result?
              <select
                value={pilotFeedback.usefulness ?? ''}
                onChange={(e) => setPilotFeedback((current) => ({ ...current, usefulness: e.target.value ? Number(e.target.value) : null }))}
                className="mt-1 w-full rounded-xl border px-3 py-2"
              >
                <option value="">Choose 1–10</option>
                {Array.from({ length: 10 }, (_, index) => index + 1).map((score) => <option key={score} value={score}>{score}/10</option>)}
              </select>
            </label>
            <div className="grid gap-3 md:grid-cols-2">
              {([
                ['Would you submit this after review?', 'wouldSubmit', pilotFeedback.wouldSubmit],
                ['Did you trust the Apply/Consider/Skip recommendation?', 'recommendationTrust', pilotFeedback.recommendationTrust],
                ['Did this materially save you time?', 'materialTimeSaving', pilotFeedback.materialTimeSaving],
                ['Would you use JobSleuth for another vacancy?', 'wouldUseAgain', pilotFeedback.wouldUseAgain],
              ] as const).map(([label, field, value]) => (
                <label key={field} className="rounded-xl bg-white p-3 text-sm">
                  <span>{label}</span>
                  <select
                    value={value}
                    onChange={(e) => setPilotFeedback((current) => ({ ...current, [field]: e.target.value as BinaryPilotAnswer }))}
                    className="mt-2 w-full rounded-lg border px-3 py-2"
                  >
                    <option value="">Choose</option>
                    <option value="yes">Yes</option>
                    <option value="no">No</option>
                  </select>
                </label>
              ))}
            </div>
            <label className="block text-sm font-medium text-gray-700">Would you pay for continued access?
              <select
                value={pilotFeedback.paymentSignal}
                onChange={(e) => setPilotFeedback((current) => ({ ...current, paymentSignal: e.target.value as PilotFeedbackDraft['paymentSignal'] }))}
                className="mt-1 w-full rounded-xl border px-3 py-2"
              >
                <option value="">Choose</option>
                <option value="yes">Yes</option>
                <option value="maybe">Maybe</option>
                <option value="no">No</option>
              </select>
            </label>
            <button type="button" disabled={savingFeedback || feedbackSaved || !isPilotFeedbackComplete(pilotFeedback)} onClick={submitFeedback} className="btn-secondary disabled:opacity-60">{feedbackSaved ? 'Feedback saved' : savingFeedback ? 'Saving…' : 'Save tester feedback'}</button>
          </div>
        </div>
      )}
    </section>
  );
}
