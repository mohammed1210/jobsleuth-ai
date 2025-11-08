/**
 * JobCard Component
 *
 * Displays a job listing card with title, company, location, salary, and save button.
 * Keyboard accessible and supports saving jobs.
 */

'use client';

import Link from 'next/link';
import { useState } from 'react';

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

interface JobCardProps {
  job: Job;
  onSave?: (jobId: string) => void;
  isSaved?: boolean;
}

export default function JobCard({ job, onSave, isSaved = false }: JobCardProps) {
  const [saved, setSaved] = useState(isSaved);
  const [saving, setSaving] = useState(false);

  const handleSave = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();

    if (saving) return;

    setSaving(true);
    try {
      if (onSave) {
        await onSave(job.id);
        setSaved(!saved);
      }
    } finally {
      setSaving(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleSave(e as any);
    }
  };

  const formatSalary = () => {
    if (job.salary_text) return job.salary_text;
    if (job.salary_min && job.salary_max) {
      return `$${(job.salary_min / 1000).toFixed(0)}k - $${(job.salary_max / 1000).toFixed(0)}k`;
    }
    if (job.salary_min) return `$${(job.salary_min / 1000).toFixed(0)}k+`;
    return null;
  };

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return null;
    const date = new Date(dateStr);
    const now = new Date();
    const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
    return `${Math.floor(diffDays / 30)} months ago`;
  };

  const salary = formatSalary();
  const posted = formatDate(job.posted_at);

  return (
    <article className="block bg-white rounded-lg border border-gray-200 hover:border-blue-400 hover:shadow-md transition-all p-5 relative">
      <Link href={`/jobs/${job.id}`} className="block focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded">
        {/* Title and Company */}
        <div className="mb-3">
          <h3 className="text-lg font-semibold text-gray-900 mb-1 hover:text-blue-600">
            {job.title}
          </h3>
          <p className="text-gray-700 font-medium">{job.company}</p>
        </div>

        {/* Metadata Badges */}
        <div className="flex flex-wrap gap-2 mb-3">
          {job.location && (
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
              📍 {job.location}
            </span>
          )}
          {salary && (
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
              💰 {salary}
            </span>
          )}
          {job.type && (
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
              {job.type}
            </span>
          )}
          {posted && (
            <span className="text-xs text-gray-500">{posted}</span>
          )}
        </div>
      </Link>

      {/* Save Button */}
      <button
        onClick={handleSave}
        onKeyDown={handleKeyDown}
        disabled={saving}
        className={`absolute top-4 right-4 p-2 rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 ${
          saved
            ? 'text-red-500 hover:bg-red-50'
            : 'text-gray-400 hover:bg-gray-100 hover:text-gray-600'
        } disabled:opacity-50`}
        aria-label={saved ? 'Unsave job' : 'Save job'}
        title={saved ? 'Unsave job' : 'Save job'}
      >
        <svg
          className="w-6 h-6"
          fill={saved ? 'currentColor' : 'none'}
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"
          />
        </svg>
      </button>
    </article>
  );
}
