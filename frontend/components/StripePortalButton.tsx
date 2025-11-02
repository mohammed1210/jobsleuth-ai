// Stripe portal button component for JobSleuth AI
'use client';
import { useState } from 'react';

interface Props {
  priceId?: string;
  children: React.ReactNode;
}

export default function StripePortalButton({ children }: Props) {
  const [loading, setLoading] = useState(false);

  const handleClick = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/stripe/create-portal-session', { method: 'POST' });
      const data = await res.json();
      if (data.url) {
        window.location.href = data.url;
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      disabled={loading}
      onClick={handleClick}
      className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 disabled:opacity-50"
    >
      {loading ? 'Loading…' : children}
    </button>
  );
}
