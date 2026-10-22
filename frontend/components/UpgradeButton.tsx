'use client';

import { useState } from 'react';
import { getFreshSession } from '@/lib/supabaseClient';
import { getBackendUrl } from '@/lib/backendConfig';

type Props = { plan: 'career_plus' | 'pro'; children: React.ReactNode };

export default function UpgradeButton({ plan, children }: Props) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const upgrade = async () => {
    setLoading(true);
    setError(null);
    try {
      const session = await getFreshSession();
      if (!session) {
        setError('Sign in to your JobSleuth account before upgrading.');
        return;
      }
      const response = await fetch(`${getBackendUrl()}/stripe/checkout`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({ plan }),
      });
      if (!response.ok) throw new Error('Checkout is currently unavailable. Please try again later.');
      const result = await response.json();
      if (!result.url) throw new Error('Checkout did not return a payment page.');
      window.location.assign(result.url);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Checkout is currently unavailable.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <button type="button" className="w-full btn-primary" onClick={upgrade} disabled={loading}>
        {loading ? 'Opening checkout…' : children}
      </button>
      {error && <p role="alert" className="mt-2 text-sm text-red-700">{error}</p>}
    </div>
  );
}
