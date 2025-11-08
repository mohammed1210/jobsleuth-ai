// Pricing page for JobSleuth AI
export const dynamic = 'force-dynamic';

import UpgradeButton from '@/components/UpgradeButton';
import HeaderClient from '@/components/HeaderClient';

const PRICE_PRO = process.env.NEXT_PUBLIC_STRIPE_PRICE_PRO || 'price_pro_xxx';
const PRICE_INVESTOR = process.env.NEXT_PUBLIC_STRIPE_PRICE_INVESTOR || 'price_investor_xxx';

export const metadata = {
  title: 'Pricing • JobSleuth AI',
};

export default function PricingPage() {
  return (
    <div className="min-h-screen">
      <HeaderClient />
      
      <main className="max-w-7xl mx-auto px-6 py-16">
        {/* Header */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center space-x-2 px-4 py-2 bg-brand-100 rounded-full mb-6">
            <svg className="w-4 h-4 text-brand-600" fill="currentColor" viewBox="0 0 20 20">
              <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
            </svg>
            <span className="text-sm font-semibold text-brand-600">AI-Powered Plans</span>
          </div>
          <h1 className="text-5xl md:text-6xl font-bold mb-6">
            Choose Your <span className="text-gradient">Perfect Plan</span>
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Unlock the full power of AI-driven job search. Find your dream job faster with intelligent matching.
          </p>
        </div>
        
        {/* Pricing Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16">
          {/* Free Plan */}
          <div className="card p-8 flex flex-col hover:shadow-ai transition-all duration-200">
            <div className="mb-6">
              <h2 className="text-2xl font-bold mb-2 text-gray-900">Free</h2>
              <div className="mb-4">
                <span className="text-5xl font-bold text-gray-900">$0</span>
                <span className="text-gray-600 ml-2">/month</span>
              </div>
              <p className="text-gray-600">Perfect for exploring opportunities</p>
            </div>
            
            <ul className="mb-8 space-y-4 flex-grow">
              <li className="flex items-start">
                <svg className="w-5 h-5 text-emerald-500 mr-3 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
                <span className="text-gray-700">Browse unlimited job listings</span>
              </li>
              <li className="flex items-start">
                <svg className="w-5 h-5 text-emerald-500 mr-3 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
                <span className="text-gray-700">Save up to 3 job listings</span>
              </li>
              <li className="flex items-start">
                <svg className="w-5 h-5 text-emerald-500 mr-3 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
                <span className="text-gray-700">Basic search filters</span>
              </li>
              <li className="flex items-start">
                <svg className="w-5 h-5 text-emerald-500 mr-3 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
                <span className="text-gray-700">Access to job details</span>
              </li>
            </ul>
            
            <div className="pt-4 border-t border-gray-200">
              <span className="text-gray-500 font-medium">Current Plan</span>
            </div>
          </div>

          {/* Pro Plan */}
          <div className="card p-8 flex flex-col relative ring-2 ring-brand-500 shadow-ai-hover transform scale-105">
            <div className="absolute -top-5 left-1/2 transform -translate-x-1/2">
              <span className="ai-badge px-6 py-2">
                Most Popular
              </span>
            </div>
            
            <div className="mb-6">
              <h2 className="text-2xl font-bold mb-2 text-gray-900">Pro</h2>
              <div className="mb-4">
                <span className="text-5xl font-bold text-gradient">$19</span>
                <span className="text-gray-600 ml-2">/month</span>
              </div>
              <p className="text-gray-600">For serious job seekers</p>
            </div>
            
            <ul className="mb-8 space-y-4 flex-grow">
              <li className="flex items-start">
                <svg className="w-5 h-5 text-brand-500 mr-3 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
                <span className="text-gray-700 font-medium">Everything in Free</span>
              </li>
              <li className="flex items-start">
                <svg className="w-5 h-5 text-brand-500 mr-3 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                </svg>
                <span className="text-gray-700"><strong>AI Match Scores</strong> - Get personalized job fit scores</span>
              </li>
              <li className="flex items-start">
                <svg className="w-5 h-5 text-brand-500 mr-3 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
                <span className="text-gray-700">Unlimited saved jobs</span>
              </li>
              <li className="flex items-start">
                <svg className="w-5 h-5 text-brand-500 mr-3 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
                <span className="text-gray-700">Advanced search filters</span>
              </li>
              <li className="flex items-start">
                <svg className="w-5 h-5 text-brand-500 mr-3 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
                <span className="text-gray-700">Email job alerts</span>
              </li>
              <li className="flex items-start">
                <svg className="w-5 h-5 text-brand-500 mr-3 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
                <span className="text-gray-700">Priority support</span>
              </li>
            </ul>
            
            <UpgradeButton priceId={PRICE_PRO}>Upgrade to Pro</UpgradeButton>
          </div>

          {/* Investor Plan */}
          <div className="card p-8 flex flex-col hover:shadow-ai transition-all duration-200">
            <div className="mb-6">
              <h2 className="text-2xl font-bold mb-2 text-gray-900">Investor</h2>
              <div className="mb-4">
                <span className="text-5xl font-bold text-gray-900">$99</span>
                <span className="text-gray-600 ml-2">/month</span>
              </div>
              <p className="text-gray-600">For teams and recruiters</p>
            </div>
            
            <ul className="mb-8 space-y-4 flex-grow">
              <li className="flex items-start">
                <svg className="w-5 h-5 text-purple-500 mr-3 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
                <span className="text-gray-700 font-medium">Everything in Pro</span>
              </li>
              <li className="flex items-start">
                <svg className="w-5 h-5 text-purple-500 mr-3 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
                <span className="text-gray-700">Team accounts (up to 5 users)</span>
              </li>
              <li className="flex items-start">
                <svg className="w-5 h-5 text-purple-500 mr-3 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
                <span className="text-gray-700">Advanced analytics dashboard</span>
              </li>
              <li className="flex items-start">
                <svg className="w-5 h-5 text-purple-500 mr-3 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
                <span className="text-gray-700">Dedicated account manager</span>
              </li>
              <li className="flex items-start">
                <svg className="w-5 h-5 text-purple-500 mr-3 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
                <span className="text-gray-700">Custom integrations & API access</span>
              </li>
              <li className="flex items-start">
                <svg className="w-5 h-5 text-purple-500 mr-3 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
                <span className="text-gray-700">White-label options</span>
              </li>
            </ul>
            
            <UpgradeButton priceId={PRICE_INVESTOR}>Upgrade to Investor</UpgradeButton>
          </div>
        </div>

        {/* Trust Section */}
        <div className="text-center mb-12">
          <p className="text-gray-600 mb-6">
            <svg className="w-5 h-5 inline mr-2 text-emerald-500" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
            14-day money-back guarantee • Cancel anytime • Secure payment
          </p>
        </div>

        {/* FAQ Section */}
        <div className="card p-8 max-w-3xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-8 text-gray-900">
            Frequently Asked Questions
          </h2>
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">How does AI matching work?</h3>
              <p className="text-gray-600">
                Our AI analyzes your profile, skills, experience, and preferences to calculate a match score for each job. 
                This helps you quickly identify the best opportunities that align with your career goals.
              </p>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Can I change plans anytime?</h3>
              <p className="text-gray-600">
                Yes! You can upgrade, downgrade, or cancel your subscription at any time. Changes take effect at the start 
                of your next billing cycle.
              </p>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">What payment methods do you accept?</h3>
              <p className="text-gray-600">
                We accept all major credit cards (Visa, Mastercard, American Express) through our secure payment processor, Stripe.
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
