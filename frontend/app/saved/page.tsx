/**
 * Saved Jobs Page
 *
 * Display user's saved/bookmarked jobs
 */

'use client';

import { useEffect, useState } from 'react';
import JobCard from '@/components/JobCard';
import Link from 'next/link';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Job {
  id: string;
  title: string;
  company: string;
  location?: string;
  salary_text?: string;
  salary_min?: number;
  salary_max?: number;
  type?: string;
  posted_at?: string;
}

export default function SavedJobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // In a real implementation, this would check for auth and fetch saved jobs
    // For now, show a message
    setLoading(false);
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
          <p className="text-gray-600">Loading saved jobs...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-5xl mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Saved Jobs</h1>
          <p className="text-gray-600">
            Jobs you've bookmarked for later review
          </p>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-800">{error}</p>
          </div>
        )}

        {!error && jobs.length === 0 && (
          <div className="text-center py-16 bg-white rounded-lg border border-gray-200">
            <div className="text-6xl mb-4">🔖</div>
            <h2 className="text-2xl font-semibold text-gray-900 mb-2">
              No Saved Jobs Yet
            </h2>
            <p className="text-gray-600 mb-6">
              Start browsing jobs and save the ones you're interested in
            </p>
            <Link
              href="/jobs"
              className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Browse Jobs
            </Link>
          </div>
        )}

        {jobs.length > 0 && (
          <div className="space-y-4">
            {jobs.map(job => (
              <JobCard key={job.id} job={job} isSaved={true} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
