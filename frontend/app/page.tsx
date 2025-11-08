// Home page for JobSleuth AI

import Link from 'next/link';

export const dynamic = 'force-dynamic';

export default function HomePage() {
  return (
    <main className="max-w-6xl mx-auto px-6 py-12">
      <div className="text-center mb-12">
        <h1 className="text-5xl font-bold mb-4 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
          Welcome to JobSleuth AI
        </h1>
        <p className="text-xl text-gray-600 mb-6">
          Discover your next career opportunity using AI‑powered job matching and scoring
        </p>
        <div className="flex gap-4 justify-center">
          <Link
            href="/jobs"
            className="px-6 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition"
          >
            Browse Jobs
          </Link>
          <Link
            href="/pricing"
            className="px-6 py-3 border border-blue-600 text-blue-600 rounded-lg font-semibold hover:bg-blue-50 transition"
          >
            View Pricing
          </Link>
        </div>
      </div>

      <div className="grid md:grid-cols-3 gap-8 mb-12">
        <div className="p-6 border rounded-lg">
          <h3 className="text-xl font-semibold mb-3">🎯 AI-Powered Matching</h3>
          <p className="text-gray-600">
            Get personalized job recommendations based on your skills and experience
          </p>
        </div>
        <div className="p-6 border rounded-lg">
          <h3 className="text-xl font-semibold mb-3">📊 Smart Scoring</h3>
          <p className="text-gray-600">
            See how well each job matches your profile with detailed fit scores
          </p>
        </div>
        <div className="p-6 border rounded-lg">
          <h3 className="text-xl font-semibold mb-3">✍️ Resume Tools</h3>
          <p className="text-gray-600">
            Generate tailored cover letters and resume suggestions for each job
          </p>
        </div>
      </div>

      <div className="bg-gray-50 p-8 rounded-lg">
        <h2 className="text-2xl font-semibold mb-4">Popular Searches</h2>
        <div className="flex flex-wrap gap-3">
          {[
            'Software Engineer',
            'Product Manager',
            'Data Scientist',
            'Frontend Developer',
            'DevOps Engineer',
            'UX Designer',
          ].map(query => (
            <Link
              key={query}
              href={`/jobs?q=${encodeURIComponent(query)}`}
              className="px-4 py-2 bg-white border rounded-lg hover:border-blue-500 hover:text-blue-600 transition"
            >
              {query}
            </Link>
          ))}
        </div>
      </div>

      <div className="mt-12 text-center text-gray-500">
        <p>
          <Link href="/account" className="text-blue-600 hover:underline">
            Sign in
          </Link>{' '}
          to save jobs and get personalized recommendations
        </p>
      </div>
    </main>
  );
}

