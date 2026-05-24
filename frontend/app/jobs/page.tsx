'use client';

import { FormEvent, useEffect, useState } from 'react';
import HeaderClient from '@/components/HeaderClient';
import JobCard from '@/components/JobCard';
import { fallbackJobs, fetchJobs as fetchJobsFromApi, saveJob, type Job } from '@/lib/api';
import { getSupabaseClient, isSupabaseConfigured } from '@/lib/supabaseClient';

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
      <main className="max-w-7xl mx-auto px-6 py-12">
        <div className="mb-8">
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-3">
            Discover Your <span className="text-gradient">Next Opportunity</span>
          </h1>
          <p className="text-xl text-gray-600">
            Explore thousands of opportunities matched by AI to your profile
          </p>
        </div>

        <form onSubmit={handleSearch} className="card p-6 mb-8">
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <div className="md:col-span-2">
              <label htmlFor="search" className="block text-sm font-semibold text-gray-700 mb-2">
                Job Title or Keywords
              </label>
              <input
                id="search"
                type="text"
                value={searchQuery}
                onChange={(event) => setSearchQuery(event.target.value)}
                placeholder="e.g. Software Engineer"
                className="input-modern"
              />
            </div>
            <div>
              <label htmlFor="location" className="block text-sm font-semibold text-gray-700 mb-2">
                Location
              </label>
              <input
                id="location"
                type="text"
                value={location}
                onChange={(event) => setLocation(event.target.value)}
                placeholder="e.g. Remote"
                className="input-modern"
              />
            </div>
            <div>
              <label htmlFor="roleType" className="block text-sm font-semibold text-gray-700 mb-2">
                Type
              </label>
              <select id="roleType" value={roleType} onChange={(event) => setRoleType(event.target.value)} className="input-modern">
                <option value="">Any type</option>
                <option value="Remote">Remote</option>
                <option value="Hybrid">Hybrid</option>
                <option value="Full-time">Full-time</option>
              </select>
            </div>
            <div>
              <label htmlFor="salaryMin" className="block text-sm font-semibold text-gray-700 mb-2">
                Min Salary
              </label>
              <input
                id="salaryMin"
                value={salaryMin}
                onChange={(event) => setSalaryMin(event.target.value)}
                placeholder="e.g. 90000"
                inputMode="numeric"
                className="input-modern"
              />
            </div>
            <div className="md:col-span-5 flex justify-end">
              <button type="submit" className="btn-primary flex items-center justify-center">
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                Search Jobs
              </button>
            </div>
          </div>
        </form>

        {error && <div className="mb-6 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-medium text-amber-800">{error}</div>}

        {loading ? (
          <div className="text-center py-20">
            <div className="inline-flex items-center justify-center">
              <div className="w-12 h-12 border-4 border-brand-200 border-t-brand-600 rounded-full animate-spin"></div>
            </div>
            <p className="mt-4 text-lg text-gray-600 font-medium">Finding perfect matches...</p>
            <p className="mt-2 text-sm text-gray-500">AI is analyzing thousands of opportunities</p>
          </div>
        ) : (
          <>
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center space-x-3">
                <div className="ai-badge text-sm">
                  <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                  </svg>
                  AI-Matched
                </div>
                <span className="text-lg text-gray-700">
                  <span className="font-bold text-gray-900">{jobs.length}</span> jobs found
                </span>
              </div>
              <div className="flex items-center space-x-2">
                <label htmlFor="sort" className="text-sm font-medium text-gray-700">Sort by:</label>
                <select id="sort" className="px-3 py-2 bg-white border-2 border-gray-200 rounded-lg text-sm font-medium focus:border-brand-500 focus:ring-2 focus:ring-brand-500/10 outline-none transition-all">
                  <option>Best Match</option>
                  <option>Most Recent</option>
                  <option>Salary: High to Low</option>
                  <option>Salary: Low to High</option>
                </select>
              </div>
            </div>
            <div className="space-y-6 mb-12">
              {jobs.map((job, index) => (
                <JobCard key={job.id} job={job} onSave={handleSaveJob} aiScore={job.ai_score ?? 0.75 + (index * 0.05)} />
              ))}
            </div>
            {totalPages > 1 && (
              <div className="flex justify-center items-center gap-2">
                <button onClick={() => setPage(Math.max(1, page - 1))} disabled={page === 1} className="px-6 py-3 border-2 border-gray-300 rounded-lg font-semibold disabled:opacity-50 disabled:cursor-not-allowed hover:border-brand-500 hover:bg-brand-50 transition-all">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
                  </svg>
                </button>
                {[...Array(totalPages)].map((_, index) => (
                  <button key={index + 1} onClick={() => setPage(index + 1)} className={`w-12 h-12 rounded-lg font-semibold transition-all ${page === index + 1 ? 'bg-gradient-ai text-white shadow-ai' : 'bg-white border-2 border-gray-300 text-gray-700 hover:border-brand-500'}`}>{index + 1}</button>
                ))}
                <button onClick={() => setPage(Math.min(totalPages, page + 1))} disabled={page === totalPages} className="px-6 py-3 border-2 border-gray-300 rounded-lg font-semibold disabled:opacity-50 disabled:cursor-not-allowed hover:border-brand-500 hover:bg-brand-50 transition-all">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                  </svg>
                </button>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}
