import type { Session } from '@supabase/supabase-js';

export type Job = {
  id: number;
  title: string;
  company: string;
  location: string;
  salary?: string | null;
  salary_min?: number | null;
  salary_max?: number | null;
  role_type?: string | null;
  url?: string | null;
  source?: string | null;
  date_posted?: string | null;
  description?: string | null;
  ai_score?: number | null;
};

export type SavedJob = {
  id: number;
  user_id: string;
  job_id: number;
  saved_at: string;
  job?: Job | null;
};

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

export const fallbackJobs: Job[] = [
  {
    id: 1,
    title: 'Senior Software Engineer',
    company: 'Northstar Labs',
    location: 'Remote',
    salary: '$140k - $180k',
    salary_min: 140000,
    salary_max: 180000,
    role_type: 'Remote',
    source: 'JobSleuth seed',
    date_posted: '2 days ago',
    url: 'https://example.com/jobs/1',
    ai_score: 0.88,
  },
  {
    id: 2,
    title: 'Product Manager, AI Tools',
    company: 'SignalWorks',
    location: 'New York, NY',
    salary: '$125k - $165k',
    salary_min: 125000,
    salary_max: 165000,
    role_type: 'Hybrid',
    source: 'LinkedIn',
    date_posted: '4 days ago',
    url: 'https://example.com/jobs/2',
    ai_score: 0.81,
  },
  {
    id: 3,
    title: 'Frontend Engineer',
    company: 'Cedar Systems',
    location: 'Austin, TX',
    salary: '$105k - $145k',
    salary_min: 105000,
    salary_max: 145000,
    role_type: 'Full-time',
    source: 'Indeed',
    date_posted: '1 week ago',
    url: 'https://example.com/jobs/3',
    ai_score: 0.76,
  },
];

export async function fetchJobs(params: Record<string, string>) {
  const query = new URLSearchParams(params);
  const response = await fetch(`${BACKEND_URL}/jobs?${query.toString()}`, { cache: 'no-store' });
  if (!response.ok) throw new Error('Failed to fetch jobs');
  return response.json() as Promise<{ jobs: Job[]; total: number; page: number; per_page: number }>;
}

export async function fetchSavedJobs(session: Session) {
  const response = await fetch(`${BACKEND_URL}/saved-jobs`, {
    headers: { Authorization: `Bearer ${session.access_token}` },
    cache: 'no-store',
  });
  if (!response.ok) throw new Error('Failed to fetch saved jobs');
  return response.json() as Promise<SavedJob[]>;
}

export async function saveJob(jobId: number, session: Session) {
  const response = await fetch(`${BACKEND_URL}/saved-jobs`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${session.access_token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ job_id: jobId }),
  });
  if (!response.ok) throw new Error('Failed to save job');
  return response.json();
}

export async function deleteSavedJob(jobId: number, session: Session) {
  const response = await fetch(`${BACKEND_URL}/saved-jobs/${jobId}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${session.access_token}` },
  });
  if (!response.ok) throw new Error('Failed to remove saved job');
  return response.json();
}