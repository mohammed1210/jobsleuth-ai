/** A same-owner auth refresh is not a new vacancy/evidence session. */
export function preserveVacancySession(
  event: string,
  previousUserId: string | null,
  nextUserId: string | null,
): boolean {
  return Boolean(previousUserId && nextUserId && previousUserId === nextUserId
    && (event === 'SIGNED_IN' || event === 'TOKEN_REFRESHED' || event === 'INITIAL_SESSION'));
}
