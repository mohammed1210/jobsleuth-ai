import type { Session } from '@supabase/supabase-js';

import { apiError, getBackendUrl } from '@/lib/backendConfig';

export type EvidenceImportDraft = {
  title: string;
  situation: string;
  task: string;
  actions: string[];
  outcome: string;
  reflection: string;
  tags: string[];
  behaviours: string[];
  skills: string[];
  authority_context?: string | null;
  confidence: number;
  source_excerpt: string;
};

export type EvidenceImportResponse = {
  source_filename: string;
  extraction_provider: string;
  drafts: EvidenceImportDraft[];
};

export type EvidenceImportSuggestion = EvidenceImportDraft & {
  source_filename: string;
};

export async function importEvidenceDocument(
  session: Session,
  file: File,
): Promise<EvidenceImportResponse> {
  const form = new FormData();
  form.append('file', file);

  const response = await fetch(`${getBackendUrl()}/evidence/import`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${session.access_token}`,
    },
    body: form,
  });

  if (!response.ok) throw await apiError(response, 'Could not extract evidence from this application');
  return response.json();
}
