// Magic login page for JobSleuth AI
'use client';
import { useState, FormEvent } from 'react';
import { createClient } from '@supabase/supabase-js';

export default function MagicLoginPage() {
  const [email, setEmail] = useState('');
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLogin = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      const supabase = createClient(
        process.env.NEXT_PUBLIC_SUPABASE_URL as string,
        process.env.NEXT_PUBLIC_SUPABASE_KEY as string,
      );
      const { error } = await supabase.auth.signInWithOtp({ email });
      if (error) {
        setError(error.message);
      } else {
        setSent(true);
      }
    } catch (err: any) {
      setError(err.message);
    }
  };

  return (
    <main className="max-w-md mx-auto p-6">
      <h1 className="text-2xl font-semibold mb-4">Magic Login</h1>
      {sent ? (
        <p className="text-green-600">Check your inbox for a magic link to sign in.</p>
      ) : (
        <form onSubmit={handleLogin} className="space-y-4">
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            required
            className="w-full border rounded px-3 py-2"
          />
          <button type="submit" className="w-full py-2 px-4 bg-blue-600 text-white rounded">
            Send Magic Link
          </button>
          {error && <p className="text-red-600 text-sm">{error}</p>}
        </form>
      )}
    </main>
  );
}
