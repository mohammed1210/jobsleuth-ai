export const MAX_EVIDENCE_IMPORT_BYTES = 5 * 1024 * 1024;

export type EvidenceUploadSource = Pick<File, 'name' | 'size' | 'type' | 'arrayBuffer'>;

export async function prepareEvidenceUpload(source: EvidenceUploadSource): Promise<{ blob: Blob; filename: string }> {
  if (source.size <= 0) {
    throw new Error('The selected application file is empty.');
  }
  if (source.size > MAX_EVIDENCE_IMPORT_BYTES) {
    throw new Error('Application files must be 5 MB or smaller.');
  }

  let bytes: ArrayBuffer;
  try {
    bytes = await source.arrayBuffer();
  } catch {
    throw new Error(
      'JobSleuth could not read the selected file from your device. Save a local copy of the file, choose it again, and retry.',
    );
  }

  if (!bytes.byteLength) {
    throw new Error('The selected application file is empty.');
  }

  return {
    blob: new Blob([bytes], { type: source.type || 'application/octet-stream' }),
    filename: source.name,
  };
}
