'use client';

import { useState, useEffect } from 'react';
import JobCard from '@/components/JobCard';

export default function JobsPage() {
  const [jobs, setJobs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [location, setLocation] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const perPage = 10;

  useEffect(() => {
    fetchJobs();
  }, [page, searchQuery, location]);

  const fetchJobs = async () => {
    setLoading(true);
    try {
      // Mock data for now - will be replaced with actual API call
      const mockJobs = [
        {
          id: 1,
          title: 'Senior Software Engineer',
          company: 'TechCorp',
          location: 'San Francisco, CA',
          salary: '$120k - $180k',
          source: 'Indeed',
          date_posted: '2 days ago',
          url: 'https://example.com/job/1'
        },
        {
          id: 2,
          title: 'Frontend Developer',
          company: 'StartupXYZ',
          location: 'Remote',
          salary: '$90k - $130k',
          source: 'LinkedIn',
          date_posted: '1 week ago',
          url: 'https://example.com/job/2'
        },
        {
          id: 3,
          title: 'Full Stack Engineer',
          company: 'BigTech Inc',
          location: 'New York, NY',
          salary: '$100k - $150k',
          source: 'Indeed',
          date_posted: '3 days ago',
          url: 'https://example.com/job/3'
        },
      ];
      
      setJobs(mockJobs);
      setTotalPages(3);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch jobs:', error);
      setLoading(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchJobs();
  };

  const handleSaveJob = async (jobId: number) => {
    console.log('Saving job:', jobId);
    // TODO: Implement actual save logic with API
  };

  return (
    <main className="max-w-6xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">Find Your Next Job</h1>
      
      {/* Search and Filters */}
      <form onSubmit={handleSearch} className="mb-8 bg-white p-4 rounded-lg shadow">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label htmlFor="search" className="block text-sm font-medium text-gray-700 mb-1">
              Job Title or Keywords
            </label>
            <input
              id="search"
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="e.g. Software Engineer"
              className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
          </div>
          <div>
            <label htmlFor="location" className="block text-sm font-medium text-gray-700 mb-1">
              Location
            </label>
            <input
              id="location"
              type="text"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="e.g. San Francisco"
              className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
          </div>
          <div className="flex items-end">
            <button
              type="submit"
              className="w-full bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2 rounded font-medium transition-colors"
            >
              Search
            </button>
          </div>
        </div>
      </form>

      {/* Job Listings */}
      {loading ? (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-gray-200 border-t-indigo-600"></div>
          <p className="mt-2 text-gray-600">Loading jobs...</p>
        </div>
      ) : (
        <>
          <div className="mb-4 text-sm text-gray-600">
            Showing {jobs.length} jobs
          </div>
          
          <div className="space-y-4 mb-8">
            {jobs.map((job) => (
              <JobCard 
                key={job.id} 
                job={job}
                onSave={handleSaveJob}
              />
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex justify-center gap-2">
              <button
                onClick={() => setPage(Math.max(1, page - 1))}
                disabled={page === 1}
                className="px-4 py-2 border rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
              >
                Previous
              </button>
              <span className="px-4 py-2">
                Page {page} of {totalPages}
              </span>
              <button
                onClick={() => setPage(Math.min(totalPages, page + 1))}
                disabled={page === totalPages}
                className="px-4 py-2 border rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </main>
  );
}
