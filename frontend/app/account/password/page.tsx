'use client';

import Link from 'next/link';
import { FormEvent, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

import HeaderClient from '@/components/HeaderClient';
import { getFreshSession, getSupabaseClient, isSupabaseConfigured } from '@/lib/supabaseClient';

export default function AccountPasswordPage() {
  const router = useRouter();
  const [ready, setReady] = useState(false);
  const [email, setEmail] = useState<string | null>(null);
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      if (!isSupabaseConfigured()) {
        setError('Authentication is not configured.');
        setReady(true);
        return;
      }
      const session = await getFreshSession();
      setEmail(session?.user.email ?? null);
      setReady(true);
    };
    void load();
  }, []);

  const save = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    setMessage(null);
    if (password.length < 8) {
      setError('Use a password with at least 8 characters.');
      return;
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setSaving(true);
    try {
      const supabase = getSupabaseClient();
      const { error: updateError } = await supabase.auth.updateUser({ password });
      if (updateError) throw updateError;
      setPassword('');
      setConfirmPassword('');
      setMessage('Password saved. You can now sign in with your email and password.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not save your password.');
    } finally {
      setSaving(false);
    }
  };

  if (!ready) {
    return <div className="min-h-screen"><HeaderClient /><main className="mx-auto max-w-xl px-6 py-16"><div className="card p-8">Checking your session…</div></main></div>;
  }

  if (!email) {
    return (
      <div className="min-h-screen">
        <HeaderClient />
        <main className="mx-auto max-w-xl px-6 py-16">
          <div className="card p-8 text-center">
            <h1 className="text-2xl font-bold text-gray-900">Sign in first</h1>
            <p className="mt-3 text-gray-600">Setting a password on an existing account requires an active session.</p>
            <Link href="/login" className="btn-primary mt-6 inline-flex">Go to sign in</Link>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <HeaderClient />
      <main className="mx-auto max-w-xl px-6 py-16">
        <div className="card p-8 md:p-10">
          <h1 className="text-3xl font-bold text-gray-900">Set your JobSleuth password</h1>
          <p className="mt-2 text-gray-600">This upgrades the existing account for <strong>{email}</strong>. Your Evidence Bank and saved data stay on the same user account.</p>

          <form onSubmit={save} className="mt-8 space-y-5">
            <label className="block text-sm font-semibold text-gray-700">
              New password
              <div className="relative mt-2">
                <input type={showPassword ? 'text' : 'password'} value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="new-password" minLength={8} required className="input-modern pr-20" />
                <button type="button" onClick={() => setShowPassword((value) => !value)} className="absolute right-3 top-1/2 -translate-y-1/2 text-sm font-semibold text-brand-600">{showPassword ? 'Hide' : 'Show'}</button>
              </div>
            </label>
            <label className="block text-sm font-semibold text-gray-700">
              Confirm password
              <input type={showPassword ? 'text' : 'password'} value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} autoComplete="new-password" minLength={8} required className="input-modern mt-2" />
            </label>

            {error && <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">{error}</div>}
            {message && <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800">{message}</div>}

            <button type="submit" disabled={saving} className="btn-primary w-full disabled:opacity-50">{saving ? 'Saving…' : 'Save password'}</button>
          </form>

          <div className="mt-6 text-sm"><Link href="/account" className="font-medium text-brand-600">← Back to Account</Link></div>
        </div>
      </main>
    </div>
  );
}
