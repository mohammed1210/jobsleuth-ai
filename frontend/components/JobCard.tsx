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
  aiScore?: number; // Optional AI score to display
}

export default function JobCard({ job, onSave, saved = false, aiScore }: JobCardProps) {
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
      className="card card-hover p-6 relative group"
      tabIndex={0}
      onKeyPress={handleKeyPress}
      role="article"
      aria-label={`Job posting: ${job.title} at ${job.company}`}
    >
      {/* AI Score Badge */}
      {aiScore !== undefined && aiScore > 0 && (
        <div className="absolute top-4 right-4">
          <div className="ai-badge">
            <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
              <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
            </svg>
            {Math.round(aiScore * 100)}% Match
          </div>
        </div>
      )}

      <div className="flex justify-between items-start mb-4">
        <div className="flex-1 pr-4">
          <Link 
            href={`/jobs/${job.id}`}
            className="text-xl font-bold text-gray-900 hover:text-brand-600 transition-colors line-clamp-2 mb-1 block"
          >
            {job.title}
          </Link>
          <p className="text-lg text-gray-700 font-medium">{job.company}</p>
        </div>
        <button
          onClick={handleSave}
          disabled={saving}
          className={`ml-2 p-2 rounded-lg transition-all duration-200 ${
            isSaved 
              ? 'bg-brand-100 text-brand-600 hover:bg-brand-200' 
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          } ${saving ? 'opacity-50 cursor-wait' : ''}`}
          aria-label={isSaved ? 'Unsave job' : 'Save job'}
          title="Press 's' to save"
        >
          <svg className="w-5 h-5" fill={isSaved ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
          </svg>
        </button>
      </div>
      
      <div className="flex flex-wrap gap-2 mb-3">
        <span className="inline-flex items-center px-3 py-1.5 bg-gray-100 text-gray-700 text-sm font-medium rounded-lg">
          <svg className="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          {job.location}
        </span>
        {job.salary && (
          <span className="inline-flex items-center px-3 py-1.5 bg-emerald-100 text-emerald-700 text-sm font-medium rounded-lg">
            <svg className="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {job.salary}
          </span>
        )}
        {job.source && (
          <span className="inline-flex items-center px-3 py-1.5 bg-blue-100 text-blue-700 text-sm font-medium rounded-lg">
            {job.source}
          </span>
        )}
      </div>
      
      {job.date_posted && (
        <p className="text-sm text-gray-500 mb-4">
          Posted {job.date_posted}
        </p>
      )}
      
      <div className="flex items-center gap-3 pt-4 border-t border-gray-100">
        <Link
          href={`/jobs/${job.id}`}
          className="flex-1 text-center px-4 py-2 bg-brand-600 text-white rounded-lg font-semibold hover:bg-brand-700 transition-colors"
        >
          View Details
        </Link>
        {job.url && (
          <a
            href={job.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center px-4 py-2 border-2 border-gray-300 text-gray-700 rounded-lg font-semibold hover:border-gray-400 hover:bg-gray-50 transition-colors"
            onClick={(e) => e.stopPropagation()}
          >
            Apply
            <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
          </a>
        )}
      </div>
    </div>
  );
}
