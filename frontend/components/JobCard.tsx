'use client';

import { useState } from 'react';
import Link from 'next/link';

export interface JobCardProps {
  job: {
    id: number;
    title: string;
    company: string;
    location: string;
    salary?: string | null;
    url?: string;
    source?: string;
    date_posted?: string | null;
  };
  onSave?: (jobId: number) => void;
  saved?: boolean;
}

export default function JobCard({ job, onSave, saved = false }: JobCardProps) {
  const [isSaved, setIsSaved] = useState(saved);
  const [saving, setSaving] = useState(false);

  const handleSave = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (saving) return;
    
    setSaving(true);
    setIsSaved(!isSaved);
    
    if (onSave) {
      await onSave(job.id);
    }
    
    setSaving(false);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 's' || e.key === 'S') {
      e.preventDefault();
      handleSave(e as any);
    }
  };

  return (
    <div 
      className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow relative"
      tabIndex={0}
      onKeyPress={handleKeyPress}
      role="article"
      aria-label={`Job posting: ${job.title} at ${job.company}`}
    >
      <div className="flex justify-between items-start mb-2">
        <div className="flex-1">
          <Link 
            href={`/jobs/${job.id}`}
            className="text-xl font-semibold text-gray-900 hover:text-indigo-600"
          >
            {job.title}
          </Link>
        </div>
        <button
          onClick={handleSave}
          disabled={saving}
          className={`ml-4 px-3 py-1 rounded text-sm font-medium transition-colors ${
            isSaved 
              ? 'bg-indigo-600 text-white hover:bg-indigo-700' 
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          } ${saving ? 'opacity-50 cursor-wait' : ''}`}
          aria-label={isSaved ? 'Unsave job' : 'Save job'}
          title="Press 's' to save"
        >
          {saving ? '...' : isSaved ? '✓ Saved' : 'Save'}
        </button>
      </div>
      
      <div className="space-y-1 mb-3">
        <p className="text-gray-700 font-medium">{job.company}</p>
        <div className="flex flex-wrap gap-2">
          <span className="inline-flex items-center px-2 py-1 bg-gray-100 text-gray-700 text-sm rounded">
            📍 {job.location}
          </span>
          {job.salary && (
            <span className="inline-flex items-center px-2 py-1 bg-green-100 text-green-700 text-sm rounded">
              💰 {job.salary}
            </span>
          )}
          {job.source && (
            <span className="inline-flex items-center px-2 py-1 bg-blue-100 text-blue-700 text-sm rounded">
              {job.source}
            </span>
          )}
        </div>
      </div>
      
      {job.date_posted && (
        <p className="text-sm text-gray-500">
          Posted: {job.date_posted}
        </p>
      )}
      
      <div className="mt-3 flex gap-2">
        <Link
          href={`/jobs/${job.id}`}
          className="text-indigo-600 hover:text-indigo-700 text-sm font-medium"
        >
          View Details →
        </Link>
        {job.url && (
          <a
            href={job.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-gray-600 hover:text-gray-700 text-sm font-medium"
            onClick={(e) => e.stopPropagation()}
          >
            Apply ↗
          </a>
        )}
      </div>
    </div>
  );
}
