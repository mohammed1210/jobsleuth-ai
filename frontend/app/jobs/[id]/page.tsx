'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import HeaderClient from '@/components/HeaderClient';

export default function JobDetailPage() {
  const params = useParams();
  const jobId = params?.id;
  const [job, setJob] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [saved, setSaved] = useState(false);
  const [aiScore, setAiScore] = useState<any>(null);
  const featureAiFit = process.env.NEXT_PUBLIC_FEATURE_AI_FIT === 'true';

  useEffect(() => {
    if (jobId) {
      fetchJobDetail();
    }
  }, [jobId]);

  const fetchJobDetail = async () => {
    setLoading(true);
    try {
      // Mock data for now - will be replaced with actual API call
      const mockJob = {
        id: jobId,
        title: 'Senior Software Engineer',
        company: 'TechCorp',
        location: 'San Francisco, CA',
        salary: '$120k - $180k',
        source: 'Indeed',
        date_posted: '2 days ago',
        url: 'https://example.com/job/' + jobId,
        description: `
          <h3>About the Role</h3>
          <p>We are seeking a talented Senior Software Engineer to join our growing team. In this role, you will work on cutting-edge technologies and help shape the future of our products.</p>
          
          <h3>Responsibilities</h3>
          <ul>
            <li>Design and develop scalable web applications</li>
            <li>Collaborate with cross-functional teams</li>
            <li>Write clean, maintainable code</li>
            <li>Mentor junior developers</li>
          </ul>
          
          <h3>Requirements</h3>
          <ul>
            <li>5+ years of software development experience</li>
            <li>Strong proficiency in JavaScript/TypeScript</li>
            <li>Experience with React and Node.js</li>
            <li>Excellent problem-solving skills</li>
          </ul>
        `,
        required_skills: ['JavaScript', 'TypeScript', 'React', 'Node.js', 'AWS', 'Docker'],
      };
      
      setJob(mockJob);
      
      // Mock AI score - always show for demonstration
      setAiScore({
        overall_score: 0.85,
        skills_score: 0.80,
        title_score: 0.90,
        location_score: 0.88,
        salary_score: 0.82,
        seniority_score: 0.87,
      });
      
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch job:', error);
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaved(!saved);
    // TODO: Implement actual save logic
  };

  const handleShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: job?.title,
          text: `Check out this job: ${job?.title} at ${job?.company}`,
          url: window.location.href,
        });
      } catch (error) {
        console.error('Error sharing:', error);
      }
    } else {
      // Fallback: copy to clipboard
      navigator.clipboard.writeText(window.location.href);
      alert('Link copied to clipboard!');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen">
        <HeaderClient />
        <main className="max-w-5xl mx-auto px-6 py-12">
          <div className="text-center py-20">
            <div className="inline-flex items-center justify-center">
              <div className="w-12 h-12 border-4 border-brand-200 border-t-brand-600 rounded-full animate-spin"></div>
            </div>
            <p className="mt-4 text-lg text-gray-600 font-medium">Loading job details...</p>
          </div>
        </main>
      </div>
    );
  }

  if (!job) {
    return (
      <div className="min-h-screen">
        <HeaderClient />
        <main className="max-w-5xl mx-auto px-6 py-12">
          <div className="text-center py-20">
            <h1 className="text-3xl font-bold text-gray-900 mb-4">Job Not Found</h1>
            <Link href="/jobs" className="btn-primary inline-flex items-center">
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              Back to Jobs
            </Link>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <HeaderClient />
      
      <main className="max-w-5xl mx-auto px-6 py-8">
        {/* Back Button */}
        <Link href="/jobs" className="inline-flex items-center text-brand-600 hover:text-brand-700 font-medium mb-6 group">
          <svg className="w-5 h-5 mr-2 transition-transform group-hover:-translate-x-1" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          Back to Jobs
        </Link>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Job Header Card */}
            <div className="card p-8">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h1 className="text-4xl font-bold text-gray-900 mb-2">{job.title}</h1>
                  <p className="text-2xl text-gray-700 font-semibold mb-4">{job.company}</p>
                </div>
                <button
                  onClick={handleSave}
                  className={`p-3 rounded-xl transition-all ${
                    saved
                      ? 'bg-brand-100 text-brand-600 hover:bg-brand-200'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                  aria-label={saved ? 'Unsave job' : 'Save job'}
                >
                  <svg className="w-6 h-6" fill={saved ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
                  </svg>
                </button>
              </div>
              
              <div className="flex flex-wrap gap-3 mb-6">
                <span className="inline-flex items-center px-4 py-2 bg-gray-100 text-gray-700 text-sm font-semibold rounded-lg">
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  {job.location}
                </span>
                {job.salary && (
                  <span className="inline-flex items-center px-4 py-2 bg-emerald-100 text-emerald-700 text-sm font-semibold rounded-lg">
                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    {job.salary}
                  </span>
                )}
                {job.source && (
                  <span className="inline-flex items-center px-4 py-2 bg-blue-100 text-blue-700 text-sm font-semibold rounded-lg">
                    via {job.source}
                  </span>
                )}
              </div>
              
              {job.date_posted && (
                <p className="text-sm text-gray-500">Posted {job.date_posted}</p>
              )}

              {/* Action Buttons */}
              <div className="mt-6 flex gap-3">
                {job.url && (
                  <a
                    href={job.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex-1 btn-primary text-center flex items-center justify-center"
                  >
                    Apply Now
                    <svg className="w-5 h-5 ml-2" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                    </svg>
                  </a>
                )}
                <button
                  onClick={handleShare}
                  className="px-6 py-3 bg-gray-100 text-gray-700 rounded-xl font-semibold hover:bg-gray-200 transition-all"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
                  </svg>
                </button>
              </div>
            </div>

            {/* Job Description Card */}
            <div className="card p-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Job Description</h2>
              <div className="prose prose-lg max-w-none prose-headings:text-gray-900 prose-p:text-gray-600 prose-li:text-gray-600 prose-strong:text-gray-900">
                <div dangerouslySetInnerHTML={{ __html: job.description }} />
              </div>
            </div>

            {/* Required Skills */}
            {job.required_skills && job.required_skills.length > 0 && (
              <div className="card p-8">
                <h3 className="text-2xl font-bold text-gray-900 mb-4">Required Skills</h3>
                <div className="flex flex-wrap gap-3">
                  {job.required_skills.map((skill: string, index: number) => (
                    <span
                      key={index}
                      className="px-4 py-2 bg-gradient-to-r from-brand-100 to-purple-100 text-brand-700 rounded-lg text-sm font-semibold border border-brand-200"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="lg:col-span-1 space-y-6">
            {/* AI Match Score Card */}
            {aiScore && (
              <div className="card overflow-hidden sticky top-24">
                <div className="bg-gradient-ai p-6 text-white">
                  <div className="flex items-center space-x-2 mb-3">
                    <div className="w-8 h-8 bg-white/20 rounded-lg flex items-center justify-center">
                      <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                      </svg>
                    </div>
                    <h3 className="text-lg font-bold">AI Match Score</h3>
                  </div>
                  <div className="text-5xl font-bold mb-2">
                    {Math.round(aiScore.overall_score * 100)}%
                  </div>
                  <p className="text-white/90 text-sm">
                    This job is an excellent match for your profile
                  </p>
                </div>
                
                <div className="p-6 space-y-4">
                  {[
                    { label: 'Skills Match', score: aiScore.skills_score, icon: '🎯' },
                    { label: 'Title Relevance', score: aiScore.title_score, icon: '💼' },
                    { label: 'Location Fit', score: aiScore.location_score, icon: '📍' },
                    { label: 'Salary Range', score: aiScore.salary_score, icon: '💰' },
                    { label: 'Seniority Level', score: aiScore.seniority_score, icon: '📊' },
                  ].map((item, index) => (
                    <div key={index}>
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-sm font-medium text-gray-700 flex items-center">
                          <span className="mr-2">{item.icon}</span>
                          {item.label}
                        </span>
                        <span className="text-sm font-bold text-brand-600">
                          {Math.round(item.score * 100)}%
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-gradient-ai h-2 rounded-full transition-all duration-500"
                          style={{ width: `${item.score * 100}%` }}
                        ></div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Company Info Card */}
            <div className="card p-6">
              <h3 className="text-xl font-bold text-gray-900 mb-4">About {job.company}</h3>
              <p className="text-gray-600 text-sm leading-relaxed">
                {job.company} is a leading technology company focused on innovation and excellence. 
                Join a team of talented professionals working on cutting-edge projects.
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
