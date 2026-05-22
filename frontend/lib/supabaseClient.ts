import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_KEY;

export function isSupabaseConfigured() {
	return Boolean(supabaseUrl && supabaseAnonKey);
}

export function getSupabaseClient() {
	if (!supabaseUrl || !supabaseAnonKey) {
		throw new Error('Supabase is not configured');
	}

	return createClient(supabaseUrl, supabaseAnonKey);
}

export const supabase = isSupabaseConfigured()
	? createClient(supabaseUrl as string, supabaseAnonKey as string)
	: null;
