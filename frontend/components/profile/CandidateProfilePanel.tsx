'use client';

import { useRef, useState } from 'react';
import type { Session } from '@supabase/supabase-js';

import {
  deleteCandidateProfile,
  uploadCandidateCv,
  type CandidateProfile,
} from '@/lib/candidateProfileApi';

type Props = {
  session: Session;
  profile: CandidateProfile | null;
  onProfileChange: (profile: CandidateProfile | null) => void;
};

export default function CandidateProfilePanel({ session, profile, onProfileChange }: Props) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [uploading, setUploading] = useState(false);
  const [removing, setRemoving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const upload = async (file: File | null) => {
    if (!file) return;
    setUploading(true);
    setMessage(null);
    try {
      const next = await uploadCandidateCv(session, file);
      onProfileChange(next);
      setMessage('CV profile updated. The raw file was processed for extraction and is not stored by JobSleuth.');
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Could not process this CV.');
    } finally {
      setUploading(false);
      if (inputRef.current) inputRef.current.value = '';
    }
  };

  const remove = async () => {
    if (!window.confirm('Remove the structured CV profile from JobSleuth?')) return;
    setRemoving(true);
    setMessage(null);
    try {
      await deleteCandidateProfile(session);
      onProfileChange(null);
      setMessage('CV profile removed.');
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Could not remove the CV profile.');
    } finally {
      setRemoving(false);
    }
  };

  return (
    <section className="card p-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="max-w-3xl">
          <p className="text-sm font-semibold text-brand-700">CV profile</p>
          <h2 className="mt-1 text-2xl font-bold text-gray-900">
            {profile ? 'Your CV is helping JobSleuth match roles' : 'Upload your CV to improve matching'}
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            JobSleuth extracts skills, employment history and qualifications. CV-only matches are treated as signals, not verified Evidence Bank proof.
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          <input
            ref={inputRef}
            type="file"
            accept=".pdf,.docx,.txt,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain"
            className="hidden"
            onChange={(event) => void upload(event.target.files?.[0] ?? null)}
          />
          <button type="button" className="btn-primary px-4 py-2 text-sm" disabled={uploading} onClick={() => inputRef.current?.click()}>
            {uploading ? 'Processing CV…' : profile ? 'Replace CV' : 'Upload CV'}
          </button>
          {profile && (
            <button type="button" className="btn-ghost text-sm" disabled={removing} onClick={() => void remove()}>
              {removing ? 'Removing…' : 'Remove'}
            </button>
          )}
        </div>
      </div>

      <p className="mt-3 text-xs text-gray-500">PDF, DOCX or TXT · maximum 5 MB · raw CV file is not retained. Extraction may use JobSleuth&apos;s configured AI provider.</p>

      {message && <div className="mt-4 rounded-xl border bg-white px-4 py-3 text-sm text-gray-700">{message}</div>}

      {profile && (
        <div className="mt-5 space-y-4">
          <div className="grid gap-3 sm:grid-cols-3">
            <div className="rounded-xl bg-gray-50 px-4 py-3">
              <p className="text-2xl font-bold text-gray-900">{profile.skills.length}</p>
              <p className="text-xs font-medium uppercase tracking-wide text-gray-500">Skills</p>
            </div>
            <div className="rounded-xl bg-gray-50 px-4 py-3">
              <p className="text-2xl font-bold text-gray-900">{profile.experience.length}</p>
              <p className="text-xs font-medium uppercase tracking-wide text-gray-500">Experience entries</p>
            </div>
            <div className="rounded-xl bg-gray-50 px-4 py-3">
              <p className="text-2xl font-bold text-gray-900">{profile.qualifications.length}</p>
              <p className="text-xs font-medium uppercase tracking-wide text-gray-500">Qualifications</p>
            </div>
          </div>

          {(Boolean(profile.summary) || profile.skills.length > 0 || profile.experience.length > 0 || profile.qualifications.length > 0) && (
            <details className="rounded-xl border bg-white">
              <summary className="cursor-pointer list-none px-4 py-3 text-sm font-semibold text-gray-800">
                Review extracted CV profile
                <span className="ml-2 text-xs font-normal text-gray-500">{profile.source_filename}</span>
              </summary>
              <div className="space-y-5 border-t p-4">
                {profile.summary && (
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">Summary</p>
                    <p className="mt-2 text-sm text-gray-700">{profile.summary}</p>
                  </div>
                )}

                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">Skills</p>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {profile.skills.map((skill) => (
                      <span key={skill} className="rounded-full bg-brand-50 px-3 py-1 text-xs font-semibold text-brand-700">{skill}</span>
                    ))}
                  </div>
                </div>

                {profile.experience.length > 0 && (
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">Experience</p>
                    <div className="mt-2 space-y-3">
                      {profile.experience.map((item, index) => (
                        <div key={`${item.role}-${item.organisation}-${index}`} className="rounded-xl bg-gray-50 p-4">
                          <p className="font-semibold text-gray-900">{item.role || 'Experience'}{item.organisation ? ` · ${item.organisation}` : ''}</p>
                          {item.dates && <p className="mt-1 text-xs text-gray-500">{item.dates}</p>}
                          {item.highlights.length > 0 && (
                            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-gray-700">
                              {item.highlights.slice(0, 6).map((highlight, highlightIndex) => <li key={`${highlight}-${highlightIndex}`}>{highlight}</li>)}
                            </ul>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {profile.qualifications.length > 0 && (
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">Qualifications</p>
                    <ul className="mt-2 space-y-2 text-sm text-gray-700">
                      {profile.qualifications.map((qualification, index) => (
                        <li key={`${qualification.name}-${index}`}>
                          <span className="font-medium">{qualification.name}</span>
                          {qualification.institution ? ` · ${qualification.institution}` : ''}
                          {qualification.date ? ` · ${qualification.date}` : ''}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </details>
          )}
        </div>
      )}
    </section>
  );
}
