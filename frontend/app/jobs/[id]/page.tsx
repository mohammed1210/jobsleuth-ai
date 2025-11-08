// Job detail page with sticky actions

'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { featureFlags } from '@/lib/flags';

interface Job {
  id: string;
  title: string;
  company: string;
  location?: string;
  salary_min?: number;
  salary_max?: number;
  salary_text?: string;
  type?: string;
  url: string;
  posted_at?: string;
  raw?: {
    description?: string;
    skills?: string[];
  };
}

interface FitScore {
  fit_score: number;
  factors: Array<{
    name: string;
    score: number;
    weight: number;
  }>;
  method: string;
}

export default function JobDetailPage() {
  const params = useParams();
  const jobId = params.id as string;
  const [job, setJob] = useState<Job | null>(null);
  const [loading, setLoading] = useState(true);
  const [fitScore, setFitScore] = useState<FitScore | null>(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    fetchJob();
  }, [jobId]);

  const fetchJob = async () => {
    try {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
      const response = await fetch(`${backendUrl}/jobs/${jobId}`);
      const data = await response.json();
      setJob(data);

      // Fetch AI fit score if enabled
      if (featureFlags.aifit) {
        fetchFitScore(data);
      }
    } catch (error) {
      console.error('Failed to fetch job:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchFitScore = async (jobData: Job) => {
    try {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
      const response = await fetch(`${backendUrl}/score`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ job: jobData }),
      });
      const data = await response.json();
      setFitScore(data);
    } catch (error) {
      console.error('Failed to fetch fit score:', error);
    }
  };

  const handleSave = async () => {
    try {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
      const token = localStorage.getItem('supabase_token');

      if (!token) {
        alert('Please sign in to save jobs');
        return;
      }

      await fetch(`${backendUrl}/saved-jobs/save-job`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ job_id: jobId }),
      });

      setSaved(true);
      alert('Job saved!');
    } catch (error) {
      console.error('Failed to save job:', error);
      alert('Failed to save job. Please try again.');
    }
  };

  const handleShare = () => {
    if (navigator.share) {
      navigator.share({
        title: job?.title,
        text: `Check out this job: ${job?.title} at ${job?.company}`,
        url: window.location.href,
      });
    } else {
      navigator.clipboard.writeText(window.location.href);
      alert('Link copied to clipboard!');
    }
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-6 py-12 text-center">
        <p className="text-gray-500">Loading job details...</p>
      </div>
    );
  }

  if (!job) {
    return (
      <div className="max-w-4xl mx-auto px-6 py-12 text-center">
        <p className="text-gray-500">Job not found</p>
        <Link href="/jobs" className="text-blue-600 hover:underline mt-4 inline-block">
          Back to jobs
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-6 py-8">
      <Link href="/jobs" className="text-blue-600 hover:underline mb-6 inline-block">
        ← Back to jobs
      </Link>

      <div className="grid lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2">
          <h1 className="text-4xl font-bold mb-2">{job.title}</h1>
          <h2 className="text-2xl text-gray-600 mb-4">{job.company}</h2>

          <div className="flex flex-wrap gap-3 mb-6">
            {job.location && (
              <span className="px-3 py-1 bg-gray-100 rounded-full text-sm">📍 {job.location}</span>
            )}
            {job.type && (
              <span className="px-3 py-1 bg-gray-100 rounded-full text-sm">💼 {job.type}</span>
            )}
            {job.salary_text && (
              <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm">
                💰 {job.salary_text}
              </span>
            )}
          </div>

          {job.raw?.description && (
            <div className="prose max-w-none mb-8">
              <h3 className="text-xl font-semibold mb-3">Job Description</h3>
              <p className="whitespace-pre-wrap text-gray-700">{job.raw.description}</p>
            </div>
          )}

          {job.raw?.skills && job.raw.skills.length > 0 && (
            <div className="mb-8">
              <h3 className="text-xl font-semibold mb-3">Required Skills</h3>
              <div className="flex flex-wrap gap-2">
                {job.raw.skills.map((skill, idx) => (
                  <span key={idx} className="px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-sm">
                    {skill}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="lg:col-span-1">
          <div className="sticky top-4 space-y-4">
            <div className="border rounded-lg p-6 space-y-3">
              <button
                onClick={handleSave}
                disabled={saved}
                className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
                aria-label={saved ? 'Job saved' : 'Save job'}
              >
                {saved ? '✓ Saved' : '⭐ Save Job'}
              </button>
              <button
                onClick={handleShare}
                className="w-full px-6 py-3 border border-gray-300 rounded-lg font-semibold hover:bg-gray-50 transition"
                aria-label="Share job"
              >
                🔗 Share
              </button>
              <a
                href={job.url}
                target="_blank"
                rel="noopener noreferrer"
                className="block w-full px-6 py-3 bg-green-600 text-white text-center rounded-lg font-semibold hover:bg-green-700 transition"
              >
                Apply Now →
              </a>
            </div>

            {featureFlags.aifit && fitScore && (
              <div className="border rounded-lg p-6">
                <h3 className="text-lg font-semibold mb-3">AI Fit Score</h3>
                <div className="text-center mb-4">
                  <div className="text-5xl font-bold text-blue-600">{fitScore.fit_score}</div>
                  <div className="text-sm text-gray-500">out of 100</div>
                </div>
                <div className="space-y-2">
                  {fitScore.factors.map((factor, idx) => (
                    <div key={idx} className="text-sm">
                      <div className="flex justify-between mb-1">
                        <span className="text-gray-700">{factor.name}</span>
                        <span className="font-medium">{Math.round(factor.score * 100)}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full"
                          style={{ width: `${factor.score * 100}%` }}
                        ></div>
                      </div>
                    </div>
                  ))}
                </div>
                <p className="text-xs text-gray-500 mt-3">Method: {fitScore.method}</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
