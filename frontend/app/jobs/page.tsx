'use client';

import { FormEvent, useEffect, useState } from 'react';
import HeaderClient from '@/components/HeaderClient';
import JobCard from '@/components/JobCard';
import { fallbackJobs, fetchJobs as fetchJobsFromApi, saveJob, type Job } from '@/lib/api';
import { getSupabaseClient, isSupabaseConfigured } from '@/lib/supabaseClient';
import { Filter, Loader2, Search } from 'lucide-react';

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [location, setLocation] = useState('');
  const [roleType, setRoleType] = useState('');
  const [salaryMin, setSalaryMin] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const perPage = 10;

  async function loadJobs() {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchJobsFromApi({
        ...(searchQuery ? { q: searchQuery } : {}),
        ...(location ? { location } : {}),
        ...(roleType ? { role_type: roleType } : {}),
        ...(salaryMin ? { salary_min: salaryMin } : {}),
        page: String(page),
        per_page: String(perPage),
      });
      setJobs(data.jobs);
      setTotalPages(Math.max(1, Math.ceil(data.total / data.per_page)));
    } catch (err) {
      console.error('Failed to fetch jobs:', err);
      setError('Backend unavailable, showing local sample jobs.');
      setJobs(fallbackJobs);
      setTotalPages(1);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadJobs();
  }, [page]);

  function handleSearch(event: FormEvent) {
    event.preventDefault();
    if (page !== 1) {
      setPage(1);
      return;
    }
    loadJobs();
  }

  async function handleSaveJob(jobId: number) {
    if (!isSupabaseConfigured()) {
      setError('Sign in is not configured yet, but this job is ready to save once Supabase env vars are set.');
      return;
    }
    const supabase = getSupabaseClient();
    const { data } = await supabase.auth.getSession();
    if (!data.session) {
      setError('Sign in to save jobs.');
      return;
    }
    await saveJob(jobId, data.session);
  }

  return (
    <div className="min-h-screen">
      <HeaderClient />
      <main className="mx-auto max-w-7xl px-4 py-10 sm:px-6">
        <div className="mb-8">
          <h1 className="text-3xl font-bold tracking-tight text-slate-950 sm:text-4xl">Find jobs</h1>
          <p className="mt-2 text-slate-600">Search, filter, score, and save opportunities from a single workspace.</p>
        </div>

        <form onSubmit={handleSearch} className="card mb-8 p-5">
          <div className="mb-4 flex items-center gap-2 text-sm font-semibold text-slate-700"><Filter className="h-4 w-4" />Filters</div>
          <div className="grid gap-3 md:grid-cols-5">
            <input value={searchQuery} onChange={(event) => setSearchQuery(event.target.value)} placeholder="Title, keyword, company" className="input-modern md:col-span-2" />
            <input value={location} onChange={(event) => setLocation(event.target.value)} placeholder="Location" className="input-modern" />
            <select value={roleType} onChange={(event) => setRoleType(event.target.value)} className="input-modern">
              <option value="">Any type</option>
              <option value="Remote">Remote</option>
              <option value="Hybrid">Hybrid</option>
              <option value="Full-time">Full-time</option>
            </select>
            <input value={salaryMin} onChange={(event) => setSalaryMin(event.target.value)} placeholder="Min salary" inputMode="numeric" className="input-modern" />
          </div>
          <button type="submit" className="btn-primary mt-4 inline-flex items-center gap-2"><Search className="h-4 w-4" />Search jobs</button>
        </form>

        {error && <div className="mb-6 rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">{error}</div>}

        {loading ? (
          <div className="py-20 text-center">
            <Loader2 className="mx-auto h-8 w-8 animate-spin text-cyan-700" />
            <p className="mt-4 text-slate-600">Loading jobs...</p>
          </div>
        ) : (
          <>
            <div className="mb-6 flex items-center justify-between">
              <span className="text-sm font-semibold text-slate-700">{jobs.length} jobs found</span>
              <span className="ai-badge">AI scores included</span>
            </div>
            <div className="mb-12 space-y-6">
              {jobs.map((job) => (
                <JobCard key={job.id} job={job} onSave={handleSaveJob} />
              ))}
            </div>
            {totalPages > 1 && (
              <div className="flex items-center justify-center gap-2">
                <button onClick={() => setPage(Math.max(1, page - 1))} disabled={page === 1} className="rounded-md border border-slate-300 px-4 py-2 text-sm font-semibold disabled:opacity-50">Previous</button>
                {[...Array(totalPages)].map((_, index) => (
                  <button key={index + 1} onClick={() => setPage(index + 1)} className={`h-10 w-10 rounded-md text-sm font-semibold ${page === index + 1 ? 'bg-slate-950 text-white' : 'border border-slate-300 bg-white text-slate-700'}`}>{index + 1}</button>
                ))}
                <button onClick={() => setPage(Math.min(totalPages, page + 1))} disabled={page === totalPages} className="rounded-md border border-slate-300 px-4 py-2 text-sm font-semibold disabled:opacity-50">Next</button>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}
