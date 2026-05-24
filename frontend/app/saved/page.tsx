'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import type { Session } from '@supabase/supabase-js';
import HeaderClient from '@/components/HeaderClient';
import JobCard from '@/components/JobCard';
import { deleteSavedJob, fallbackJobs, fetchSavedJobs, type Job, type SavedJob } from '@/lib/api';
import { getSupabaseClient, isSupabaseConfigured } from '@/lib/supabaseClient';

export default function SavedJobsPage() {
  const [savedJobs, setSavedJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [session, setSession] = useState<Session | null>(null);
  const [userEmail, setUserEmail] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const run = async () => {
      if (!isSupabaseConfigured()) {
        setError('Supabase is not configured yet.');
        setLoading(false);
        return;
      }

      const supabase = getSupabaseClient();
      const { data } = await supabase.auth.getSession();
      const activeSession = data.session;
      setSession(activeSession);
      setUserEmail(activeSession?.user.email ?? null);

      if (!activeSession) {
        setLoading(false);
        return;
      }

      await loadSavedJobs(activeSession);
    };

    run();
  }, []);

  const mapSavedRows = (rows: SavedJob[]) => rows.map((row) => row.job ?? fallbackJobs.find((job) => job.id === row.job_id)).filter(Boolean) as Job[];

  const loadSavedJobs = async (activeSession: Session) => {
    setLoading(true);
    setError(null);
    try {
      const rows = await fetchSavedJobs(activeSession);
      setSavedJobs(mapSavedRows(rows));
    } catch (err) {
      console.error('Failed to fetch saved jobs:', err);
      setError('Saved jobs API unavailable, showing a local sample.');
      setSavedJobs(fallbackJobs.slice(0, 1));
    } finally {
      setLoading(false);
    }
  };

  const handleUnsave = async (jobId: number) => {
    if (session) await deleteSavedJob(jobId, session);
    setSavedJobs((rows) => rows.filter((job) => job.id !== jobId));
  };

  if (!userEmail && !loading) {
    return (
      <div className="min-h-screen">
        <HeaderClient />
        <main className="max-w-4xl mx-auto px-6 py-12">
          <div className="card p-10 text-center">
            <h1 className="text-3xl font-bold mb-3 text-gray-900">Sign in required</h1>
            <p className="text-gray-600 mb-6">Please sign in to view your saved jobs.</p>
            <Link href="/magic-login" className="btn-primary inline-flex">Sign in</Link>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <HeaderClient />
      <main className="max-w-6xl mx-auto px-6 py-12">
        <div className="mb-8">
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-3">
            Saved <span className="text-gradient">Jobs</span>
          </h1>
          <p className="text-xl text-gray-600">
            {savedJobs.length} {savedJobs.length === 1 ? 'job' : 'jobs'} saved
          </p>
        </div>

      {error && <div className="mb-6 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-medium text-amber-800">{error}</div>}

      {loading ? (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-brand-200 border-t-brand-600" />
          <p className="mt-2 text-gray-600">Loading saved jobs...</p>
        </div>
      ) : savedJobs.length === 0 ? (
        <div className="card p-10 text-center">
          <p className="text-gray-600 mb-4">You have not saved any jobs yet.</p>
          <Link href="/jobs" className="btn-secondary inline-flex">Browse Jobs</Link>
        </div>
      ) : (
        <div className="space-y-4">
          {savedJobs.map((job) => (
            <JobCard key={job.id} job={job} saved onSave={handleUnsave} />
          ))}
        </div>
      )}
      </main>
    </div>
  );
}
