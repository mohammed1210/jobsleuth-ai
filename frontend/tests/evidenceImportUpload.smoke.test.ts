import test from 'node:test';
import assert from 'node:assert/strict';

import { MAX_EVIDENCE_IMPORT_BYTES, prepareEvidenceUpload } from '../lib/evidenceImportUpload';

test('evidence import buffers the selected file before fetch', async () => {
  let reads = 0;
  const bytes = new TextEncoder().encode('example application').buffer;
  const upload = await prepareEvidenceUpload({
    name: 'Operation manager.docx',
    size: bytes.byteLength,
    type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    async arrayBuffer() {
      reads += 1;
      return bytes;
    },
  });

  assert.equal(reads, 1);
  assert.equal(upload.filename, 'Operation manager.docx');
  assert.equal(upload.blob.size, bytes.byteLength);
});

test('evidence import reports device file-read failures clearly', async () => {
  await assert.rejects(
    () => prepareEvidenceUpload({
      name: 'Operation manager.docx',
      size: 123,
      type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      async arrayBuffer() {
        throw new Error('ERR_UPLOAD_FILE_CHANGED');
      },
    }),
    /could not read the selected file from your device/i,
  );
});

test('evidence import rejects files over the advertised 5 MB limit before fetch', async () => {
  await assert.rejects(
    () => prepareEvidenceUpload({
      name: 'large.docx',
      size: MAX_EVIDENCE_IMPORT_BYTES + 1,
      type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      async arrayBuffer() {
        return new ArrayBuffer(1);
      },
    }),
    /5 MB or smaller/i,
  );
});
