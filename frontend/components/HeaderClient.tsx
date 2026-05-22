'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { BriefcaseBusiness, ChartNoAxesCombined, Home, LogOut, Search, UserRound } from 'lucide-react';
import { getSupabaseClient, isSupabaseConfigured } from '@/lib/supabaseClient';

const navItems = [
  { href: '/', label: 'Home', Icon: Home },
  { href: '/jobs', label: 'Jobs', Icon: Search },
  { href: '/saved', label: 'Saved', Icon: BriefcaseBusiness },
  { href: '/analytics', label: 'Analytics', Icon: ChartNoAxesCombined },
  { href: '/pricing', label: 'Pricing', Icon: ChartNoAxesCombined },
  { href: '/account', label: 'Account', Icon: UserRound },
];

export default function HeaderClient() {
  const [signedIn, setSignedIn] = useState(false);

  useEffect(() => {
    if (!isSupabaseConfigured()) return;
    const supabase = getSupabaseClient();
    supabase.auth.getSession().then(({ data }) => {
      setSignedIn(!!data.session);
    });
    const { data: listener } = supabase.auth.onAuthStateChange((_event, session) => {
      setSignedIn(!!session);
    });
    return () => {
      listener?.subscription.unsubscribe();
    };
  }, []);

  const handleSignOut = async () => {
    if (!isSupabaseConfigured()) return;
    const supabase = getSupabaseClient();
    await supabase.auth.signOut();
    setSignedIn(false);
  };

  return (
    <header className="sticky top-0 z-50 border-b border-slate-200 bg-white/95 shadow-sm backdrop-blur">
      <nav className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6">
        <div className="flex items-center gap-6">
          <Link href="/" className="flex items-center space-x-2 group">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-950 transition-transform group-hover:scale-105">
              <span className="text-white font-bold text-lg">JS</span>
            </div>
            <span className="text-xl font-bold text-slate-950">
              JobSleuth
            </span>
            <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-semibold text-emerald-700">
              AI
            </span>
          </Link>
          <div className="hidden items-center gap-1 lg:flex">
            {navItems.map(({ href, label, Icon }) => (
              <Link key={href} href={href} className="inline-flex items-center gap-1.5 rounded-md px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 hover:text-slate-950">
                <Icon className="h-4 w-4" />
                {label}
              </Link>
            ))}
          </div>
        </div>
        <div className="flex items-center gap-3">
          {signedIn ? (
            <>
              <Link href="/account" className="hidden text-sm font-medium text-slate-700 hover:text-slate-950 sm:inline">
                Account
              </Link>
              <button onClick={handleSignOut} className="inline-flex items-center gap-2 rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100">
                <LogOut className="h-4 w-4" />
                Sign out
              </button>
            </>
          ) : (
            <>
              <Link href="/magic-login" className="text-sm font-medium text-slate-700 hover:text-slate-950">
                Sign in
              </Link>
              <Link href="/pricing" className="hidden rounded-md bg-slate-950 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800 sm:inline-flex">
                Get Started
              </Link>
            </>
          )}
        </div>
      </nav>
    </header>
  );
}
