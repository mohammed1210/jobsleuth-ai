'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Bookmark, Building2, ExternalLink, MapPin, Sparkles } from 'lucide-react';
import type { Job } from '@/lib/api';

export interface JobCardProps {
  job: Job;
  onSave?: (jobId: number) => Promise<void> | void;
  saved?: boolean;
  aiScore?: number;
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

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 's' || e.key === 'S') {
      e.preventDefault();
      void handleSave(e as unknown as React.MouseEvent);
    }
  };

  const score = aiScore ?? job.ai_score ?? undefined;

  return (
    <div 
      className="card card-hover group relative p-5 sm:p-6"
      tabIndex={0}
      onKeyDown={handleKeyDown}
      role="article"
      aria-label={`Job posting: ${job.title} at ${job.company}`}
    >
      {score !== undefined && score > 0 && (
        <div className="absolute right-4 top-4">
          <div className="ai-badge gap-1.5"><Sparkles className="h-3.5 w-3.5" />{Math.round(score * 100)}% match</div>
        </div>
      )}

      <div className="mb-4 flex items-start justify-between gap-4 pr-20">
        <div className="min-w-0 flex-1">
          <Link 
            href={`/jobs/${job.id}`}
            className="mb-1 block text-xl font-bold leading-tight text-slate-950 hover:text-cyan-700"
          >
            {job.title}
          </Link>
          <p className="inline-flex items-center gap-1.5 text-sm font-medium text-slate-600"><Building2 className="h-4 w-4" />{job.company}</p>
        </div>
        <button
          onClick={handleSave}
          disabled={saving}
          className={`rounded-lg p-2 transition-all ${
            isSaved 
              ? 'bg-emerald-100 text-emerald-700 hover:bg-emerald-200' 
              : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
          } ${saving ? 'opacity-50 cursor-wait' : ''}`}
          aria-label={isSaved ? 'Unsave job' : 'Save job'}
          title={isSaved ? 'Unsave job' : 'Save job'}
        >
          <Bookmark className="h-5 w-5" fill={isSaved ? 'currentColor' : 'none'} />
        </button>
      </div>
      
      <div className="mb-3 flex flex-wrap gap-2">
        <span className="inline-flex items-center rounded-md bg-slate-100 px-3 py-1.5 text-sm font-medium text-slate-700">
          <MapPin className="mr-1.5 h-4 w-4" />
          {job.location}
        </span>
        {job.role_type && <span className="inline-flex items-center rounded-md bg-cyan-50 px-3 py-1.5 text-sm font-medium text-cyan-700">{job.role_type}</span>}
        {job.salary && (
          <span className="inline-flex items-center rounded-md bg-emerald-50 px-3 py-1.5 text-sm font-medium text-emerald-700">
            {job.salary}
          </span>
        )}
        {job.source && (
          <span className="inline-flex items-center rounded-md bg-slate-100 px-3 py-1.5 text-sm font-medium text-slate-600">
            {job.source}
          </span>
        )}
      </div>
      
      {job.date_posted && (
        <p className="mb-4 text-sm text-slate-500">
          Posted {job.date_posted}
        </p>
      )}
      
      <div className="flex items-center gap-3 border-t border-slate-100 pt-4">
        <Link
          href={`/jobs/${job.id}`}
          className="text-sm font-semibold text-cyan-700 hover:text-cyan-800"
        >
          View details
        </Link>
        {job.url && (
          <a
            href={job.url}
            target="_blank"
            rel="noopener noreferrer"
            className="ml-auto inline-flex items-center gap-1.5 rounded-md bg-slate-950 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800"
            onClick={(e) => e.stopPropagation()}
          >
            Apply
            <ExternalLink className="h-4 w-4" />
          </a>
        )}
      </div>
    </div>
  );
}
