'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

import HeaderClient from '@/components/HeaderClient';
import { getFreshSession, getSupabaseClient } from '@/lib/supabaseClient';

export default function AccountPage() {
  const router = useRouter();
  const [email, setEmail] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    void getFreshSession().then((session) => {
      setEmail(session?.user.email ?? null);
      setLoading(false);
    });
  }, []);

  const signOut = async () => {
    await getSupabaseClient().auth.signOut();
    router.replace('/login');
    router.refresh();
  };

  return (
    <div className="min-h-screen">
      <HeaderClient />
      <main className="mx-auto max-w-4xl space-y-8 px-6 py-12">
        <div>
          <h1 className="text-4xl font-bold text-gray-900">Your Account</h1>
          <p className="mt-2 text-gray-600">Manage sign-in and account security.</p>
        </div>

        {loading ? (
          <div className="card p-8 text-gray-600">Loading account…</div>
        ) : email ? (
          <>
            <section className="card p-8">
              <h2 className="text-2xl font-bold text-gray-900">Profile</h2>
              <div className="mt-5 rounded-xl bg-gray-50 p-4">
                <p className="text-sm font-medium text-gray-500">Email address</p>
                <p className="mt-1 text-lg font-semibold text-gray-900">{email}</p>
              </div>
            </section>

            <section className="card p-8">
              <h2 className="text-2xl font-bold text-gray-900">Security</h2>
              <p className="mt-2 text-gray-600">Use a password for normal JobSleuth sign-in instead of relying on an emailed magic link.</p>
              <Link href="/account/password" className="btn-primary mt-5 inline-flex">Set or change password</Link>
            </section>

            <section className="card p-8">
              <h2 className="text-2xl font-bold text-gray-900">Subscription</h2>
              <p className="mt-2 text-gray-600">Manage plan options and billing from JobSleuth pricing.</p>
              <Link href="/pricing" className="btn-secondary mt-5 inline-flex">View plans</Link>
            </section>

            <section className="card border-2 border-red-100 p-8">
              <h2 className="text-xl font-bold text-gray-900">Sign out</h2>
              <p className="mt-2 text-sm text-gray-600">You can sign back in with your email and password.</p>
              <button type="button" onClick={signOut} className="mt-5 rounded-xl border-2 border-red-600 px-6 py-3 font-semibold text-red-600 hover:bg-red-50">Sign out</button>
            </section>
          </>
        ) : (
          <div className="card p-10 text-center">
            <h2 className="text-3xl font-bold text-gray-900">Sign in to your account</h2>
            <p className="mx-auto mt-3 max-w-md text-gray-600">Use your JobSleuth email and password.</p>
            <Link href="/login" className="btn-primary mt-6 inline-flex">Sign in</Link>
          </div>
        )}
      </main>
    </div>
  );
}
