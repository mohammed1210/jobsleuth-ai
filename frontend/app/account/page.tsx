'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import HeaderClient from '@/components/HeaderClient';
import StripePortalButton from '@/components/StripePortalButton';
import { getSupabaseClient, isSupabaseConfigured } from '@/lib/supabaseClient';
import { BriefcaseBusiness, Loader2, UserRound } from 'lucide-react';

export default function AccountPage() {
  const [email, setEmail] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [configured, setConfigured] = useState(true);

  useEffect(() => {
    async function load() {
      if (!isSupabaseConfigured()) {
        setConfigured(false);
        setLoading(false);
        return;
      }
      const supabase = getSupabaseClient();
      const { data } = await supabase.auth.getSession();
      setEmail(data.session?.user.email ?? null);
      setLoading(false);
    }
    load();
  }, []);

  async function signOut() {
    if (!isSupabaseConfigured()) return;
    await getSupabaseClient().auth.signOut();
    setEmail(null);
  }

  return (
    <div className="min-h-screen">
      <HeaderClient />
      <main className="mx-auto max-w-4xl px-4 py-10 sm:px-6">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-950">Account</h1>
          <p className="mt-2 text-slate-600">Manage sign-in, subscription status, and billing.</p>
        </div>
        {loading ? (
          <div className="card p-10 text-center"><Loader2 className="mx-auto h-8 w-8 animate-spin text-cyan-700" /><p className="mt-3 text-slate-600">Loading account...</p></div>
        ) : !configured ? (
          <div className="card p-8"><h2 className="text-xl font-bold text-slate-950">Supabase not configured</h2><p className="mt-2 text-slate-600">Add frontend Supabase env vars to enable magic-link auth.</p></div>
        ) : email ? (
          <div className="space-y-6">
            <section className="card p-6">
              <div className="flex items-start justify-between gap-4">
                <div><div className="text-sm font-medium text-slate-500">Signed in as</div><div className="mt-1 text-lg font-bold text-slate-950">{email}</div><div className="mt-3 inline-flex rounded-full bg-slate-100 px-3 py-1 text-sm font-semibold text-slate-700">Free plan placeholder</div></div>
                <UserRound className="h-8 w-8 text-cyan-700" />
              </div>
            </section>
            <section className="card p-6">
              <h2 className="text-xl font-bold text-slate-950">Billing</h2>
              <p className="mt-2 text-sm text-slate-600">Stripe portal integration is wired and returns a safe response when Stripe is not configured.</p>
              <div className="mt-5"><StripePortalButton>Manage billing</StripePortalButton></div>
            </section>
            <section className="grid gap-4 sm:grid-cols-2">
              <Link href="/saved" className="card flex items-center gap-3 p-5 font-semibold text-slate-800 hover:bg-slate-50"><BriefcaseBusiness className="h-5 w-5 text-cyan-700" />Saved jobs</Link>
              <button onClick={signOut} className="card p-5 text-left font-semibold text-red-700 hover:bg-red-50">Sign out</button>
            </section>
          </div>
        ) : (
          <div className="card p-10 text-center"><h2 className="text-2xl font-bold text-slate-950">Sign in to manage your account</h2><p className="mt-3 text-slate-600">Magic-link auth keeps this simple and passwordless.</p><Link href="/magic-login" className="btn-primary mt-6 inline-flex">Send magic link</Link></div>
        )}
      </main>
    </div>
  );
}
