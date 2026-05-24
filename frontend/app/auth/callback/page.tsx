// Authentication callback page for JobSleuth AI
'use client';
import { useEffect } from 'react';
import { createClient } from '@supabase/supabase-js';
import { useRouter } from 'next/navigation';

export default function AuthCallbackPage() {
  const router = useRouter();
  useEffect(() => {
    // Create a Supabase client on mount
    const supabase = createClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL as string,
      process.env.NEXT_PUBLIC_SUPABASE_KEY as string,
    );
    // Exchange the magic link for a session then redirect
    supabase.auth.getSession().then(({ data }) => {
      if (data.session) {
        router.push('/');
      }
    });
  }, [router]);
  return <p className="p-4">Completing sign‑in…</p>;
}
