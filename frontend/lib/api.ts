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