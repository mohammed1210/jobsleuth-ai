import type { Job } from './api';

/** Local-only routes: never accept a publisher URL as an auth return target. */
export function applicationPath(jobId: number): string {
  if (!Number.isSafeInteger(jobId) || jobId <= 0) throw new Error('Invalid job ID');
  return `/apply/vacancy?job=${jobId}`;
}

export function signInPathForJob(jobId: number): string {
  return `/login?next=${encodeURIComponent(applicationPath(jobId))}`;
}

export function safeLoginReturnPath(value: string | null): string {
  if (!value || !/^\/apply\/vacancy\?job=[1-9][0-9]{0,14}$/.test(value)) {
    return '/apply/vacancy';
  }
  const id = Number(value.slice('/apply/vacancy?job='.length));
  return Number.isSafeInteger(id) ? applicationPath(id) : '/apply/vacancy';
}

/** Facts from the official feed, not a generated application or match score. */
export function advertForApplication(job: Job): string {
  const fields = [
    `Job title: ${job.title}`,
    `Employer: ${job.company}`,
    `Location: ${job.location}`,
    job.role_type ? `Working pattern: ${job.role_type}` : '',
    job.salary ? `Advertised salary: ${job.salary}` : '',
    job.expires_at ? `Applications close: ${job.expires_at}` : '',
    job.url ? `Original advertisement: ${job.url}` : '',
    '',
    'Publisher-supplied job description (review original for full criteria and application instructions):',
    job.description?.trim() || 'No description supplied by the publisher. Review the original advert before extracting criteria.',
  ];
  return fields.filter((line) => line !== '').join('\n\n');
}
