const LOCAL_BACKEND_URL = 'http://localhost:8000';

export function getBackendUrl(): string {
  const configured = process.env.NEXT_PUBLIC_BACKEND_URL?.trim();

  if (configured) {
    return configured.replace(/\/$/, '');
  }

  if (process.env.NODE_ENV === 'development') {
    return LOCAL_BACKEND_URL;
  }

  throw new Error('JobSleuth API is not configured. Set NEXT_PUBLIC_BACKEND_URL in Vercel.');
}

export async function apiError(response: Response, fallback: string): Promise<Error> {
  let detail = '';

  try {
    const payload = await response.json();
    if (typeof payload?.detail === 'string') detail = payload.detail;
  } catch {
    try {
      detail = (await response.text()).trim();
    } catch {
      detail = '';
    }
  }

  const suffix = detail ? `: ${detail}` : ` (HTTP ${response.status})`;
  return new Error(`${fallback}${suffix}`);
}
