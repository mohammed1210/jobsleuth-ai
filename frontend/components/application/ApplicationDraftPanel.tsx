'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import type { Session } from '@supabase/supabase-js';

import type { EvidenceCard, VacancyAnalysis } from '@/lib/applyApi';
import { buildApplication, type ApplicationDraftResult, type ApplicationType } from '@/lib/applicationBuilderApi';
import { detectApplicationInstructions } from '@/lib/applicationInstructions';
import { savePilotFeedback, type PaymentSignal } from '@/lib/pilotFeedbackApi';

type Props = { session: Session; analysis: VacancyAnalysis; evidence: EvidenceCard[]; vacancyText: string };

const statusLabel: Record<string, string> = {
  covered: 'Covered',
  'partially-covered': 'Partial',
  'evidence-gap': 'Evidence gap',
  'not-used': 'Not used',
};

export default function ApplicationDraftPanel({ session, analysis, evidence, vacancyText }: Props) {
  const instructions = useMemo(() => detectApplicationInstructions(vacancyText), [vacancyText]);
  const [roleTitle, setRoleTitle] = useState('');
  const [organisation, setOrganisation] = useState('');
  const [applicationType, setApplicationType] = useState<ApplicationType>('statement_of_suitability');
  const [wordLimitInput, setWordLimitInput] = useState('500');
  const [draftAnyway, setDraftAnyway] = useState(false);
  const [result, setResult] = useState<ApplicationDraftResult | null>(null);
  const [draft, setDraft] = useState('');
  const [building, setBuilding] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [usefulness, setUsefulness] = useState(8);
  const [wouldSubmit, setWouldSubmit] = useState(true);
  const [recommendationTrust, setRecommendationTrust] = useState(true);
  const [timeSaving, setTimeSaving] = useState(true);
  const [wouldUseAgain, setWouldUseAgain] = useState(true);
  const [paymentSignal, setPaymentSignal] = useState<PaymentSignal>('maybe');
  const [feedbackSaved, setFeedbackSaved] = useState(false);
  const [savingFeedback, setSavingFeedback] = useState(false);

  useEffect(() => {
    setRoleTitle(instructions.roleTitle);
    setOrganisation(instructions.organisation);
    setApplicationType(instructions.applicationType);
    if (instructions.wordLimit) setWordLimitInput(String(instructions.wordLimit));
    setDraftAnyway(false);
    setResult(null);
    setDraft('');
  }, [instructions]);

  const wordLimit = useMemo(() => {
    const parsed = Number(wordLimitInput);
    if (!Number.isFinite(parsed)) return 500;
    return Math.min(5000, Math.max(100, Math.round(parsed)));
  }, [wordLimitInput]);

  const liveWordCount = useMemo(() => draft.trim() ? draft.trim().split(/\s+/).length : 0, [draft]);

  const readiness = useMemo(() => {
    const essential = analysis.requirements.filter((item) => item.category === 'essential');
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
  }, [analysis.requirements]);

  const build = async () => {
    if (readiness.needsStrengthening && !draftAnyway) {
      setMessage('Review the evidence-readiness warning first. Strengthen your Evidence Bank or explicitly choose to draft with current evidence.');
      return;
    }
    setBuilding(true); setMessage(null); setFeedbackSaved(false);
    try {
      const next = await buildApplication(session, { roleTitle, organisation, applicationType, wordLimit, requirements: analysis.requirements, evidenceCards: evidence });
      setResult(next); setDraft(next.draft);
      if (!next.can_generate) setMessage('JobSleuth did not find enough supported evidence to draft safely. Strengthen the Evidence Bank first.');
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Application Builder could not generate a draft. Please try again.');
    } finally { setBuilding(false); }
  };

  const copyDraft = async () => {
    if (!draft) return;
    await navigator.clipboard.writeText(draft);
    setMessage('Draft copied to clipboard.');
  };

  const submitFeedback = async () => {
    if (!result) return;
    setSavingFeedback(true); setMessage(null);
    try {
      await savePilotFeedback(session, {
        provider: result.provider,
        recommendation: analysis.decision,
        application_type: applicationType,
        word_count: liveWordCount,
        usefulness,
        would_submit: wouldSubmit,
        recommendation_trust: recommendationTrust,
        material_time_saving: timeSaving,
        would_use_again: wouldUseAgain,
        payment_signal: paymentSignal,
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
        <h2 className="mt-1 text-2xl font-bold text-gray-900">Turn matched evidence into a supported draft</h2>
        <p className="mt-2 text-sm text-gray-600">JobSleuth uses only Strong or Partial matched Evidence Cards. Missing evidence stays visible rather than being invented.</p>
      </div>

      <div className="rounded-2xl border bg-gray-50 p-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">Detected application instructions</p>
            <p className="mt-1 text-sm font-medium text-gray-900">{instructions.applicationTypeLabel}{instructions.wordLimit ? ` · maximum ${instructions.wordLimit} words` : ''}</p>
          </div>
          {instructions.requiredDocuments.length > 0 && <p className="text-sm text-gray-600">Required: {instructions.requiredDocuments.join(' + ')}</p>}
        </div>
        <p className="mt-2 text-xs text-gray-500">These are pre-filled from the vacancy and remain editable.</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <label className="text-sm font-medium text-gray-700">Role title<input value={roleTitle} onChange={(e) => setRoleTitle(e.target.value)} className="mt-1 w-full rounded-xl border px-3 py-2" placeholder="e.g. Counter Fraud Officer" /></label>
        <label className="text-sm font-medium text-gray-700">Organisation<input value={organisation} onChange={(e) => setOrganisation(e.target.value)} className="mt-1 w-full rounded-xl border px-3 py-2" placeholder="Optional" /></label>
        <label className="text-sm font-medium text-gray-700">Application type<select value={applicationType} onChange={(e) => setApplicationType(e.target.value as ApplicationType)} className="mt-1 w-full rounded-xl border px-3 py-2"><option value="statement_of_suitability">Personal statement / statement of suitability</option><option value="criteria_response">Essential criteria response</option></select></label>
        <label className="text-sm font-medium text-gray-700">Word limit<input inputMode="numeric" value={wordLimitInput} onChange={(e) => setWordLimitInput(e.target.value.replace(/[^0-9]/g, ''))} onBlur={() => setWordLimitInput(String(wordLimit))} className="mt-1 w-full rounded-xl border px-3 py-2" placeholder="e.g. 750" /></label>
      </div>

      {readiness.needsStrengthening ? (
        <div className="rounded-2xl border border-amber-300 bg-amber-50 p-5">
          <h3 className="font-semibold text-amber-950">Evidence needs strengthening before drafting</h3>
          <p className="mt-2 text-sm text-amber-900">Of {readiness.total} essential criteria: {readiness.strong} Strong, {readiness.partial} Partial, {readiness.weak} Weak, {readiness.missing} Missing.</p>
          <p className="mt-2 text-sm text-amber-900">A draft can only use evidence JobSleuth can support. Missing or weak criteria will stay uncovered rather than being invented.</p>
          <div className="mt-4 flex flex-wrap gap-3">
            <Link href="/apply" className="btn-secondary">Strengthen Evidence Bank</Link>
            {!draftAnyway ? (
              <button type="button" onClick={() => setDraftAnyway(true)} className="btn-secondary">Draft with current evidence anyway</button>
            ) : (
              <span className="inline-flex items-center rounded-xl border border-amber-300 bg-white px-4 py-2 text-sm font-semibold text-amber-900">Current-evidence drafting enabled</span>
            )}
          </div>
        </div>
      ) : (
        <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-900"><strong>Evidence ready to draft.</strong> All {readiness.total} essential criteria have Strong support.</div>
      )}

      <button type="button" onClick={build} disabled={building || (readiness.needsStrengthening && !draftAnyway)} className="btn-primary disabled:cursor-not-allowed disabled:opacity-50">{building ? 'Building evidence-backed draft…' : 'Build application draft'}</button>
      {message && <div className="rounded-xl border bg-white px-4 py-3 text-sm text-gray-700">{message}</div>}

      {result && (
        <div className="space-y-5">
          {result.warnings.length > 0 && <div className="rounded-xl border border-amber-200 bg-amber-50 p-4"><p className="font-semibold text-amber-900">Review before submitting</p><ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-amber-900">{result.warnings.map((w) => <li key={w}>{w}</li>)}</ul></div>}

          <div>
            <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
              <div><h3 className="font-semibold text-gray-900">Editable draft</h3><p className="text-xs text-gray-500">Provider: {result.provider}{result.fallback_reason ? ` · fallback: ${result.fallback_reason}` : ''}</p></div>
              <div className="flex items-center gap-3"><span className="text-sm text-gray-600">{liveWordCount} / {wordLimit} words</span><button type="button" onClick={copyDraft} className="btn-secondary">Copy</button></div>
            </div>
            <textarea value={draft} onChange={(e) => setDraft(e.target.value)} className="min-h-[28rem] w-full rounded-xl border px-4 py-3 leading-7" placeholder="A supported draft will appear here." />
            <p className="mt-2 text-xs text-gray-500">The evidence audit below describes the generated version. Re-check facts after substantial manual edits.</p>
          </div>

          <div><h3 className="font-semibold text-gray-900">Criteria coverage</h3><div className="mt-3 space-y-2">{result.coverage.map((item, index) => <div key={`${item.requirement}-${index}`} className="rounded-xl border p-3"><div className="flex flex-wrap items-start justify-between gap-3"><div><p className="text-sm font-medium text-gray-900">{item.requirement}</p><p className="mt-1 text-xs uppercase tracking-wide text-gray-500">{item.category} · {item.match_strength}</p></div><span className="rounded-full bg-gray-100 px-3 py-1 text-xs font-semibold text-gray-700">{statusLabel[item.status] || item.status}</span></div></div>)}</div></div>

          {result.paragraphs.length > 0 && <div><h3 className="font-semibold text-gray-900">Evidence audit</h3><div className="mt-3 space-y-3">{result.paragraphs.map((paragraph, index) => <details key={`${paragraph.evidence_ids.join('-')}-${index}`} className="rounded-xl border p-4"><summary className="cursor-pointer text-sm font-semibold text-gray-900">Paragraph {index + 1} · {paragraph.grounding_status}</summary><div className="mt-3 space-y-2 text-sm text-gray-600">{paragraph.supporting_facts.map((fact, factIndex) => <div key={`${fact.evidence_id}-${fact.field}-${factIndex}`} className="rounded-lg bg-gray-50 p-3"><p className="text-xs font-semibold uppercase tracking-wide text-gray-500">{fact.field}</p><p className="mt-1">{fact.text}</p></div>)}</div></details>)}</div></div>}

          <div className="rounded-2xl border border-brand-100 bg-brand-50/40 p-5 space-y-4">
            <div><h3 className="font-semibold text-gray-900">Tester feedback</h3><p className="mt-1 text-sm text-gray-600">Help us validate JobSleuth. We store these ratings only — not your vacancy, evidence or draft text.</p></div>
            <label className="block text-sm font-medium text-gray-700">How useful was this result? <strong>{usefulness}/10</strong><input className="mt-2 w-full" type="range" min={1} max={10} value={usefulness} onChange={(e) => setUsefulness(Number(e.target.value))} /></label>
            <div className="grid gap-3 md:grid-cols-2">
              {[['Would you submit this after review?', wouldSubmit, setWouldSubmit], ['Did you trust the Apply/Consider/Skip recommendation?', recommendationTrust, setRecommendationTrust], ['Did this materially save you time?', timeSaving, setTimeSaving], ['Would you use JobSleuth for another vacancy?', wouldUseAgain, setWouldUseAgain]].map(([label, value, setter]) => <label key={String(label)} className="flex items-center justify-between gap-3 rounded-xl bg-white p-3 text-sm"><span>{String(label)}</span><input type="checkbox" checked={Boolean(value)} onChange={(e) => (setter as (v: boolean) => void)(e.target.checked)} /></label>)}
            </div>
            <label className="block text-sm font-medium text-gray-700">Would you pay for continued access?<select value={paymentSignal} onChange={(e) => setPaymentSignal(e.target.value as PaymentSignal)} className="mt-1 w-full rounded-xl border px-3 py-2"><option value="yes">Yes</option><option value="maybe">Maybe</option><option value="no">No</option></select></label>
            <button type="button" disabled={savingFeedback || feedbackSaved} onClick={submitFeedback} className="btn-secondary disabled:opacity-60">{feedbackSaved ? 'Feedback saved' : savingFeedback ? 'Saving…' : 'Save tester feedback'}</button>
          </div>
        </div>
      )}
    </section>
  );
}
