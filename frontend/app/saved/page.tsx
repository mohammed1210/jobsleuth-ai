'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { createClient } from '@supabase/supabase-js';

// If you already have a shared helper at `@/lib/supabaseClient` you can import it instead.
// Here we inline to keep this file self-contained and avoid import-path issues in fresh repos.
const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL as string,
  process.env.NEXT_PUBLIC_SUPABASE_KEY as string
);

type SavedJob = {
  id: number;
  title: string;
  company: string;
  location: string;
  salary?: string;
  source?: string;
  date_posted?: string;
  url?: string;
  saved_at?: string;
};

export default function SavedJobsPage() {
  const [savedJobs, setSavedJobs] = useState<SavedJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [userEmail, setUserEmail] = useState<string | null>(null);

  useEffect(() => {
    const run = async () => {
      // 1) check auth
      const { data } = await supabase.auth.getUser();
      const user = data.user ?? null;
      setUserEmail(user?.email ?? null);

      if (!user) {
        setLoading(false);
        return;
      }

      // 2) fetch saved jobs (mock for now)
      await fetchSavedJobs(user.id);
    };

    run();
  }, []);

  const fetchSavedJobs = async (userId: string) => {
    setLoading(true);
    try {
      // TODO: replace with real call once backend route or Supabase table exists
      // e.g., const res = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/saved-jobs`, { headers: { Authorization: `Bearer ${token}` }})
      // const rows: SavedJob[] = await res.json();

      const mockRows: SavedJob[] = [
        {
          id: 1,
          title: 'Senior Software Engineer',
          company: 'TechCorp',
          location: 'San Francisco, CA',
          salary: '$120k - $180k',
          source: 'Indeed',
          date_posted: '2 days ago',
          url: 'https://example.com/job/1',
          saved_at: '2025-11-01',
        },
        {
          id: 2,
          title: 'Frontend Developer',
          company: 'StartupXYZ',
          location: 'Remote',
          salary: '$90k - $130k',
          source: 'LinkedIn',
          date_posted: '1 week ago',
          url: 'https://example.com/job/2',
          saved_at: '2025-10-29',
        },
      ];

      setSavedJobs(mockRows);
    } catch (err) {
      console.error('Failed to fetch saved jobs:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleUnsave = async (jobId: number) => {
    // TODO: call backend or Supabase to remove saved job for the user
    setSavedJobs((rows) => rows.filter((j) => j.id !== jobId));
  };

  // Not signed in
  if (!userEmail && !loading) {
    return (
      <main className="max-w-4xl mx-auto px-4 py-8">
        <div className="text-center py-12">
          <h1 className="text-2xl font-bold mb-3">Sign in required</h1>
          <p className="opacity-80 mb-6">Please sign in to view your saved jobs.</p>
          <Link
            href="/magic-login"
            className="inline-block bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-3 rounded font-medium"
          >
            Sign in
          </Link>
        </div>
      </main>
    );
  }

  return (
    <main className="max-w-6xl mx-auto px-4 py-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">Saved Jobs</h1>
        <p className="opacity-80">
          {savedJobs.length} {savedJobs.length === 1 ? 'job' : 'jobs'} saved
        </p>
      </div>

      {loading ? (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-gray-200 border-t-indigo-600" />
          <p className="mt-2 opacity-80">Loading saved jobs…</p>
        </div>
      ) : savedJobs.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <p className="opacity-80 mb-4">You haven’t saved any jobs yet.</p>
          <Link
            href="/jobs"
            className="inline-block text-indigo-600 hover:text-indigo-700 font-medium"
          >
            Browse Jobs →
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          {savedJobs.map((job) => (
            // `key` is a special React prop (not part of JobCardProps), so it’s fine here.
            <div key={job.id} className="border rounded-md p-4">
              {/* If you already have a JobCard component, you can swap this block with <JobCard job={job} onSave={() => handleUnsave(job.id)} saved /> */}
              <div className="flex items-start justify-between">
                <div>
                  <h2 className="text-xl font-semibold">{job.title}</h2>
                  <p className="opacity-80">{job.company} • {job.location}</p>
                  {job.salary && <p className="opacity-80">{job.salary}</p>}
                  {job.source && <p className="opacity-60 text-sm">Source: {job.source}</p>}
                </div>
                <div className="flex gap-3">
                  {job.url && (
                    <a
                      href={job.url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-indigo-600 hover:text-indigo-700 font-medium"
                    >
                      View
                    </a>
                  )}
                  <button
                    onClick={() => handleUnsave(job.id)}
                    className="text-red-600 hover:text-red-700 font-medium"
                  >
                    Unsave
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </main>
  );
}
