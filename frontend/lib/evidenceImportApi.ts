import type { Session } from '@supabase/supabase-js';

import { apiError, getBackendUrl } from '@/lib/backendConfig';
import { prepareEvidenceUpload } from '@/lib/evidenceImportUpload';

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
  source_index: number;
};

export async function importEvidenceDocument(
  session: Session,
  file: File,
): Promise<EvidenceImportResponse> {
  const upload = await prepareEvidenceUpload(file);
  const form = new FormData();
  form.append('file', upload.blob, upload.filename);

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
