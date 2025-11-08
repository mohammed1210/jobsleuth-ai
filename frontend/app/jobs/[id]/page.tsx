'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';

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
        required_skills: ['JavaScript', 'TypeScript', 'React', 'Node.js'],
      };
      
      setJob(mockJob);
      
      // Mock AI score if feature is enabled
      if (featureAiFit) {
        setAiScore({
          overall_score: 0.82,
          skills_score: 0.75,
          title_score: 0.88,
          location_score: 0.90,
          salary_score: 0.80,
          seniority_score: 0.85,
        });
      }
      
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
      <main className="max-w-4xl mx-auto px-4 py-8">
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-gray-200 border-t-indigo-600"></div>
          <p className="mt-2 text-gray-600">Loading job details...</p>
        </div>
      </main>
    );
  }

  if (!job) {
    return (
      <main className="max-w-4xl mx-auto px-4 py-8">
        <div className="text-center py-12">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Job Not Found</h1>
          <Link href="/jobs" className="text-indigo-600 hover:text-indigo-700">
            ← Back to Jobs
          </Link>
        </div>
      </main>
    );
  }

  return (
    <main className="max-w-4xl mx-auto px-4 py-8">
      <Link href="/jobs" className="text-indigo-600 hover:text-indigo-700 mb-4 inline-block">
        ← Back to Jobs
      </Link>

      <div className="bg-white rounded-lg shadow-lg overflow-hidden">
        {/* Header */}
        <div className="p-6 border-b">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">{job.title}</h1>
          <p className="text-xl text-gray-700 mb-4">{job.company}</p>
          
          <div className="flex flex-wrap gap-2 mb-4">
            <span className="inline-flex items-center px-3 py-1 bg-gray-100 text-gray-700 text-sm rounded">
              📍 {job.location}
            </span>
            {job.salary && (
              <span className="inline-flex items-center px-3 py-1 bg-green-100 text-green-700 text-sm rounded">
                💰 {job.salary}
              </span>
            )}
            {job.source && (
              <span className="inline-flex items-center px-3 py-1 bg-blue-100 text-blue-700 text-sm rounded">
                {job.source}
              </span>
            )}
          </div>
          
          {job.date_posted && (
            <p className="text-sm text-gray-500">Posted: {job.date_posted}</p>
          )}
        </div>

        {/* Sticky Actions Bar */}
        <div className="sticky top-0 bg-white border-b p-4 flex gap-3 z-10">
          <button
            onClick={handleSave}
            className={`flex-1 px-4 py-2 rounded font-medium transition-colors ${
              saved
                ? 'bg-indigo-600 text-white hover:bg-indigo-700'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {saved ? '✓ Saved' : 'Save'}
          </button>
          <button
            onClick={handleShare}
            className="flex-1 px-4 py-2 bg-gray-100 text-gray-700 rounded font-medium hover:bg-gray-200 transition-colors"
          >
            Share
          </button>
          {job.url && (
            <a
              href={job.url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex-1 px-4 py-2 bg-indigo-600 text-white rounded font-medium hover:bg-indigo-700 transition-colors text-center"
            >
              Apply ↗
            </a>
          )}
        </div>

        <div className="p-6">
          {/* AI Fit Panel */}
          {featureAiFit && aiScore && (
            <div className="mb-6 bg-indigo-50 border border-indigo-200 rounded-lg p-4">
              <h2 className="text-lg font-semibold text-indigo-900 mb-3">AI Match Score</h2>
              <div className="mb-3">
                <div className="flex justify-between items-center mb-1">
                  <span className="text-sm font-medium text-indigo-800">Overall Fit</span>
                  <span className="text-sm font-bold text-indigo-900">
                    {Math.round(aiScore.overall_score * 100)}%
                  </span>
                </div>
                <div className="w-full bg-indigo-200 rounded-full h-2">
                  <div
                    className="bg-indigo-600 h-2 rounded-full"
                    style={{ width: `${aiScore.overall_score * 100}%` }}
                  ></div>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div>
                  <span className="text-gray-700">Skills:</span>{' '}
                  <span className="font-medium">{Math.round(aiScore.skills_score * 100)}%</span>
                </div>
                <div>
                  <span className="text-gray-700">Title:</span>{' '}
                  <span className="font-medium">{Math.round(aiScore.title_score * 100)}%</span>
                </div>
                <div>
                  <span className="text-gray-700">Location:</span>{' '}
                  <span className="font-medium">{Math.round(aiScore.location_score * 100)}%</span>
                </div>
                <div>
                  <span className="text-gray-700">Salary:</span>{' '}
                  <span className="font-medium">{Math.round(aiScore.salary_score * 100)}%</span>
                </div>
              </div>
            </div>
          )}

          {/* Job Description */}
          <div className="prose max-w-none">
            <div dangerouslySetInnerHTML={{ __html: job.description }} />
          </div>
          
          {/* Required Skills */}
          {job.required_skills && job.required_skills.length > 0 && (
            <div className="mt-6">
              <h3 className="text-lg font-semibold mb-2">Required Skills</h3>
              <div className="flex flex-wrap gap-2">
                {job.required_skills.map((skill: string, index: number) => (
                  <span
                    key={index}
                    className="px-3 py-1 bg-indigo-100 text-indigo-700 rounded-full text-sm"
                  >
                    {skill}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
