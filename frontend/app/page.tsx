'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import HeaderClient from '@/components/HeaderClient';
import { BarChart3, BriefcaseBusiness, Filter, Search, Sparkles } from 'lucide-react';

export default function HomePage() {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState('');
  const [location, setLocation] = useState('');

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const params = new URLSearchParams();
    if (searchQuery) params.append('q', searchQuery);
    if (location) params.append('location', location);
    router.push(`/jobs?${params.toString()}`);
  };

  return (
    <div className="min-h-screen bg-white">
      <HeaderClient />
      <main>
        <section className="border-b border-slate-200 bg-slate-50">
          <div className="mx-auto grid max-w-7xl gap-10 px-4 py-16 sm:px-6 lg:grid-cols-[1.05fr_0.95fr] lg:py-20">
            <div className="flex flex-col justify-center">
              <div className="mb-5 inline-flex w-fit items-center gap-2 rounded-full border border-cyan-200 bg-white px-3 py-1 text-sm font-semibold text-cyan-800">
                <Sparkles className="h-4 w-4" /> AI job matching, cleaner from day one
              </div>
              <h1 className="max-w-3xl text-4xl font-bold tracking-tight text-slate-950 sm:text-5xl lg:text-6xl">
                JobSleuth AI
              </h1>
              <p className="mt-5 max-w-2xl text-lg leading-8 text-slate-600">
                Search roles, compare salary fit, save opportunities, and use AI scoring to focus on jobs that match your next move.
              </p>
              <form onSubmit={handleSearch} className="mt-8 max-w-3xl rounded-lg border border-slate-200 bg-white p-2 shadow-sm">
                <div className="grid gap-2 sm:grid-cols-[1fr_1fr_auto]">
                  <input value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} placeholder="Role, skill, or company" className="input-modern" />
                  <input value={location} onChange={(e) => setLocation(e.target.value)} placeholder="Location or Remote" className="input-modern" />
                  <button type="submit" className="btn-primary inline-flex items-center justify-center gap-2"><Search className="h-4 w-4" />Search</button>
                </div>
              </form>
              <div className="mt-6 flex flex-wrap gap-3">
                <Link href="/jobs" className="btn-secondary">Browse jobs</Link>
                <Link href="/pricing" className="btn-ghost">Compare plans</Link>
              </div>
            </div>
            <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
              <div className="mb-4 flex items-center justify-between border-b border-slate-100 pb-3">
                <span className="text-sm font-semibold text-slate-600">Priority matches</span>
                <span className="rounded-full bg-emerald-100 px-2 py-1 text-xs font-semibold text-emerald-700">Live preview</span>
              </div>
              {['Senior Software Engineer', 'AI Product Manager', 'Frontend Engineer'].map((title, index) => (
                <div key={title} className="mb-3 rounded-md border border-slate-200 p-4 last:mb-0">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <div className="font-semibold text-slate-950">{title}</div>
                      <div className="mt-1 text-sm text-slate-500">Remote or hybrid • ${index === 0 ? '140k - $180k' : '105k - $165k'}</div>
                    </div>
                    <div className="rounded-md bg-cyan-50 px-2 py-1 text-sm font-bold text-cyan-700">{88 - index * 6}%</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="mx-auto grid max-w-7xl gap-5 px-4 py-12 sm:px-6 md:grid-cols-3">
          {[{ icon: Sparkles, title: 'AI match score', body: 'Deterministic fallback scoring now, OpenAI scoring when configured.' }, { icon: Filter, title: 'Career filters', body: 'Search by role, location, salary range, and role type from one screen.' }, { icon: BarChart3, title: 'Subscription-ready', body: 'Free, Pro, and Career Plus paths map cleanly into Stripe.' }].map(({ icon: Icon, title, body }) => (
            <div key={title} className="card p-6">
              <Icon className="h-6 w-6 text-cyan-700" />
              <h2 className="mt-4 text-lg font-bold text-slate-950">{title}</h2>
              <p className="mt-2 text-sm leading-6 text-slate-600">{body}</p>
            </div>
          ))}
        </section>
      </main>
    </div>
  );
}
