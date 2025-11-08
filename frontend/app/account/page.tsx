// Account page for JobSleuth AI
'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { createClient } from '@supabase/supabase-js';
import { featureFlags } from '@/lib/flags';
import HeaderClient from '@/components/HeaderClient';

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
        return 'bg-gradient-ai text-white shadow-glow';
      case 'investor':
        return 'bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-lg';
      default:
        return 'bg-gray-200 text-gray-700';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen">
        <HeaderClient />
        <main className="max-w-4xl mx-auto px-6 py-12">
          <div className="text-center py-12">
            <div className="inline-flex items-center justify-center">
              <div className="w-12 h-12 border-4 border-brand-200 border-t-brand-600 rounded-full animate-spin"></div>
            </div>
            <p className="mt-4 text-lg text-gray-600 font-medium">Loading account...</p>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <HeaderClient />
      
      <main className="max-w-4xl mx-auto px-6 py-12 space-y-8">
        <div>
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-3">
            Your <span className="text-gradient">Account</span>
          </h1>
          <p className="text-xl text-gray-600">Manage your profile and subscription</p>
        </div>

        {userEmail ? (
          <>
            {/* Profile Card */}
            <div className="card p-8">
              <div className="flex items-start justify-between mb-6">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900 mb-2">Profile Information</h2>
                  <p className="text-gray-600">Your account details and current plan</p>
                </div>
                <div className="w-16 h-16 bg-gradient-ai rounded-2xl flex items-center justify-center shadow-glow">
                  <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                </div>
              </div>
              
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 bg-gray-50 rounded-xl">
                  <div>
                    <p className="text-sm font-medium text-gray-500 mb-1">Email Address</p>
                    <p className="text-lg font-semibold text-gray-900">{userEmail}</p>
                  </div>
                  <svg className="w-5 h-5 text-emerald-500" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                
                <div className="flex items-center justify-between p-4 bg-gray-50 rounded-xl">
                  <div>
                    <p className="text-sm font-medium text-gray-500 mb-1">Current Plan</p>
                    <span className={`inline-flex px-4 py-2 rounded-lg text-base font-bold ${getPlanBadgeClass(userPlan)}`}>
                      {userPlan.charAt(0).toUpperCase() + userPlan.slice(1)}
                    </span>
                  </div>
                  {userPlan === 'free' && (
                    <Link
                      href="/pricing"
                      className="btn-primary text-sm"
                    >
                      Upgrade
                    </Link>
                  )}
                </div>
              </div>
            </div>

            {/* Quick Actions Card */}
            <div className="card p-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Quick Actions</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Link
                  href="/saved"
                  className="flex items-center p-4 bg-gradient-to-br from-brand-50 to-purple-50 hover:from-brand-100 hover:to-purple-100 rounded-xl transition-all duration-200 border-2 border-transparent hover:border-brand-300 group"
                >
                  <div className="w-12 h-12 bg-white rounded-lg flex items-center justify-center mr-4 shadow-sm group-hover:shadow-md transition-shadow">
                    <svg className="w-6 h-6 text-brand-600" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
                    </svg>
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900 mb-1">Saved Jobs</h3>
                    <p className="text-sm text-gray-600">View your saved opportunities</p>
                  </div>
                  <svg className="w-5 h-5 text-gray-400 group-hover:text-brand-600 transition-colors" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                  </svg>
                </Link>

                {userPlan === 'free' && (
                  <Link
                    href="/pricing"
                    className="flex items-center p-4 bg-gradient-ai hover:opacity-90 rounded-xl transition-all duration-200 shadow-ai hover:shadow-ai-hover group"
                  >
                    <div className="w-12 h-12 bg-white/20 rounded-lg flex items-center justify-center mr-4">
                      <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                    </div>
                    <div className="flex-1">
                      <h3 className="font-semibold text-white mb-1">Upgrade Plan</h3>
                      <p className="text-sm text-white/90">Unlock AI features</p>
                    </div>
                    <svg className="w-5 h-5 text-white/80 group-hover:text-white transition-colors" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                    </svg>
                  </Link>
                )}
              </div>
            </div>

            {/* Email Digests Card */}
            {featureFlags.digests && (
              <div className="card p-8">
                <div className="flex items-start justify-between mb-6">
                  <div>
                    <h2 className="text-2xl font-bold text-gray-900 mb-2">Email Digests</h2>
                    <p className="text-gray-600">
                      Get personalized job recommendations delivered to your inbox
                    </p>
                  </div>
                  <svg className="w-8 h-8 text-brand-600" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                </div>
                <button className="btn-secondary w-full md:w-auto">
                  Manage Digest Settings
                </button>
              </div>
            )}

            {/* Billing Card */}
            <div className="card p-8">
              <div className="flex items-start justify-between mb-6">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900 mb-2">Billing & Subscription</h2>
                  <p className="text-gray-600">Manage your subscription and billing information</p>
                </div>
                <svg className="w-8 h-8 text-brand-600" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                </svg>
              </div>
              <a
                href="/api/stripe/portal"
                className="btn-primary w-full md:w-auto inline-flex items-center justify-center"
              >
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                Manage Billing
              </a>
            </div>

            {/* Sign Out Section */}
            <div className="card p-8 border-2 border-red-100">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-1">Sign Out</h3>
                  <p className="text-sm text-gray-600">You'll need to sign in again to access your account</p>
                </div>
                <button
                  onClick={handleSignOut}
                  className="px-6 py-3 text-red-600 border-2 border-red-600 rounded-xl font-semibold hover:bg-red-50 transition-all"
                >
                  Sign Out
                </button>
              </div>
            </div>
          </>
        ) : (
          <div className="card p-12 text-center">
            <div className="w-20 h-20 mx-auto mb-6 bg-gradient-ai rounded-2xl flex items-center justify-center shadow-glow">
              <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
            </div>
            <h2 className="text-3xl font-bold text-gray-900 mb-4">Sign In to Your Account</h2>
            <p className="text-lg text-gray-600 mb-8 max-w-md mx-auto">
              Use magic link authentication - no password required! We'll send a secure link to your email.
            </p>
            <button
              onClick={handleSignIn}
              className="btn-primary inline-flex items-center text-lg"
            >
              <svg className="w-6 h-6 mr-2" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
              Sign In with Magic Link
            </button>
            <p className="mt-6 text-sm text-gray-500">
              Don't have an account? It will be created automatically when you sign in.
            </p>
          </div>
        )}
      </main>
    </div>
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

