import type { Session } from '@supabase/supabase-js';

import { apiError, getBackendUrl } from '@/lib/backendConfig';

export type CandidateExperience = {
  role: string;
  organisation: string;
  dates: string;
  highlights: string[];
  skills: string[];
};

export type CandidateQualification = {
  name: string;
  institution: string;
  date: string;
};

export type CandidateProfile = {
  user_id: string;
  source_filename: string;
  summary: string;
  skills: string[];
  experience: CandidateExperience[];
  qualifications: CandidateQualification[];
  extraction_provider: string;
  updated_at?: string | null;
};

function auth(session: Session) {
  return { Authorization: `Bearer ${session.access_token}` };
}

export async function fetchCandidateProfile(session: Session): Promise<CandidateProfile | null> {
  const response = await fetch(`${getBackendUrl()}/candidate-profile`, {
    headers: auth(session),
    cache: 'no-store',
  });
  if (!response.ok) throw await apiError(response, 'Failed to load CV profile');
  return response.json();
}

export async function uploadCandidateCv(session: Session, file: File): Promise<CandidateProfile> {
  const body = new FormData();
  body.append('file', file);
  const response = await fetch(`${getBackendUrl()}/candidate-profile/cv-upload`, {
    method: 'POST',
    headers: auth(session),
    body,
  });
  if (!response.ok) throw await apiError(response, 'CV upload failed');
  return response.json();
}

export async function deleteCandidateProfile(session: Session): Promise<void> {
  const response = await fetch(`${getBackendUrl()}/candidate-profile`, {
    method: 'DELETE',
    headers: auth(session),
  });
  if (!response.ok) throw await apiError(response, 'Could not remove CV profile');
}
