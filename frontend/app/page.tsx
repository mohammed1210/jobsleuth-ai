// Home page for JobSleuth AI

import Link from 'next/link';

export const dynamic = 'force-dynamic';

export default function HomePage() {
  const sampleQueries = [
    'Software Engineer Remote',
    'Product Manager San Francisco',
    'Data Scientist New York',
    'DevOps Engineer',
  ];

  return (
    <main className="min-h-screen bg-gradient-to-b from-white to-gray-50">
      {/* Hero Section */}
      <div className="max-w-6xl mx-auto px-6 py-20">
        <div className="text-center mb-16">
          <h1 className="text-5xl md:text-6xl font-bold mb-6 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Find Your Dream Job with AI
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
            JobSleuth AI helps you discover, analyze, and land the perfect job using AI-powered
            matching and insights.
          </p>

          {/* Search Bar */}
          <div className="max-w-2xl mx-auto mb-8">
            <form action="/jobs" method="get" className="relative">
              <input
                type="search"
                name="q"
                placeholder="Search for jobs..."
                className="w-full px-6 py-4 text-lg rounded-full border-2 border-gray-200 focus:border-blue-500 focus:outline-none shadow-lg"
              />
              <button
                type="submit"
                className="absolute right-2 top-1/2 -translate-y-1/2 px-6 py-2 bg-blue-600 text-white rounded-full hover:bg-blue-700 transition-colors"
              >
                Search
              </button>
            </form>
          </div>

          {/* Sample Queries */}
          <div className="flex flex-wrap gap-2 justify-center">
            <span className="text-sm text-gray-500">Try:</span>
            {sampleQueries.map(query => (
              <Link
                key={query}
                href={`/jobs?q=${encodeURIComponent(query)}`}
                className="text-sm px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded-full transition-colors"
              >
                {query}
              </Link>
            ))}
          </div>
        </div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-3 gap-8 mt-20">
          <FeatureCard
            icon="🎯"
            title="AI-Powered Matching"
            description="Get personalized job fit scores based on your skills and preferences"
          />
          <FeatureCard
            icon="📝"
            title="Resume Tools"
            description="Enhance your resume and generate tailored cover letters with AI"
          />
          <FeatureCard
            icon="📧"
            title="Email Digests"
            description="Receive curated job listings directly to your inbox"
          />
        </div>

        {/* CTA Section */}
        <div className="mt-20 text-center">
          <Link
            href="/jobs"
            className="inline-block px-8 py-4 bg-blue-600 text-white text-lg font-semibold rounded-lg hover:bg-blue-700 transition-colors shadow-lg"
          >
            Browse All Jobs
          </Link>
          <p className="mt-4 text-gray-600">
            Or{' '}
            <Link href="/pricing" className="text-blue-600 hover:underline">
              view pricing
            </Link>{' '}
            for premium features
          </p>
        </div>
      </div>
    </main>
  );
}

function FeatureCard({
  icon,
  title,
  description,
}: {
  icon: string;
  title: string;
  description: string;
}) {
  return (
    <div className="p-6 bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow">
      <div className="text-4xl mb-4">{icon}</div>
      <h3 className="text-xl font-semibold mb-2">{title}</h3>
      <p className="text-gray-600">{description}</p>
    </div>
  );
}
