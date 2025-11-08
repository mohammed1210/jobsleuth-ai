/**
 * Pricing Page
 *
 * Display subscription tiers and Stripe checkout buttons
 */

export const dynamic = 'force-dynamic';

export const metadata = {
  title: 'Pricing • JobSleuth AI',
  description: 'Choose the perfect plan for your job search',
};

export default function PricingPage() {
  const plans = [
    {
      name: 'Free',
      price: '$0',
      period: 'forever',
      description: 'Perfect for getting started with your job search',
      features: [
        'Browse unlimited job listings',
        'Basic search and filters',
        'Save up to 10 jobs',
        'Email support',
      ],
      cta: 'Get Started',
      ctaLink: '/jobs',
      highlighted: false,
    },
    {
      name: 'Pro',
      price: '$19',
      period: 'per month',
      description: 'Unlock AI-powered features for serious job seekers',
      features: [
        'Everything in Free',
        'AI job fit scoring',
        'Resume enhancement tools',
        'Cover letter generator',
        'Unlimited saved jobs',
        'Weekly email digests',
        'Priority support',
      ],
      cta: 'Upgrade to Pro',
      ctaLink: '#',
      highlighted: true,
    },
    {
      name: 'Investor',
      price: '$49',
      period: 'per month',
      description: 'Premium features for executive-level job searches',
      features: [
        'Everything in Pro',
        'Advanced AI insights',
        'Executive job board access',
        'Personal job agent',
        'Interview preparation AI',
        'Salary negotiation tools',
        'White-glove support',
      ],
      cta: 'Upgrade to Investor',
      ctaLink: '#',
      highlighted: false,
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-b from-white to-gray-50 py-16">
      <div className="max-w-7xl mx-auto px-4">
        {/* Header */}
        <div className="text-center mb-16">
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
            Choose Your Plan
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Start free and upgrade as you grow. All plans include our core job search features.
          </p>
        </div>

        {/* Pricing Cards */}
        <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
          {plans.map(plan => (
            <div
              key={plan.name}
              className={`rounded-2xl p-8 ${
                plan.highlighted
                  ? 'bg-blue-600 text-white shadow-2xl scale-105 border-4 border-blue-700'
                  : 'bg-white border-2 border-gray-200'
              }`}
            >
              {plan.highlighted && (
                <div className="inline-block px-4 py-1 bg-yellow-400 text-blue-900 text-sm font-semibold rounded-full mb-4">
                  Most Popular
                </div>
              )}

              <h2
                className={`text-2xl font-bold mb-2 ${
                  plan.highlighted ? 'text-white' : 'text-gray-900'
                }`}
              >
                {plan.name}
              </h2>

              <div className="mb-4">
                <span className="text-4xl font-bold">{plan.price}</span>
                <span
                  className={`text-sm ${
                    plan.highlighted ? 'text-blue-100' : 'text-gray-600'
                  }`}
                >
                  {' '}
                  / {plan.period}
                </span>
              </div>

              <p
                className={`mb-6 ${
                  plan.highlighted ? 'text-blue-100' : 'text-gray-600'
                }`}
              >
                {plan.description}
              </p>

              <ul className="space-y-3 mb-8">
                {plan.features.map(feature => (
                  <li key={feature} className="flex items-start">
                    <svg
                      className={`w-5 h-5 mr-2 mt-0.5 flex-shrink-0 ${
                        plan.highlighted ? 'text-blue-200' : 'text-green-500'
                      }`}
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                        clipRule="evenodd"
                      />
                    </svg>
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>

              <a
                href={plan.ctaLink}
                className={`block w-full py-3 px-6 rounded-lg font-semibold text-center transition-colors ${
                  plan.highlighted
                    ? 'bg-white text-blue-600 hover:bg-blue-50'
                    : 'bg-blue-600 text-white hover:bg-blue-700'
                }`}
              >
                {plan.cta}
              </a>
            </div>
          ))}
        </div>

        {/* FAQ or Additional Info */}
        <div className="mt-16 text-center">
          <p className="text-gray-600">
            All plans come with a 14-day money-back guarantee.{' '}
            <a href="/account" className="text-blue-600 hover:underline">
              Manage your subscription
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}
