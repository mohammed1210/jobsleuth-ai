'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import HeaderClient from '@/components/HeaderClient';
import { fetchJobDetail, fetchSavedJobs, saveJob, deleteSavedJob, type Job } from '@/lib/api';
import { getFreshSession, isSupabaseConfigured } from '@/lib/supabaseClient';

type SavedState = 'signed-out' | 'saved' | 'unsaved' | 'unknown';

/** Display source descriptions as escaped text, not executable scraped HTML. */
function plainDescription(value: string | null | undefined): string {
  if (!value) return 'The source has not provided a job description.';
  const text = value.replace(/<br\s*\/?\s*>/gi, '\n')
    .replace(/<\/(?:p|div|h[1-6]|li)>/gi, '\n')
    .replace(/<[^>]*>/g, '')
    .replace(/&nbsp;/gi, ' ')
    .replace(/&amp;/gi, '&')
    .trim();
  return text || 'The source has not provided a job description.';
}

function safeApplyUrl(value: string | null | undefined): string | null {
  if (!value) return null;
  try {
    const url = new URL(value);
    return url.protocol === 'https:' || url.protocol === 'http:' ? url.toString() : null;
  } catch {
    return null;
  }
}

export default function JobDetailPage() {
  const params = useParams();
  const rawJobId = typeof params?.id === 'string' ? params.id : '';
  const [job, setJob] = useState<Job | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [savedState, setSavedState] = useState<SavedState>('signed-out');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    let active = true;
    const load = async () => {
      setLoading(true);
      setJob(null);
      setLoadError(null);
      setActionError(null);
      setNotFound(false);
      setSavedState('signed-out');

      const id = Number(rawJobId);
      if (!/^\d+$/.test(rawJobId) || !Number.isSafeInteger(id) || id <= 0) {
        if (active) {
          setNotFound(true);
          setLoading(false);
        }
        return;
      }

      try {
        const record = await fetchJobDetail(id);
        if (!active) return;
        if (!record) {
          setNotFound(true);
          return;
        }
        setJob(record);
        if (isSupabaseConfigured()) {
          try {
            const session = await getFreshSession();
            if (!active) return;
            if (session) {
              setSavedState('unknown');
              const saved = await fetchSavedJobs(session);
              if (!active) return;
              setSavedState(saved.some((item) => item.job_id === id) ? 'saved' : 'unsaved');
            }
          } catch {
            if (!active) return;
            setSavedState('unknown');
            setActionError('Saved status is unavailable. Reload this page to retry.');
          }
        }
      } catch (err) {
        if (active) setLoadError(err instanceof Error ? err.message : 'Job details could not be loaded.');
      } finally {
        if (active) setLoading(false);
      }
    };
    void load();
    return () => { active = false; };
  }, [rawJobId]);

  const handleSave = async () => {
    if (!job || saving || savedState === 'unknown') return;
    setActionError(null);
    if (!isSupabaseConfigured()) {
      setActionError('Sign-in is not configured yet.');
      return;
    }
    setSaving(true);
    try {
      const session = await getFreshSession();
      if (!session) {
        setActionError('Sign in to save this job.');
        return;
      }
      if (savedState === 'saved') {
        await deleteSavedJob(job.id, session);
        setSavedState('unsaved');
      } else {
        await saveJob(job.id, session);
        setSavedState('saved');
      }
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Saved Jobs could not be updated.');
    } finally {
      setSaving(false);
    }
  };

  const handleShare = async () => {
    if (!job) return;
    try {
      if (navigator.share) {
        await navigator.share({
          title: job.title,
          text: `Job opportunity: ${job.title} at ${job.company}`,
          url: window.location.href,
        });
      } else {
        await navigator.clipboard.writeText(window.location.href);
        setActionError('Job link copied to your clipboard.');
      }
    } catch {
      // Cancelling a system share dialog is not an error in job data.
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen">
        <HeaderClient />
        <main className="max-w-5xl mx-auto px-6 py-12 text-center">
          <p className="text-gray-600">Loading job details from JobSleuth...</p>
        </main>
      </div>
    );
  }

  if (!job) {
    return (
      <div className="min-h-screen">
        <HeaderClient />
        <main className="max-w-5xl mx-auto px-6 py-12">
          <div className="card p-10 text-center">
            <h1 className="text-3xl font-bold text-gray-900">
              {notFound ? 'Job not found' : 'Job details unavailable'}
            </h1>
            <p className="text-gray-600 mt-3">
              {notFound ? 'This vacancy was not found in the database.' :
                loadError || 'Please try again later.'}
            </p>
            <Link href="/jobs" className="btn-primary mt-6 inline-flex">Back to Jobs</Link>
          </div>
        </main>
      </div>
    );
  }

  const applyUrl = safeApplyUrl(job.url);
  return (
    <div className="min-h-screen">
      <HeaderClient />
      <main className="max-w-5xl mx-auto px-6 py-8">
        <Link href="/jobs" className="inline-flex text-brand-600 hover:text-brand-700 font-medium mb-6">
          ← Back to Jobs
        </Link>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 space-y-6">
            <section className="card p-8">
              <h1 className="text-4xl font-bold text-gray-900 mb-2">{job.title}</h1>
              <p className="text-2xl text-gray-700 font-semibold mb-4">{job.company}</p>

              <div className="flex flex-wrap gap-3 mb-6 text-sm text-gray-700">
                <span className="rounded-lg bg-gray-100 px-4 py-2">{job.location}</span>
                {job.salary && <span className="rounded-lg bg-gray-100 px-4 py-2">{job.salary}</span>}
                {job.role_type && <span className="rounded-lg bg-gray-100 px-4 py-2">{job.role_type}</span>}
                {job.source === 'dfe_teaching_vacancies' ? (
                  <span className="rounded-lg bg-gray-100 px-4 py-2">
                    Source: DfE Teaching Vacancies —{' '}
                    <a href="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
                      target="_blank" rel="noopener noreferrer" className="underline">
                      OGL v3.0
                    </a>
                  </span>
                ) : job.source ? (
                  <span className="rounded-lg bg-gray-100 px-4 py-2">Source: {job.source}</span>
                ) : null}
              </div>

              {actionError && (
                <p role="status" className="text-sm text-amber-800 mb-4">{actionError}</p>
              )}

              <div className="flex flex-wrap gap-3">
                <button type="button" onClick={handleSave}
                  disabled={saving || savedState === 'unknown'}
                  className="btn-secondary disabled:opacity-50">
                  {saving ? 'Updating…' :
                    savedState === 'saved' ? 'Remove saved job' :
                    savedState === 'unknown' ? 'Saved status unavailable' : 'Save job'}
                </button>
                {applyUrl && (
                  <a href={applyUrl} target="_blank" rel="noopener noreferrer"
                    className="btn-primary inline-flex">View original vacancy</a>
                )}
                <button type="button" onClick={handleShare}
                  className="rounded-xl px-4 py-3 bg-gray-100 text-gray-700 hover:bg-gray-200">
                  Share
                </button>
              </div>
            </section>

            <section className="card p-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-5">Job Description</h2>
              <div className="whitespace-pre-wrap break-words text-gray-700 leading-relaxed">
                {plainDescription(job.description)}
              </div>
            </section>
          </div>

          <aside className="lg:col-span-1">
            <div className="card p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-3">Vacancy details</h2>
              <p className="text-sm text-gray-600">
                Information shown here comes from the selected job record. An AI match
                percentage will only appear when a verified assessment is available.
              </p>
              {job.source && <p className="mt-4 text-sm text-gray-700">Listed via: {job.source}</p>}
            </div>
          </aside>
        </div>
      </main>
    </div>
  );
}
