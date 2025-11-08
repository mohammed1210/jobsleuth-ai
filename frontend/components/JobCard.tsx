// JobCard component - displays job summary with prominent Save action

'use client';

import Link from 'next/link';
import { useState } from 'react';

interface JobCardProps {
  job: {
    id: string;
    title: string;
    company: string;
    location?: string;
    salary_min?: number;
    salary_max?: number;
    salary_text?: string;
    type?: string;
    url: string;
  };
}

export default function JobCard({ job }: JobCardProps) {
  const [saved, setSaved] = useState(false);
  const [saving, setSaving] = useState(false);

  const handleSave = async (e: React.MouseEvent) => {
    e.preventDefault(); // Prevent navigation
    setSaving(true);

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
        body: JSON.stringify({ job_id: job.id }),
      });

      setSaved(true);
    } catch (error) {
      console.error('Failed to save job:', error);
      alert('Failed to save job');
    } finally {
      setSaving(false);
    }
  };

  return (
    <article
      className="border rounded-lg p-6 hover:shadow-lg transition-shadow"
      role="article"
      aria-label={`Job posting: ${job.title} at ${job.company}`}
    >
      <div className="flex justify-between items-start gap-4">
        <Link href={`/jobs/${job.id}`} className="flex-1 min-w-0">
          <h3 className="text-xl font-semibold mb-1 hover:text-blue-600 transition truncate">
            {job.title}
          </h3>
          <p className="text-gray-600 mb-3">{job.company}</p>

          <div className="flex flex-wrap gap-2 mb-3">
            {job.location && (
              <span className="px-2 py-1 bg-gray-100 rounded text-sm">📍 {job.location}</span>
            )}
            {job.type && (
              <span className="px-2 py-1 bg-gray-100 rounded text-sm">💼 {job.type}</span>
            )}
            {job.salary_text && (
              <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-sm">
                💰 {job.salary_text}
              </span>
            )}
          </div>
        </Link>

        <button
          onClick={handleSave}
          disabled={saving || saved}
          className="px-4 py-2 border border-blue-600 text-blue-600 rounded-lg font-semibold hover:bg-blue-50 transition disabled:opacity-50 disabled:cursor-not-allowed flex-shrink-0"
          aria-label={saved ? 'Job saved' : 'Save job'}
          tabIndex={0}
        >
          {saved ? '✓ Saved' : saving ? '...' : '⭐ Save'}
        </button>
      </div>

      <div className="flex gap-3 mt-4">
        <Link
          href={`/jobs/${job.id}`}
          className="text-blue-600 hover:underline text-sm font-medium"
        >
          View Details →
        </Link>
        <a
          href={job.url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-green-600 hover:underline text-sm font-medium"
          onClick={e => e.stopPropagation()}
        >
          Apply →
        </a>
      </div>
    </article>
  );
}
