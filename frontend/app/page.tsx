'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

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

  const sampleQueries = [
    { query: 'Software Engineer', location: 'San Francisco' },
    { query: 'Product Manager', location: 'Remote' },
    { query: 'Data Scientist', location: 'New York' },
    { query: 'UI/UX Designer', location: 'Austin' },
  ];

  return (
    <main className="min-h-screen">
      {/* Hero Section */}
      <section className="bg-gradient-to-b from-indigo-50 to-white py-20">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h1 className="text-5xl font-bold mb-6 text-gray-900">
            Find Your Dream Job with AI
          </h1>
          <p className="text-xl text-gray-600 mb-10">
            Discover career opportunities tailored to your skills and preferences using 
            AI-powered job matching and scoring.
          </p>

          {/* Search Form */}
          <form onSubmit={handleSearch} className="bg-white p-6 rounded-lg shadow-lg mb-8">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Job title or keywords"
                className="px-4 py-3 border border-gray-300 rounded focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              />
              <input
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="Location"
                className="px-4 py-3 border border-gray-300 rounded focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              />
              <button
                type="submit"
                className="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-3 rounded font-medium transition-colors"
              >
                Search Jobs
              </button>
            </div>
          </form>

          {/* Sample Queries */}
          <div className="mb-8">
            <p className="text-sm text-gray-600 mb-3">Try searching for:</p>
            <div className="flex flex-wrap justify-center gap-2">
              {sampleQueries.map((sample, index) => (
                <button
                  key={index}
                  onClick={() => {
                    setSearchQuery(sample.query);
                    setLocation(sample.location);
                  }}
                  className="px-3 py-1 bg-white border border-gray-300 rounded-full text-sm hover:border-indigo-500 hover:text-indigo-600 transition-colors"
                >
                  {sample.query} in {sample.location}
                </button>
              ))}
            </div>
          </div>

          {/* CTA */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/jobs"
              className="bg-indigo-600 hover:bg-indigo-700 text-white px-8 py-3 rounded-lg font-medium transition-colors inline-block"
            >
              Browse All Jobs
            </Link>
            <Link
              href="/pricing"
              className="bg-white hover:bg-gray-50 text-indigo-600 border-2 border-indigo-600 px-8 py-3 rounded-lg font-medium transition-colors inline-block"
            >
              View Pricing
            </Link>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-16 bg-white">
        <div className="max-w-6xl mx-auto px-6">
          <h2 className="text-3xl font-bold text-center mb-12">Why Choose JobSleuth?</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="text-4xl mb-4">🎯</div>
              <h3 className="text-xl font-semibold mb-2">AI-Powered Matching</h3>
              <p className="text-gray-600">
                Get personalized job recommendations based on your skills, experience, and preferences.
              </p>
            </div>
            <div className="text-center">
              <div className="text-4xl mb-4">⚡</div>
              <h3 className="text-xl font-semibold mb-2">Real-Time Updates</h3>
              <p className="text-gray-600">
                Access the latest job postings from multiple sources, all in one place.
              </p>
            </div>
            <div className="text-center">
              <div className="text-4xl mb-4">💼</div>
              <h3 className="text-xl font-semibold mb-2">Save & Organize</h3>
              <p className="text-gray-600">
                Keep track of interesting opportunities and manage your job search efficiently.
              </p>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}

