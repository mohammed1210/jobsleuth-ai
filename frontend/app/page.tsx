'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import HeaderClient from '@/components/HeaderClient';

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
    { query: 'Software Engineer', location: 'San Francisco', icon: '💻' },
    { query: 'Product Manager', location: 'Remote', icon: '📊' },
    { query: 'Data Scientist', location: 'New York', icon: '📈' },
    { query: 'UI/UX Designer', location: 'Austin', icon: '🎨' },
  ];

  return (
    <div className="min-h-screen">
      <HeaderClient />
      
      <main>
        {/* Hero Section */}
        <section className="relative overflow-hidden py-20 lg:py-32">
          {/* Animated Background */}
          <div className="absolute inset-0 bg-gradient-to-br from-brand-50 via-purple-50 to-pink-50">
            <div className="absolute inset-0 bg-gradient-ai-soft opacity-50"></div>
          </div>
          
          <div className="relative max-w-7xl mx-auto px-6">
            <div className="text-center mb-12">
              {/* AI Badge */}
              <div className="inline-flex items-center space-x-2 px-4 py-2 bg-white/80 backdrop-blur-sm rounded-full shadow-ai mb-6 border border-brand-100">
                <div className="ai-indicator w-2 h-2 bg-gradient-ai rounded-full"></div>
                <span className="text-sm font-semibold text-brand-600">AI-Powered Job Matching</span>
              </div>
              
              <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold mb-6 leading-tight">
                <span className="text-gray-900">Find Your Dream Job</span>
                <br />
                <span className="text-gradient">with AI Precision</span>
              </h1>
              
              <p className="text-xl md:text-2xl text-gray-600 mb-10 max-w-3xl mx-auto">
                Discover career opportunities perfectly matched to your skills and preferences 
                using cutting-edge AI technology.
              </p>

              {/* Search Form */}
              <form onSubmit={handleSearch} className="max-w-4xl mx-auto mb-8">
                <div className="card p-2 flex flex-col md:flex-row gap-2">
                  <div className="flex-1">
                    <input
                      type="text"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      placeholder="Job title, keywords, or company"
                      className="w-full px-6 py-4 bg-gray-50 rounded-lg focus:bg-white focus:ring-2 focus:ring-brand-500/20 transition-all outline-none text-lg"
                    />
                  </div>
                  <div className="flex-1">
                    <input
                      type="text"
                      value={location}
                      onChange={(e) => setLocation(e.target.value)}
                      placeholder="City, state, or 'Remote'"
                      className="w-full px-6 py-4 bg-gray-50 rounded-lg focus:bg-white focus:ring-2 focus:ring-brand-500/20 transition-all outline-none text-lg"
                    />
                  </div>
                  <button
                    type="submit"
                    className="px-8 py-4 bg-gradient-ai text-white rounded-lg font-semibold shadow-ai hover:shadow-ai-hover transition-all duration-200 hover:-translate-y-0.5 text-lg whitespace-nowrap"
                  >
                    Search Jobs
                  </button>
                </div>
              </form>

              {/* Sample Queries */}
              <div className="mb-10">
                <p className="text-sm text-gray-600 mb-4 font-medium">Popular Searches:</p>
                <div className="flex flex-wrap justify-center gap-3">
                  {sampleQueries.map((sample, index) => (
                    <button
                      key={index}
                      onClick={() => {
                        setSearchQuery(sample.query);
                        setLocation(sample.location);
                      }}
                      className="group px-4 py-2 bg-white hover:bg-brand-50 border-2 border-gray-200 hover:border-brand-300 rounded-xl text-sm font-medium transition-all duration-200 hover:-translate-y-0.5 shadow-sm hover:shadow-md"
                    >
                      <span className="mr-2">{sample.icon}</span>
                      {sample.query} in {sample.location}
                    </button>
                  ))}
                </div>
              </div>

              {/* CTA Buttons */}
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Link
                  href="/jobs"
                  className="inline-flex items-center justify-center px-8 py-4 bg-gradient-ai text-white rounded-xl font-semibold shadow-ai hover:shadow-ai-hover transition-all duration-200 hover:-translate-y-0.5 text-lg"
                >
                  <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                  Browse All Jobs
                </Link>
                <Link
                  href="/pricing"
                  className="inline-flex items-center justify-center px-8 py-4 bg-white hover:bg-gray-50 text-brand-600 border-2 border-brand-600 rounded-xl font-semibold transition-all duration-200 hover:-translate-y-0.5 text-lg"
                >
                  <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  View Pricing
                </Link>
              </div>
            </div>
          </div>

          {/* Decorative Elements */}
          <div className="absolute top-20 left-10 w-72 h-72 bg-purple-300 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse-slow"></div>
          <div className="absolute bottom-20 right-10 w-72 h-72 bg-brand-300 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse-slow animation-delay-2000"></div>
        </section>

        {/* Features Section */}
        <section className="py-20 bg-white">
          <div className="max-w-7xl mx-auto px-6">
            <div className="text-center mb-16">
              <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
                Why Choose <span className="text-gradient">JobSleuth AI</span>?
              </h2>
              <p className="text-xl text-gray-600 max-w-2xl mx-auto">
                Leverage cutting-edge AI technology to accelerate your job search
              </p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {/* Feature 1 */}
              <div className="card card-hover p-8 text-center group">
                <div className="w-16 h-16 mx-auto mb-6 bg-gradient-ai rounded-2xl flex items-center justify-center shadow-glow transform group-hover:scale-110 transition-transform duration-200">
                  <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                  </svg>
                </div>
                <h3 className="text-2xl font-bold mb-3 text-gray-900">AI-Powered Matching</h3>
                <p className="text-gray-600 leading-relaxed">
                  Get personalized job recommendations with AI-calculated fit scores based on your skills, experience, and career goals.
                </p>
              </div>

              {/* Feature 2 */}
              <div className="card card-hover p-8 text-center group">
                <div className="w-16 h-16 mx-auto mb-6 bg-gradient-to-br from-emerald-500 to-teal-500 rounded-2xl flex items-center justify-center shadow-lg transform group-hover:scale-110 transition-transform duration-200">
                  <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <h3 className="text-2xl font-bold mb-3 text-gray-900">Real-Time Updates</h3>
                <p className="text-gray-600 leading-relaxed">
                  Access the latest job postings from multiple sources in real-time, all aggregated in one powerful platform.
                </p>
              </div>

              {/* Feature 3 */}
              <div className="card card-hover p-8 text-center group">
                <div className="w-16 h-16 mx-auto mb-6 bg-gradient-to-br from-orange-500 to-pink-500 rounded-2xl flex items-center justify-center shadow-lg transform group-hover:scale-110 transition-transform duration-200">
                  <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
                  </svg>
                </div>
                <h3 className="text-2xl font-bold mb-3 text-gray-900">Save & Organize</h3>
                <p className="text-gray-600 leading-relaxed">
                  Keep track of interesting opportunities, organize your applications, and manage your job search efficiently.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Stats Section */}
        <section className="py-20 bg-gradient-to-br from-brand-600 to-purple-600 text-white">
          <div className="max-w-7xl mx-auto px-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-12 text-center">
              <div>
                <div className="text-5xl font-bold mb-2">10,000+</div>
                <div className="text-xl text-brand-100">Active Job Listings</div>
              </div>
              <div>
                <div className="text-5xl font-bold mb-2">95%</div>
                <div className="text-xl text-brand-100">AI Match Accuracy</div>
              </div>
              <div>
                <div className="text-5xl font-bold mb-2">24/7</div>
                <div className="text-xl text-brand-100">Real-Time Updates</div>
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
