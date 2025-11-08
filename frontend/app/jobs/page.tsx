/**
 * Jobs Listing Page
 *
 * Search and browse jobs with filters and pagination
 */

import { Suspense } from 'react';
import Link from 'next/link';
import JobCard from '@/components/JobCard';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Job {
  id: string;
  title: string;
  company: string;
  location?: string;
  salary_text?: string;
  salary_min?: number;
  salary_max?: number;
  type?: string;
  posted_at?: string;
}

interface JobsResponse {
  jobs: Job[];
  pagination: {
    page: number;
    per_page: number;
    total: number;
    total_pages: number;
    has_next: boolean;
    has_prev: boolean;
  };
}

async function getJobs(searchParams: any): Promise<JobsResponse> {
  const params = new URLSearchParams();
  
  if (searchParams.q) params.set('q', searchParams.q);
  if (searchParams.location) params.set('location', searchParams.location);
  if (searchParams.minSalary) params.set('minSalary', searchParams.minSalary);
  if (searchParams.type) params.set('type', searchParams.type);
  params.set('page', searchParams.page || '1');
  params.set('per_page', '20');

  try {
    const response = await fetch(`${API_URL}/jobs?${params.toString()}`, {
      cache: 'no-store',
    });

    if (!response.ok) {
      throw new Error('Failed to fetch jobs');
    }

    return response.json();
  } catch (error) {
    console.error('Error fetching jobs:', error);
    return {
      jobs: [],
      pagination: {
        page: 1,
        per_page: 20,
        total: 0,
        total_pages: 0,
        has_next: false,
        has_prev: false,
      },
    };
  }
}

export default async function JobsPage({
  searchParams,
}: {
  searchParams: { [key: string]: string | undefined };
}) {
  const data = await getJobs(searchParams);
  const { jobs, pagination } = data;

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Header with Search */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-6">Job Listings</h1>

          {/* Search and Filters */}
          <form method="get" action="/jobs" className="space-y-4">
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Search Query */}
              <input
                type="search"
                name="q"
                defaultValue={searchParams.q || ''}
                placeholder="Search jobs..."
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />

              {/* Location Filter */}
              <input
                type="text"
                name="location"
                defaultValue={searchParams.location || ''}
                placeholder="Location..."
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />

              {/* Salary Filter */}
              <input
                type="number"
                name="minSalary"
                defaultValue={searchParams.minSalary || ''}
                placeholder="Min Salary..."
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />

              {/* Type Filter */}
              <select
                name="type"
                defaultValue={searchParams.type || ''}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white"
              >
                <option value="">All Types</option>
                <option value="Full-time">Full-time</option>
                <option value="Part-time">Part-time</option>
                <option value="Contract">Contract</option>
                <option value="Internship">Internship</option>
              </select>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Apply Filters
            </button>

            {/* Clear Filters */}
            {(searchParams.q || searchParams.location || searchParams.minSalary || searchParams.type) && (
              <Link
                href="/jobs"
                className="ml-4 px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors inline-block"
              >
                Clear Filters
              </Link>
            )}
          </form>
        </div>

        {/* Results Count */}
        <div className="mb-4 text-gray-600">
          {pagination.total > 0 ? (
            <p>
              Showing {(pagination.page - 1) * pagination.per_page + 1} -{' '}
              {Math.min(pagination.page * pagination.per_page, pagination.total)} of{' '}
              {pagination.total} jobs
            </p>
          ) : (
            <p>No jobs found. Try adjusting your filters.</p>
          )}
        </div>

        {/* Job Listings */}
        <div className="space-y-4 mb-8">
          <Suspense
            fallback={
              <div className="text-center py-12">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                <p className="mt-2 text-gray-600">Loading jobs...</p>
              </div>
            }
          >
            {jobs.map(job => (
              <JobCard key={job.id} job={job} />
            ))}
          </Suspense>
        </div>

        {/* Pagination */}
        {pagination.total_pages > 1 && (
          <div className="flex justify-center items-center gap-2">
            {pagination.has_prev && (
              <Link
                href={`/jobs?${new URLSearchParams({
                  ...searchParams,
                  page: String(pagination.page - 1),
                }).toString()}`}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Previous
              </Link>
            )}

            <span className="px-4 py-2 text-gray-700">
              Page {pagination.page} of {pagination.total_pages}
            </span>

            {pagination.has_next && (
              <Link
                href={`/jobs?${new URLSearchParams({
                  ...searchParams,
                  page: String(pagination.page + 1),
                }).toString()}`}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Next
              </Link>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
