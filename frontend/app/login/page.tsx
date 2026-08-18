'use client';

import Link from 'next/link';
import { FormEvent, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

import HeaderClient from '@/components/HeaderClient';
import { getSupabaseClient, isSupabaseConfigured } from '@/lib/supabaseClient';

type Mode = 'sign-in' | 'sign-up';

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<Mode>('sign-in');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isSupabaseConfigured()) return;
    const supabase = getSupabaseClient();
    void supabase.auth.getSession().then(({ data }) => {
      if (data.session) router.replace('/apply/vacancy');
    });
  }, [router]);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    setMessage(null);

    if (!isSupabaseConfigured()) {
      setError('Authentication is not configured.');
      return;
    }
    if (password.length < 8) {
      setError('Use a password with at least 8 characters.');
      return;
    }
    if (mode === 'sign-up' && password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setLoading(true);
    try {
      const supabase = getSupabaseClient();
      if (mode === 'sign-in') {
        const { data, error: authError } = await supabase.auth.signInWithPassword({ email, password });
        if (authError) throw authError;
        if (!data.session) throw new Error('Sign in did not create a session.');
        router.replace('/apply/vacancy');
        router.refresh();
        return;
      }

      const { data, error: authError } = await supabase.auth.signUp({ email, password });
      if (authError) throw authError;
      if (data.session) {
        router.replace('/apply/vacancy');
        router.refresh();
      } else {
        setMessage('Account created. If email confirmation is enabled for this project, confirm your address before signing in.');
        setMode('sign-in');
        setConfirmPassword('');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Authentication failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen">
      <HeaderClient />
      <main className="mx-auto max-w-md px-6 py-16">
        <div className="card p-8 md:p-10">
          <div className="mb-8 text-center">
            <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-ai shadow-glow">
              <span className="text-xl font-bold text-white">JS</span>
            </div>
            <h1 className="text-3xl font-bold text-gray-900">{mode === 'sign-in' ? 'Welcome back' : 'Create your account'}</h1>
            <p className="mt-2 text-gray-600">{mode === 'sign-in' ? 'Sign in with your email and password.' : 'Create a password so normal sign-in does not depend on an email link.'}</p>
          </div>

          <div className="mb-6 grid grid-cols-2 rounded-xl bg-gray-100 p-1">
            <button type="button" onClick={() => { setMode('sign-in'); setError(null); setMessage(null); }} className={`rounded-lg px-3 py-2 text-sm font-semibold ${mode === 'sign-in' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-600'}`}>Sign in</button>
            <button type="button" onClick={() => { setMode('sign-up'); setError(null); setMessage(null); }} className={`rounded-lg px-3 py-2 text-sm font-semibold ${mode === 'sign-up' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-600'}`}>Create account</button>
          </div>

          <form onSubmit={submit} className="space-y-5">
            <label className="block text-sm font-semibold text-gray-700">
              Email address
              <input type="email" value={email} onChange={(event) => setEmail(event.target.value)} autoComplete="email" required disabled={loading} className="input-modern mt-2" placeholder="you@example.com" />
            </label>

            <label className="block text-sm font-semibold text-gray-700">
              Password
              <div className="relative mt-2">
                <input type={showPassword ? 'text' : 'password'} value={password} onChange={(event) => setPassword(event.target.value)} autoComplete={mode === 'sign-in' ? 'current-password' : 'new-password'} minLength={8} required disabled={loading} className="input-modern pr-20" placeholder="At least 8 characters" />
                <button type="button" onClick={() => setShowPassword((value) => !value)} className="absolute right-3 top-1/2 -translate-y-1/2 text-sm font-semibold text-brand-600">{showPassword ? 'Hide' : 'Show'}</button>
              </div>
            </label>

            {mode === 'sign-up' && (
              <label className="block text-sm font-semibold text-gray-700">
                Confirm password
                <input type={showPassword ? 'text' : 'password'} value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} autoComplete="new-password" minLength={8} required disabled={loading} className="input-modern mt-2" />
              </label>
            )}

            {error && <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">{error}</div>}
            {message && <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800">{message}</div>}

            <button type="submit" disabled={loading} className="btn-primary w-full disabled:opacity-50">{loading ? 'Please wait…' : mode === 'sign-in' ? 'Sign in' : 'Create account'}</button>
          </form>

          <div className="mt-7 border-t pt-5 text-sm text-gray-600">
            <p>Already signed in through an older magic-link session? <Link href="/account/password" className="font-semibold text-brand-600">Set a password on that account</Link>.</p>
            <p className="mt-3"><Link href="/" className="font-medium text-brand-600">← Back to Home</Link></p>
          </div>
        </div>
      </main>
    </div>
  );
}
