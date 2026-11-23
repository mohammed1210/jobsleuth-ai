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
  const [checkedAt, setCheckedAt] = useState(() => Date.now());

  useEffect(() => {
    const refresh = () => setCheckedAt(Date.now());
    const interval = window.setInterval(refresh, 60_000);
    window.addEventListener('focus', refresh);
    document.addEventListener('visibilitychange', refresh);
    return () => {
      window.clearInterval(interval);
      window.removeEventListener('focus', refresh);
      document.removeEventListener('visibilitychange', refresh);
    };
  }, []);

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

  const deadline = job.expires_at ? Date.parse(job.expires_at) : NaN;
  const closed = job.is_active === false || (Number.isFinite(deadline) && checkedAt >= deadline);
  const closingDate = Number.isFinite(deadline)
    ? new Intl.DateTimeFormat('en-GB', {
        day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit',
        minute: '2-digit', hour12: false, timeZone: 'Europe/London',
      }).format(new Date(deadline))
    : null;
  const applyUrl = !closed ? safeApplyUrl(job.url) : null;
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
                {job.salary && <span className="rounded-lg bg-emerald-50 px-4 py-2 font-medium text-emerald-800">{job.salary}</span>}
                {job.role_type && <span className="rounded-lg bg-violet-50 px-4 py-2 text-violet-700">{job.role_type}</span>}
                {closingDate && <span className="rounded-lg bg-amber-50 px-4 py-2 text-amber-800">
                  {closed ? 'Closed' : 'Closes'} {closingDate}
                </span>}
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

              {closed && (
                <p role="status" className="mb-4 rounded-lg bg-amber-50 p-3 text-amber-800">
                  This vacancy has closed. The original application link is no longer offered.
                </p>
              )}
              <div className="flex flex-wrap gap-3">
                <button type="button" onClick={handleSave}
                  disabled={saving || savedState === 'unknown' || (closed && savedState !== 'saved')}
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
            <div className="card">
              <div className="bg-gradient-ai px-6 py-6 text-white">
                <h2 className="text-xl font-bold">Vacancy overview</h2>
                <p className="mt-2 text-sm text-white/90">Facts from the original job advert</p>
              </div>
              <dl className="divide-y divide-gray-100 px-6">
                <div className="py-4">
                  <dt className="text-xs font-semibold uppercase tracking-wide text-gray-500">Employer</dt>
                  <dd className="mt-1 font-semibold text-gray-900">{job.company}</dd>
                </div>
                {closingDate && (
                  <div className="py-4">
                    <dt className="text-xs font-semibold uppercase tracking-wide text-gray-500">Application deadline</dt>
                    <dd className="mt-1 font-semibold text-gray-900">{closingDate}</dd>
                  </div>
                )}
                {job.salary && (
                  <div className="py-4">
                    <dt className="text-xs font-semibold uppercase tracking-wide text-gray-500">Advertised salary</dt>
                    <dd className="mt-1 font-semibold text-emerald-700">{job.salary}</dd>
                  </div>
                )}
                {job.role_type && (
                  <div className="py-4">
                    <dt className="text-xs font-semibold uppercase tracking-wide text-gray-500">Working pattern</dt>
                    <dd className="mt-1 font-semibold text-gray-900">{job.role_type}</dd>
                  </div>
                )}
                {job.source && (
                  <div className="py-4">
                    <dt className="text-xs font-semibold uppercase tracking-wide text-gray-500">Original source</dt>
                    <dd className="mt-1 text-sm font-medium text-gray-900">
                      {job.source === 'dfe_teaching_vacancies' ? 'DfE Teaching Vacancies' : job.source}
                    </dd>
                  </div>
                )}
              </dl>
              <div className="mx-6 mb-6 rounded-xl border border-brand-100 bg-brand-50 p-4">
                <p className="font-semibold text-brand-800">AI suitability match</p>
                <p className="mt-1 text-sm text-gray-600">
                  Not assessed yet. A percentage will only appear after a verified
                  comparison with your profile or Evidence Bank.
                </p>
              </div>
            </div>
          </aside>
        </div>
      </main>
    </div>
  );
}
