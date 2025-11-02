// Pricing page for JobSleuth AI
export const dynamic = 'force-dynamic';

import UpgradeButton from '@/components/UpgradeButton';

const PRICE_BASIC = process.env.NEXT_PUBLIC_STRIPE_PRICE_BASIC || 'price_basic_xxx';
const PRICE_PRO = process.env.NEXT_PUBLIC_STRIPE_PRICE_PRO || 'price_pro_xxx';
const PRICE_ENTERPRISE = process.env.NEXT_PUBLIC_STRIPE_PRICE_ENTERPRISE || 'price_enterprise_xxx';

export const metadata = {
  title: 'Pricing • JobSleuth AI',
};

export default function PricingPage() {
  return (
    <main className="max-w-4xl mx-auto px-6 py-12">
      <h1 className="text-3xl font-semibold mb-6">Choose your plan</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <section className="border rounded p-6">
          <h2 className="text-xl font-medium">Free</h2>
          <p className="opacity-70">Browse jobs and save up to 3 listings.</p>
        </section>
        <section className="border rounded p-6">
          <h2 className="text-xl font-medium">Pro</h2>
          <p className="opacity-70 mb-4">Unlock advanced filters, AI scores and unlimited saved jobs.</p>
          <UpgradeButton priceId={PRICE_PRO}>Upgrade to Pro</UpgradeButton>
        </section>
        <section className="border rounded p-6">
          <h2 className="text-xl font-medium">Enterprise</h2>
          <p className="opacity-70 mb-4">Team accounts, analytics and priority support.</p>
          <UpgradeButton priceId={PRICE_ENTERPRISE}>Upgrade to Enterprise</UpgradeButton>
        </section>
      </div>
    </main>
  );
}
