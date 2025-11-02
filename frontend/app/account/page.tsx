// Account page for JobSleuth AI
'use client';
import StripePortalButton from '@/components/StripePortalButton';
import { createClient } from '@supabase/supabase-js';
import { useEffect, useState } from 'react';

export default function AccountPage() {
  const [userEmail, setUserEmail] = useState<string | null>(null);
  useEffect(() => {
    const supabase = createClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL as string,
      process.env.NEXT_PUBLIC_SUPABASE_KEY as string,
    );
    supabase.auth.getUser().then(({ data }) => {
      setUserEmail(data.user?.email ?? null);
    });
  }, []);
  return (
    <main className="max-w-3xl mx-auto px-6 py-12 space-y-6">
      <h1 className="text-2xl font-semibold">Account</h1>
      {userEmail ? (
        <p className="opacity-80">Signed in as {userEmail}</p>
      ) : (
        <p className="opacity-80">Loading user info…</p>
      )}
      <div>
        <h2 className="text-xl font-medium mb-2">Billing</h2>
        <StripePortalButton>Manage Billing</StripePortalButton>
      </div>
    </main>
  );
}
