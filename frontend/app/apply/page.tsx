'use client';

import HeaderClient from '@/components/HeaderClient';
import RecordForm from '@/components/RecordForm';

export default function ApplyPage() {
  return (
    <div className="min-h-screen">
      <HeaderClient />
      <main className="max-w-6xl mx-auto px-6 py-10 space-y-8">
        <div>
          <p className="text-sm font-semibold text-brand-700 mb-2">JobSleuth Evidence Bank</p>
          <h1 className="text-4xl font-bold text-gray-900">Capture facts once. Reuse them well.</h1>
          <p className="text-gray-600 mt-3">Build a private library of examples that can support vacancy analysis and application drafting.</p>
        </div>
        <RecordForm onSave={async () => {}} />
      </main>
    </div>
  );
}
