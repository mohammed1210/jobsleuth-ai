'use client';

import { useRef, useState } from 'react';
import type { Session } from '@supabase/supabase-js';

import {
  importEvidenceDocument,
  type EvidenceImportSuggestion,
} from '@/lib/evidenceImportApi';

type Props = {
  session: Session;
  onReview: (draft: EvidenceImportSuggestion) => void;
};

export default function EvidenceImportPanel({ session, onReview }: Props) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [files, setFiles] = useState<File[]>([]);
  const [suggestions, setSuggestions] = useState<EvidenceImportSuggestion[]>([]);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const runImport = async () => {
    if (!files.length) return;
    setBusy(true);
    setMessage(null);
    const next: EvidenceImportSuggestion[] = [];
    const failures: string[] = [];

    for (const file of files.slice(0, 10)) {
      try {
        const result = await importEvidenceDocument(session, file);
        next.push(
          ...result.drafts.map((draft) => ({
            ...draft,
            source_filename: result.source_filename,
          })),
        );
      } catch (error) {
        failures.push(
          `${file.name}: ${error instanceof Error ? error.message : 'could not extract examples'}`,
        );
      }
    }

    setSuggestions(next);
    if (next.length && failures.length) {
      setMessage(`Found ${next.length} example(s). ${failures.length} file(s) could not be processed.`);
    } else if (next.length) {
      setMessage(`Found ${next.length} reusable example(s). Review only the ones you want to keep.`);
    } else if (failures.length) {
      setMessage(failures.join(' '));
    }
    setBusy(false);
  };

  return (
    <section className="rounded-2xl border border-brand-200 bg-brand-50/60 p-5">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="max-w-2xl">
          <p className="text-xs font-semibold uppercase tracking-wide text-brand-700">Fastest way to build your Evidence Bank</p>
          <h2 className="mt-1 text-xl font-bold text-gray-900">Import past applications</h2>
          <p className="mt-2 text-sm text-gray-700">
            Upload old personal statements or applications. JobSleuth will pull out reusable examples so you can review them instead of typing the same experience again.
          </p>
          <p className="mt-1 text-xs text-gray-500">PDF, DOCX or TXT · up to 5 MB each · raw files are processed for extraction and are not saved to your Evidence Bank.</p>
        </div>
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-3">
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.docx,.txt"
          multiple
          className="hidden"
          onChange={(event) => {
            const selected = Array.from(event.target.files ?? []).slice(0, 10);
            setFiles(selected);
            setSuggestions([]);
            setMessage(null);
          }}
        />
        <button type="button" className="btn-secondary" onClick={() => inputRef.current?.click()}>
          Choose past applications
        </button>
        {files.length > 0 && (
          <>
            <span className="text-sm text-gray-600">{files.length} file{files.length === 1 ? '' : 's'} selected</span>
            <button type="button" className="btn-primary" onClick={runImport} disabled={busy}>
              {busy ? 'Extracting examples…' : 'Find my examples'}
            </button>
          </>
        )}
      </div>

      {message && <p className="mt-3 text-sm text-gray-700">{message}</p>}

      {suggestions.length > 0 && (
        <div className="mt-5 grid gap-3 md:grid-cols-2">
          {suggestions.map((draft, index) => (
            <article key={`${draft.source_filename}-${draft.title}-${index}`} className="rounded-xl border bg-white p-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-gray-400">{draft.source_filename}</p>
              <h3 className="mt-1 font-semibold text-gray-900">{draft.title}</h3>
              <p className="mt-2 line-clamp-3 text-sm text-gray-600">
                {draft.actions[0] || draft.situation || draft.task || draft.outcome}
              </p>
              <div className="mt-3 flex flex-wrap gap-1.5">
                {draft.skills.slice(0, 4).map((skill) => (
                  <span key={skill} className="rounded-full bg-gray-100 px-2 py-1 text-xs text-gray-600">{skill}</span>
                ))}
              </div>
              <button type="button" className="btn-secondary mt-4 px-3 py-2 text-sm" onClick={() => onReview(draft)}>
                Review & save
              </button>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
