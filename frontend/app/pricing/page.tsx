// Pricing page for JobSleuth AI
export const dynamic = 'force-dynamic';

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
          Find the perfect plan for your job search journey
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <section className="border rounded-lg p-8 hover:shadow-lg transition">
          <h2 className="text-2xl font-semibold mb-2">Free</h2>
          <div className="text-4xl font-bold mb-4">$0</div>
          <p className="text-gray-600 mb-6">Perfect for getting started</p>
          <ul className="space-y-3 mb-8">
            <li className="flex items-start">
              <span className="text-green-500 mr-2">✓</span>
              <span>Browse all job listings</span>
            </li>
            <li className="flex items-start">
              <span className="text-green-500 mr-2">✓</span>
              <span>Save up to 5 jobs</span>
            </li>
            <li className="flex items-start">
              <span className="text-green-500 mr-2">✓</span>
              <span>Basic search filters</span>
            </li>
            <li className="flex items-start">
              <span className="text-gray-300 mr-2">✗</span>
              <span className="text-gray-400">AI fit scoring</span>
            </li>
            <li className="flex items-start">
              <span className="text-gray-300 mr-2">✗</span>
              <span className="text-gray-400">Resume tools</span>
            </li>
          </ul>
          <button className="w-full px-6 py-3 border border-gray-300 rounded-lg font-semibold hover:bg-gray-50 transition">
            Current Plan
          </button>
        </section>

        <section className="border-2 border-blue-600 rounded-lg p-8 hover:shadow-lg transition relative">
          <div className="absolute top-0 right-0 bg-blue-600 text-white px-3 py-1 text-sm font-semibold rounded-bl-lg rounded-tr-lg">
            Popular
          </div>
          <h2 className="text-2xl font-semibold mb-2">Pro</h2>
          <div className="text-4xl font-bold mb-4">$29<span className="text-lg text-gray-600">/mo</span></div>
          <p className="text-gray-600 mb-6">For serious job seekers</p>
          <ul className="space-y-3 mb-8">
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
              <span>AI-powered fit scoring</span>
            </li>
            <li className="flex items-start">
              <span className="text-green-500 mr-2">✓</span>
              <span>Resume suggestions</span>
            </li>
            <li className="flex items-start">
              <span className="text-green-500 mr-2">✓</span>
              <span>Cover letter generator</span>
            </li>
            <li className="flex items-start">
              <span className="text-green-500 mr-2">✓</span>
              <span>Email digests</span>
            </li>
          </ul>
          <a
            href={`/api/stripe/checkout?priceId=${PRICE_PRO}`}
            className="block w-full px-6 py-3 bg-blue-600 text-white text-center rounded-lg font-semibold hover:bg-blue-700 transition"
          >
            Upgrade to Pro
          </a>
        </section>

        <section className="border rounded-lg p-8 hover:shadow-lg transition">
          <h2 className="text-2xl font-semibold mb-2">Investor</h2>
          <div className="text-4xl font-bold mb-4">$99<span className="text-lg text-gray-600">/mo</span></div>
          <p className="text-gray-600 mb-6">For teams and recruiters</p>
          <ul className="space-y-3 mb-8">
            <li className="flex items-start">
              <span className="text-green-500 mr-2">✓</span>
              <span>Everything in Pro</span>
            </li>
            <li className="flex items-start">
              <span className="text-green-500 mr-2">✓</span>
              <span>Team accounts (up to 5)</span>
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
            <li className="flex items-start">
              <span className="text-green-500 mr-2">✓</span>
              <span>API access</span>
            </li>
          </ul>
          <a
            href={`/api/stripe/checkout?priceId=${PRICE_INVESTOR}`}
            className="block w-full px-6 py-3 bg-purple-600 text-white text-center rounded-lg font-semibold hover:bg-purple-700 transition"
          >
            Upgrade to Investor
          </a>
        </section>
      </div>

      <div className="mt-12 text-center text-gray-600">
        <p>All plans include a 14-day money-back guarantee. Cancel anytime.</p>
      </div>
    </main>
  );
}

