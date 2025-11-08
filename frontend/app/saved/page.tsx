// Saved jobs page - shows user's saved jobs

'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import JobCard from '@/components/JobCard';

interface SavedJob {
  id: string;
  created_at: string;
  jobs: {
    id: string;
    title: string;
    company: string;
    location?: string;
    salary_text?: string;
    type?: string;
    url: string;
  };
}

export default function SavedJobsPage() {
  const [savedJobs, setSavedJobs] = useState<SavedJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchSavedJobs();
  }, []);

  const fetchSavedJobs = async () => {
    try {
      const token = localStorage.getItem('supabase_token');

      if (!token) {
        setError('Please sign in to view saved jobs');
        setLoading(false);
        return;
      }

      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
      const response = await fetch(`${backendUrl}/saved-jobs`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch saved jobs');
      }

      const data = await response.json();
      setSavedJobs(data.jobs || []);
    } catch (err) {
      console.error('Failed to fetch saved jobs:', err);
      setError('Failed to load saved jobs');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto px-6 py-12 text-center">
        <p className="text-gray-500">Loading saved jobs...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-6xl mx-auto px-6 py-12 text-center">
        <p className="text-red-600 mb-4">{error}</p>
        <Link href="/account" className="text-blue-600 hover:underline">
          Go to Account
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-6 py-8">
      <h1 className="text-4xl font-bold mb-8">Saved Jobs</h1>

      {savedJobs.length === 0 ? (
        <div className="text-center py-12 border rounded-lg">
          <p className="text-gray-500 mb-4">You haven't saved any jobs yet</p>
          <Link
            href="/jobs"
            className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition"
          >
            Browse Jobs
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          {savedJobs.map(savedJob => (
            <JobCard
              key={savedJob.id}
              job={{
                ...savedJob.jobs,
                id: savedJob.jobs.id,
              }}
            />
          ))}
        </div>
      )}
    </div>
  );
}
