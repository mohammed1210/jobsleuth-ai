// Account page for JobSleuth AI
'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { createClient } from '@supabase/supabase-js';
import { featureFlags } from '@/lib/flags';

export default function AccountPage() {
  const [userEmail, setUserEmail] = useState<string | null>(null);
  const [userPlan, setUserPlan] = useState<string>('free');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadUserData();
  }, []);

  const loadUserData = async () => {
    try {
      const supabase = createClient(
        process.env.NEXT_PUBLIC_SUPABASE_URL as string,
        process.env.NEXT_PUBLIC_SUPABASE_KEY as string
      );

      const { data } = await supabase.auth.getUser();
      setUserEmail(data.user?.email ?? null);

      if (data.user?.email) {
        // Fetch user plan from backend
        const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
        const response = await fetch(`${backendUrl}/users/plan?email=${data.user.email}`);
        const planData = await response.json();
        setUserPlan(planData.plan || 'free');
      }
    } catch (error) {
      console.error('Failed to load user data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSignIn = async () => {
    const supabase = createClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL as string,
      process.env.NEXT_PUBLIC_SUPABASE_KEY as string
    );

    const email = prompt('Enter your email for magic link sign-in:');
    if (!email) return;

    try {
      await supabase.auth.signInWithOtp({
        email,
        options: {
          emailRedirectTo: `${window.location.origin}/auth/callback`,
        },
      });
      alert('Check your email for the magic link!');
    } catch (error) {
      console.error('Sign in failed:', error);
      alert('Failed to send magic link. Please try again.');
    }
  };

  const handleSignOut = async () => {
    const supabase = createClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL as string,
      process.env.NEXT_PUBLIC_SUPABASE_KEY as string
    );

    await supabase.auth.signOut();
    setUserEmail(null);
    setUserPlan('free');
    localStorage.removeItem('supabase_token');
  };

  const getPlanBadgeClass = (plan: string) => {
    switch (plan) {
      case 'pro':
        return 'bg-blue-100 text-blue-800';
      case 'investor':
        return 'bg-purple-100 text-purple-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <main className="max-w-3xl mx-auto px-6 py-12">
        <p className="text-gray-500">Loading account...</p>
      </main>
    );
  }

  return (
    <main className="max-w-3xl mx-auto px-6 py-12 space-y-8">
      <h1 className="text-4xl font-bold">Account</h1>

      {userEmail ? (
        <>
          <section className="border rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Profile</h2>
            <div className="space-y-2">
              <p className="text-gray-600">
                <span className="font-medium">Email:</span> {userEmail}
              </p>
              <div className="flex items-center gap-2">
                <span className="font-medium text-gray-600">Plan:</span>
                <span className={`px-3 py-1 rounded-full text-sm font-semibold ${getPlanBadgeClass(userPlan)}`}>
                  {userPlan.charAt(0).toUpperCase() + userPlan.slice(1)}
                </span>
              </div>
            </div>
          </section>

          <section className="border rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Quick Links</h2>
            <div className="space-y-3">
              <Link
                href="/saved"
                className="block px-4 py-2 text-blue-600 hover:bg-blue-50 rounded transition"
              >
                View Saved Jobs →
              </Link>
              {userPlan === 'free' && (
                <Link
                  href="/pricing"
                  className="block px-4 py-2 text-purple-600 hover:bg-purple-50 rounded transition"
                >
                  Upgrade Plan →
                </Link>
              )}
            </div>
          </section>

          {featureFlags.digests && (
            <section className="border rounded-lg p-6">
              <h2 className="text-xl font-semibold mb-4">Email Digests</h2>
              <p className="text-gray-600 mb-4">
                Get personalized job recommendations delivered to your inbox
              </p>
              <button className="px-4 py-2 border rounded-lg hover:bg-gray-50 transition">
                Manage Digest Settings
              </button>
            </section>
          )}

          <section className="border rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Billing</h2>
            <p className="text-gray-600 mb-4">Manage your subscription and billing information</p>
            <a
              href="/api/stripe/portal"
              className="inline-block px-6 py-2 bg-gray-900 text-white rounded-lg font-semibold hover:bg-gray-800 transition"
            >
              Manage Billing
            </a>
          </section>

          <section>
            <button
              onClick={handleSignOut}
              className="px-6 py-2 text-red-600 border border-red-600 rounded-lg hover:bg-red-50 transition"
            >
              Sign Out
            </button>
          </section>
        </>
      ) : (
        <section className="border rounded-lg p-8 text-center">
          <h2 className="text-2xl font-semibold mb-4">Sign In to Your Account</h2>
          <p className="text-gray-600 mb-6">
            Use magic link authentication - no password required!
          </p>
          <button
            onClick={handleSignIn}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition"
          >
            Sign In with Magic Link
          </button>
          <p className="mt-4 text-sm text-gray-500">
            Don't have an account? It will be created automatically when you sign in.
          </p>
        </section>
      )}
    </main>
  );
}

