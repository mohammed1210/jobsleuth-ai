import { createClient, type Session, type SupabaseClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_KEY;

let browserClient: SupabaseClient | null = null;

export function isSupabaseConfigured() {
  return Boolean(supabaseUrl && supabaseAnonKey);
}

export function getSupabaseClient() {
  if (!supabaseUrl || !supabaseAnonKey) {
    throw new Error('Supabase is not configured');
  }

  if (!browserClient) {
    browserClient = createClient(supabaseUrl, supabaseAnonKey, {
      auth: {
        autoRefreshToken: true,
        persistSession: true,
        detectSessionInUrl: true,
      },
    });
  }

  return browserClient;
}

export async function getFreshSession(): Promise<Session | null> {
  const client = getSupabaseClient();
  const { data, error } = await client.auth.getSession();
  if (error) return null;

  const session = data.session;
  if (!session) return null;

  const expiresAt = session.expires_at ?? 0;
  const expiresSoon = expiresAt * 1000 <= Date.now() + 60_000;
  if (!expiresSoon) return session;

  const refreshed = await client.auth.refreshSession();
  if (refreshed.error) return null;
  return refreshed.data.session;
}

export const supabase = isSupabaseConfigured() ? getSupabaseClient() : null;
