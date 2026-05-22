'use client';

import { FormEvent, useState } from 'react';
import Link from 'next/link';
import HeaderClient from '@/components/HeaderClient';
import { getSupabaseClient } from '@/lib/supabaseClient';
import { Mail } from 'lucide-react';

function getSiteUrl() {
  if (typeof window !== 'undefined') return window.location.origin;
  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || process.env.NEXT_PUBLIC_VERCEL_URL;
  if (!siteUrl) return 'http://localhost:3000';
  return siteUrl.startsWith('http') ? siteUrl : `https://${siteUrl}`;
}

export default function MagicLoginPage() {
  const [email, setEmail] = useState('');
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleLogin(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const supabase = getSupabaseClient();
      const { error } = await supabase.auth.signInWithOtp({
        email,
        options: { emailRedirectTo: `${getSiteUrl()}/auth/callback?returnTo=/account` },
      });
      if (error) throw error;
      setSent(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not send magic link');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen">
      <HeaderClient />
      <main className="mx-auto max-w-md px-4 py-12 sm:px-6">
        <div className="card p-8">
          <div className="mb-6 flex h-12 w-12 items-center justify-center rounded-lg bg-cyan-50 text-cyan-700"><Mail className="h-6 w-6" /></div>
          <h1 className="text-2xl font-bold text-slate-950">Magic link login</h1>
          <p className="mt-2 text-slate-600">Enter your email and JobSleuth will send a secure sign-in link.</p>

          {sent ? (
            <div className="mt-6 rounded-md border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800">Email sent to {email}. Check your inbox.</div>
          ) : (
            <form onSubmit={handleLogin} className="mt-6 space-y-4">
              <input type="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="you@example.com" required className="input-modern" />
              <button type="submit" disabled={loading} className="btn-primary w-full disabled:opacity-60">{loading ? 'Sending...' : 'Send magic link'}</button>
            </form>
          )}

          {error && <div className="mt-4 rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div>}
          <Link href="/" className="mt-6 inline-flex text-sm font-semibold text-cyan-700 hover:text-cyan-800">Back to home</Link>
        </div>
      </main>
    </div>
  );
}
