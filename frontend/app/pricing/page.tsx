// Pricing page for JobSleuth AI
export const dynamic = 'force-dynamic';

import UpgradeButton from '@/components/UpgradeButton';

const PRICE_PRO = process.env.NEXT_PUBLIC_STRIPE_PRICE_PRO || 'price_pro_xxx';
const PRICE_INVESTOR = process.env.NEXT_PUBLIC_STRIPE_PRICE_INVESTOR || 'price_investor_xxx';

export const metadata = {
  title: 'Pricing • JobSleuth AI',
};

export default function PricingPage() {
  return (
    <main className="max-w-6xl mx-auto px-6 py-12">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold mb-4">Choose Your Plan</h1>
        <p className="text-xl text-gray-600">
          Get the features you need to accelerate your job search
        </p>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {/* Free Plan */}
        <section className="border-2 border-gray-200 rounded-lg p-6 flex flex-col">
          <div className="mb-6">
            <h2 className="text-2xl font-bold mb-2">Free</h2>
            <div className="mb-4">
              <span className="text-4xl font-bold">$0</span>
              <span className="text-gray-600">/month</span>
            </div>
            <p className="text-gray-600">Perfect for getting started</p>
          </div>
          
          <ul className="mb-6 space-y-3 flex-grow">
            <li className="flex items-start">
              <span className="text-green-500 mr-2">✓</span>
              <span>Browse jobs</span>
            </li>
            <li className="flex items-start">
              <span className="text-green-500 mr-2">✓</span>
              <span>Save up to 3 listings</span>
            </li>
            <li className="flex items-start">
              <span className="text-green-500 mr-2">✓</span>
              <span>Basic search filters</span>
            </li>
          </ul>
          
          <div className="border-t pt-4">
            <span className="text-gray-500">Current Plan</span>
          </div>
        </section>

        {/* Pro Plan */}
        <section className="border-2 border-indigo-500 rounded-lg p-6 flex flex-col relative">
          <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
            <span className="bg-indigo-500 text-white px-4 py-1 rounded-full text-sm font-medium">
              Most Popular
            </span>
          </div>
          
          <div className="mb-6">
            <h2 className="text-2xl font-bold mb-2">Pro</h2>
            <div className="mb-4">
              <span className="text-4xl font-bold">$19</span>
              <span className="text-gray-600">/month</span>
            </div>
            <p className="text-gray-600">For serious job seekers</p>
          </div>
          
          <ul className="mb-6 space-y-3 flex-grow">
            <li className="flex items-start">
              <span className="text-green-500 mr-2">✓</span>
              <span>Everything in Free</span>
            </li>
            <li className="flex items-start">
              <span className="text-green-500 mr-2">✓</span>
              <span>Unlimited saved jobs</span>
            </li>
            <li className="flex items-start">
              <span className="text-green-500 mr-2">✓</span>
              <span>AI match scores</span>
            </li>
            <li className="flex items-start">
              <span className="text-green-500 mr-2">✓</span>
              <span>Advanced filters</span>
            </li>
            <li className="flex items-start">
              <span className="text-green-500 mr-2">✓</span>
              <span>Email job alerts</span>
            </li>
          </ul>
          
          <UpgradeButton priceId={PRICE_PRO}>Upgrade to Pro</UpgradeButton>
        </section>

        {/* Investor Plan */}
        <section className="border-2 border-gray-200 rounded-lg p-6 flex flex-col">
          <div className="mb-6">
            <h2 className="text-2xl font-bold mb-2">Investor</h2>
            <div className="mb-4">
              <span className="text-4xl font-bold">$99</span>
              <span className="text-gray-600">/month</span>
            </div>
            <p className="text-gray-600">For teams and recruiters</p>
          </div>
          
          <ul className="mb-6 space-y-3 flex-grow">
            <li className="flex items-start">
              <span className="text-green-500 mr-2">✓</span>
              <span>Everything in Pro</span>
            </li>
            <li className="flex items-start">
              <span className="text-green-500 mr-2">✓</span>
              <span>Team accounts (up to 5 users)</span>
            </li>
            <li className="flex items-start">
              <span className="text-green-500 mr-2">✓</span>
              <span>Advanced analytics</span>
            </li>
            <li className="flex items-start">
              <span className="text-green-500 mr-2">✓</span>
              <span>Priority support</span>
            </li>
            <li className="flex items-start">
              <span className="text-green-500 mr-2">✓</span>
              <span>Custom integrations</span>
            </li>
          </ul>
          
          <UpgradeButton priceId={PRICE_INVESTOR}>Upgrade to Investor</UpgradeButton>
        </section>
      </div>

      <div className="mt-12 text-center text-gray-600">
        <p>All plans include a 14-day money-back guarantee</p>
      </div>
    </main>
  );
}
