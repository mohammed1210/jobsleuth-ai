'use client';

import { useMemo, useState } from 'react';
import type { Session } from '@supabase/supabase-js';

import type { EvidenceCard, VacancyAnalysis } from '@/lib/applyApi';
import {
  buildApplication,
  type ApplicationDraftResult,
  type ApplicationType,
} from '@/lib/applicationBuilderApi';

type Props = {
  session: Session;
  analysis: VacancyAnalysis;
  evidence: EvidenceCard[];
};

const statusLabel: Record<string, string> = {
  covered: 'Covered',
  'partially-covered': 'Partial',
  'evidence-gap': 'Evidence gap',
  'not-used': 'Not used',
};

export default function ApplicationDraftPanel({ session, analysis, evidence }: Props) {
  const [roleTitle, setRoleTitle] = useState('');
  const [organisation, setOrganisation] = useState('');
  const [applicationType, setApplicationType] = useState<ApplicationType>('statement_of_suitability');
  const [wordLimit, setWordLimit] = useState(500);
  const [result, setResult] = useState<ApplicationDraftResult | null>(null);
  const [draft, setDraft] = useState('');
  const [building, setBuilding] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const liveWordCount = useMemo(() => draft.trim() ? draft.trim().split(/\s+/).length : 0, [draft]);

  const build = async () => {
    setBuilding(true);
    setMessage(null);
    try {
      const next = await buildApplication(session, {
        roleTitle,
        organisation,
        applicationType,
        wordLimit,
        requirements: analysis.requirements,
        evidenceCards: evidence,
      });
      setResult(next);
      setDraft(next.draft);
      if (!next.can_generate) {
        setMessage('JobSleuth did not find enough supported evidence to draft safely. Strengthen the Evidence Bank first.');
      }
    } catch {
      setMessage('Application Builder could not generate a draft. Please try again.');
    } finally {
      setBuilding(false);
    }
  };

  const copyDraft = async () => {
    if (!draft) return;
    await navigator.clipboard.writeText(draft);
    setMessage('Draft copied to clipboard.');
  };

  return (
    <section className="card p-6 space-y-5">
      <div>
        <p className="text-sm font-semibold text-brand-700">Application Builder</p>
        <h2 className="mt-1 text-2xl font-bold text-gray-900">Turn matched evidence into a supported draft</h2>
        <p className="mt-2 text-sm text-gray-600">
          JobSleuth uses only Strong or Partial matched Evidence Cards. Missing evidence stays visible rather than being invented.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <label className="text-sm font-medium text-gray-700">
          Role title
          <input
            value={roleTitle}
            onChange={(event) => setRoleTitle(event.target.value)}
            className="mt-1 w-full rounded-xl border px-3 py-2"
            placeholder="e.g. Counter Fraud Officer"
          />
        </label>
        <label className="text-sm font-medium text-gray-700">
          Organisation
          <input
            value={organisation}
            onChange={(event) => setOrganisation(event.target.value)}
            className="mt-1 w-full rounded-xl border px-3 py-2"
            placeholder="Optional"
          />
        </label>
        <label className="text-sm font-medium text-gray-700">
          Application type
          <select
            value={applicationType}
            onChange={(event) => setApplicationType(event.target.value as ApplicationType)}
            className="mt-1 w-full rounded-xl border px-3 py-2"
          >
            <option value="statement_of_suitability">Statement of suitability</option>
            <option value="criteria_response">Essential criteria response</option>
          </select>
        </label>
        <label className="text-sm font-medium text-gray-700">
          Word limit
          <input
            type="number"
            min={150}
            max={1500}
            value={wordLimit}
            onChange={(event) => setWordLimit(Math.min(1500, Math.max(150, Number(event.target.value) || 500)))}
            className="mt-1 w-full rounded-xl border px-3 py-2"
          />
        </label>
      </div>

      <button type="button" onClick={build} disabled={building} className="btn-primary disabled:opacity-60">
        {building ? 'Building evidence-backed draft…' : 'Build application draft'}
      </button>

      {message && <div className="rounded-xl border bg-white px-4 py-3 text-sm text-gray-700">{message}</div>}

      {result && (
        <div className="space-y-5">
          {result.warnings.length > 0 && (
            <div className="rounded-xl border border-amber-200 bg-amber-50 p-4">
              <p className="font-semibold text-amber-900">Review before submitting</p>
              <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-amber-900">
                {result.warnings.map((warning) => <li key={warning}>{warning}</li>)}
              </ul>
            </div>
          )}

          <div>
            <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
              <div>
                <h3 className="font-semibold text-gray-900">Editable draft</h3>
                <p className="text-xs text-gray-500">Provider: {result.provider}</p>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-sm text-gray-600">{liveWordCount} / {wordLimit} words</span>
                <button type="button" onClick={copyDraft} className="btn-secondary">Copy</button>
              </div>
            </div>
            <textarea
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              className="min-h-[28rem] w-full rounded-xl border px-4 py-3 leading-7"
              placeholder="A supported draft will appear here."
            />
            <p className="mt-2 text-xs text-gray-500">
              The evidence audit below describes the generated version. Re-check facts after substantial manual edits.
            </p>
          </div>

          <div>
            <h3 className="font-semibold text-gray-900">Criteria coverage</h3>
            <div className="mt-3 space-y-2">
              {result.coverage.map((item, index) => (
                <div key={`${item.requirement}-${index}`} className="rounded-xl border p-3">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="text-sm font-medium text-gray-900">{item.requirement}</p>
                      <p className="mt-1 text-xs uppercase tracking-wide text-gray-500">{item.category} · {item.match_strength}</p>
                    </div>
                    <span className="rounded-full bg-gray-100 px-3 py-1 text-xs font-semibold text-gray-700">
                      {statusLabel[item.status] || item.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {result.paragraphs.length > 0 && (
            <div>
              <h3 className="font-semibold text-gray-900">Evidence audit</h3>
              <div className="mt-3 space-y-3">
                {result.paragraphs.map((paragraph, index) => (
                  <details key={`${paragraph.evidence_ids.join('-')}-${index}`} className="rounded-xl border p-4">
                    <summary className="cursor-pointer text-sm font-semibold text-gray-900">
                      Paragraph {index + 1} · {paragraph.grounding_status}
                    </summary>
                    <div className="mt-3 space-y-2 text-sm text-gray-600">
                      {paragraph.supporting_facts.map((fact, factIndex) => (
                        <div key={`${fact.evidence_id}-${fact.field}-${factIndex}`} className="rounded-lg bg-gray-50 p-3">
                          <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">{fact.field}</p>
                          <p className="mt-1">{fact.text}</p>
                        </div>
                      ))}
                    </div>
                  </details>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </section>
  );
}
