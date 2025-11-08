// Header component for JobSleuth AI
'use client';
import Link from 'next/link';
import { useEffect, useState } from 'react';
import { createClient } from '@supabase/supabase-js';

export default function HeaderClient() {
  const [signedIn, setSignedIn] = useState(false);
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL as string;
  const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_KEY as string;
  useEffect(() => {
    const supabase = createClient(supabaseUrl, supabaseKey);
    supabase.auth.getSession().then(({ data }) => {
      setSignedIn(!!data.session);
    });
    const { data: listener } = supabase.auth.onAuthStateChange((_event, session) => {
      setSignedIn(!!session);
    });
    return () => {
      listener?.subscription.unsubscribe();
    };
  }, [supabaseUrl, supabaseKey]);

  const handleSignOut = async () => {
    const supabase = createClient(supabaseUrl, supabaseKey);
    await supabase.auth.signOut();
  };

  return (
    <header className="sticky top-0 z-50 glass border-b border-white/20 shadow-sm">
      <nav className="max-w-7xl mx-auto flex items-center justify-between px-6 py-4">
        <div className="flex items-center space-x-8">
          <Link href="/" className="flex items-center space-x-2 group">
            <div className="w-8 h-8 rounded-lg bg-gradient-ai flex items-center justify-center shadow-glow transition-transform group-hover:scale-110">
              <span className="text-white font-bold text-lg">JS</span>
            </div>
            <span className="text-xl font-bold bg-gradient-ai bg-clip-text text-transparent">
              JobSleuth
            </span>
            <span className="text-xs px-2 py-0.5 bg-gradient-ai text-white rounded-full font-medium shadow-sm">
              AI
            </span>
          </Link>
          <div className="hidden md:flex items-center space-x-6">
            <Link href="/jobs" className="text-gray-700 hover:text-brand-600 font-medium transition-colors">
              Jobs
            </Link>
            {signedIn && (
              <Link href="/saved" className="text-gray-700 hover:text-brand-600 font-medium transition-colors">
                Saved
              </Link>
            )}
            <Link href="/pricing" className="text-gray-700 hover:text-brand-600 font-medium transition-colors">
              Pricing
            </Link>
          </div>
        </div>
        <div className="flex items-center space-x-4">
          {signedIn ? (
            <>
              <Link 
                href="/account" 
                className="text-gray-700 hover:text-brand-600 font-medium transition-colors"
              >
                Account
              </Link>
              <button 
                onClick={handleSignOut} 
                className="text-gray-600 hover:text-gray-900 font-medium transition-colors"
              >
                Sign out
              </button>
            </>
          ) : (
            <>
              <Link 
                href="/magic-login" 
                className="text-gray-700 hover:text-brand-600 font-medium transition-colors"
              >
                Sign in
              </Link>
              <Link 
                href="/pricing" 
                className="hidden sm:inline-flex px-4 py-2 bg-gradient-ai text-white rounded-lg font-semibold shadow-sm hover:shadow-ai transition-all duration-200 hover:-translate-y-0.5"
              >
                Get Started
              </Link>
            </>
          )}
        </div>
      </nav>
    </header>
  );
}
