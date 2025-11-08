'use client';

import { useState, useEffect } from 'react';
import { createClient } from '@supabase/supabase-js';
import JobCard from '@/components/JobCard';
import Link from 'next/link';

export default function SavedJobsPage() {
  const [savedJobs, setSavedJobs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    const supabase = createClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL as string,
      process.env.NEXT_PUBLIC_SUPABASE_KEY as string,
    );
    
    const { data } = await supabase.auth.getUser();
    
    if (data.user) {
      setUser(data.user);
      fetchSavedJobs(data.user.id);
    } else {
      setLoading(false);
    }
  };

  const fetchSavedJobs = async (userId: string) => {
    setLoading(true);
    try {
      // Mock data for now - will be replaced with actual API call
      const mockSavedJobs = [
        {
          id: 1,
          title: 'Senior Software Engineer',
          company: 'TechCorp',
          location: 'San Francisco, CA',
          salary: '$120k - $180k',
          source: 'Indeed',
          date_posted: '2 days ago',
          url: 'https://example.com/job/1',
          saved_at: '2024-01-15'
        },
        {
          id: 2,
          title: 'Frontend Developer',
          company: 'StartupXYZ',
          location: 'Remote',
          salary: '$90k - $130k',
          source: 'LinkedIn',
          date_posted: '1 week ago',
          url: 'https://example.com/job/2',
          saved_at: '2024-01-14'
        },
      ];
      
      setSavedJobs(mockSavedJobs);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch saved jobs:', error);
      setLoading(false);
    }
  };

  const handleUnsave = async (jobId: number) => {
    // Remove from saved jobs
    setSavedJobs(savedJobs.filter(job => job.id !== jobId));
    // TODO: Implement actual unsave logic with API
  };

  if (!user && !loading) {
    return (
      <main className="max-w-4xl mx-auto px-4 py-8">
        <div className="text-center py-12">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Sign In Required</h1>
          <p className="text-gray-600 mb-6">You need to sign in to view your saved jobs.</p>
          <Link 
            href="/magic-login"
            className="inline-block bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-3 rounded font-medium"
          >
            Sign In
          </Link>
        </div>
      </main>
    );
  }

  return (
    <main className="max-w-6xl mx-auto px-4 py-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">Saved Jobs</h1>
        <p className="text-gray-600">
          {savedJobs.length} {savedJobs.length === 1 ? 'job' : 'jobs'} saved
        </p>
      </div>

      {loading ? (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-gray-200 border-t-indigo-600"></div>
          <p className="mt-2 text-gray-600">Loading saved jobs...</p>
        </div>
      ) : savedJobs.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <p className="text-gray-600 mb-4">You haven't saved any jobs yet.</p>
          <Link 
            href="/jobs"
            className="inline-block text-indigo-600 hover:text-indigo-700 font-medium"
          >
            Browse Jobs →
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          {savedJobs.map((job) => (
            <JobCard 
              key={job.id} 
              job={job}
              onSave={handleUnsave}
              saved={true}
            />
          ))}
        </div>
      )}
    </main>
  );
}
