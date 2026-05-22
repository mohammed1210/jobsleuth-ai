'use client';
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { getSupabaseClient, isSupabaseConfigured } from '@/lib/supabaseClient';

export default function AuthCallbackPage() {
  const router = useRouter();
  useEffect(() => {
    if (!isSupabaseConfigured()) {
      router.push('/magic-login');
      return;
    }
    getSupabaseClient().auth.getSession().then(() => router.push('/account'));
  }, [router]);
  return <p className="p-4">Completing sign-in...</p>;
}
