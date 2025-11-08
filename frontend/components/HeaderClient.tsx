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
    <header className="border-b sticky top-0 bg-white/80 backdrop-blur z-50">
      <nav className="max-w-6xl mx-auto flex items-center justify-between px-4 py-2">
        <div className="flex items-center space-x-4">
          <Link href="/" className="text-lg font-bold">
            JobSleuth
          </Link>
          <Link href="/jobs" className="hover:underline">Jobs</Link>
          {signedIn && (
            <Link href="/saved" className="hover:underline">Saved</Link>
          )}
          <Link href="/pricing" className="hover:underline">Pricing</Link>
        </div>
        <div className="space-x-4">
          {signedIn ? (
            <>
              <Link href="/account" className="hover:underline">
                Account
              </Link>
              <button onClick={handleSignOut} className="hover:underline">
                Sign out
              </button>
            </>
          ) : (
            <Link href="/magic-login" className="hover:underline">
              Sign in
            </Link>
          )}
        </div>
      </nav>
    </header>
  );
}
