import HeaderClient from '@/components/HeaderClient';
import UpgradeButton from '@/components/UpgradeButton';
import { Check, Sparkles } from 'lucide-react';

export const dynamic = 'force-dynamic';

const PRICE_PRO = process.env.NEXT_PUBLIC_STRIPE_PRICE_PRO || 'price_pro_xxx';
const PRICE_CAREER_PLUS = process.env.NEXT_PUBLIC_STRIPE_PRICE_CAREER_PLUS || 'price_career_plus_xxx';

const plans = [
  {
    name: 'Free',
    price: '$0',
    description: 'Search jobs and keep a short list while you explore.',
    features: ['Browse job listings', 'Core filters', 'Save up to 3 jobs', 'Basic job detail pages'],
    cta: null,
  },
  {
    name: 'Pro',
    price: '$19',
    description: 'For active job seekers who want faster triage.',
    features: ['Everything in Free', 'Unlimited saved jobs', 'AI match scoring', 'Resume improvement prompts', 'Email digest ready'],
    cta: { label: 'Upgrade to Pro', priceId: PRICE_PRO },
    featured: true,
  },
  {
    name: 'Career Plus',
    price: '$49',
    description: 'For career users and recruiters tracking more signals.',
    features: ['Everything in Pro', 'Analytics widgets', 'Salary fit tracking', 'Priority matches', 'Career workflow exports'],
    cta: { label: 'Upgrade to Career Plus', priceId: PRICE_CAREER_PLUS },
  },
];

export const metadata = {
  title: 'Pricing - JobSleuth AI',
};

export default function PricingPage() {
  return (
    <div className="min-h-screen">
      <HeaderClient />
      <main className="mx-auto max-w-7xl px-4 py-12 sm:px-6">
        <div className="mx-auto mb-12 max-w-3xl text-center">
          <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-cyan-200 bg-cyan-50 px-3 py-1 text-sm font-semibold text-cyan-800"><Sparkles className="h-4 w-4" />MVP monetisation baseline</div>
          <h1 className="text-4xl font-bold tracking-tight text-slate-950 sm:text-5xl">Choose your JobSleuth plan</h1>
          <p className="mt-4 text-lg leading-8 text-slate-600">Start with core job discovery, then unlock AI scoring, resume tools, analytics, and larger saved-job workflows.</p>
        </div>
        <div className="grid gap-6 lg:grid-cols-3">
          {plans.map((plan) => (
            <section key={plan.name} className={`card flex flex-col p-7 ${plan.featured ? 'border-2 border-cyan-600 shadow-lg' : ''}`}>
              {plan.featured && <div className="mb-4 w-fit rounded-full bg-cyan-700 px-3 py-1 text-xs font-bold text-white">Most useful</div>}
              <h2 className="text-2xl font-bold text-slate-950">{plan.name}</h2>
              <p className="mt-3 min-h-12 text-sm leading-6 text-slate-600">{plan.description}</p>
              <div className="mt-6 flex items-end gap-1"><span className="text-4xl font-bold text-slate-950">{plan.price}</span><span className="pb-1 text-sm font-medium text-slate-500">/month</span></div>
              <ul className="mt-7 flex-1 space-y-3 text-sm text-slate-700">
                {plan.features.map((feature) => (
                  <li key={feature} className="flex gap-3"><Check className="mt-0.5 h-4 w-4 flex-none text-emerald-600" />{feature}</li>
                ))}
              </ul>
              <div className="mt-8">
                {plan.cta ? <UpgradeButton priceId={plan.cta.priceId}>{plan.cta.label}</UpgradeButton> : <div className="rounded-md border border-slate-300 px-4 py-3 text-center text-sm font-semibold text-slate-600">Current baseline</div>}
              </div>
            </section>
          ))}
        </div>
      </main>
    </div>
  );
}
