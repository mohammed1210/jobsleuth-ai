'use client';

import HeaderClient from '@/components/HeaderClient';
import { BarChart3, BriefcaseBusiness, Lock, Target, WalletCards } from 'lucide-react';

const widgets = [
  { title: 'Applications tracked', value: '0', Icon: BriefcaseBusiness, locked: false },
  { title: 'Saved jobs', value: '0', Icon: Target, locked: false },
  { title: 'Average AI match', value: '82%', Icon: BarChart3, locked: true },
  { title: 'Salary range', value: '$105k - $180k', Icon: WalletCards, locked: true },
];

export default function AnalyticsPage() {
  return (
    <div className="min-h-screen">
      <HeaderClient />
      <main className="mx-auto max-w-7xl px-4 py-10 sm:px-6">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-950">Analytics</h1>
          <p className="mt-2 text-slate-600">Track search momentum, saved opportunities, match quality, and salary signals.</p>
        </div>
        <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
          {widgets.map(({ title, value, Icon, locked }) => (
            <section key={title} className="card p-6">
              <div className="flex items-center justify-between">
                <Icon className="h-6 w-6 text-cyan-700" />
                {locked && <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-600"><Lock className="h-3 w-3" />Pro</span>}
              </div>
              <div className="mt-6 text-3xl font-bold text-slate-950">{value}</div>
              <div className="mt-1 text-sm font-medium text-slate-600">{title}</div>
            </section>
          ))}
        </div>
        <section className="mt-8 rounded-lg border border-slate-200 bg-slate-50 p-6">
          <h2 className="text-lg font-bold text-slate-950">Premium insights</h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">AI match history, salary fit trends, source performance, and application conversion tracking are ready for the Pro and Career Plus subscription path.</p>
        </section>
      </main>
    </div>
  );
}