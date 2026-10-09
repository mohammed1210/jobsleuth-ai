export type EvidenceLike = {
  title?: string;
  situation?: string;
  task?: string;
  actions?: string[];
  outcome?: string;
};

const STOPWORDS = new Set([
  'and', 'the', 'that', 'this', 'with', 'from', 'into', 'for', 'was', 'were',
  'have', 'had', 'has', 'then', 'when', 'while', 'their', 'they', 'them',
  'your', 'our', 'you', 'role', 'work', 'working',
]);

function normalise(value: string) {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function tokens(card: EvidenceLike) {
  const text = [
    card.situation ?? '',
    card.task ?? '',
    ...(card.actions ?? []),
    card.outcome ?? '',
  ].join(' ');

  return new Set(
    normalise(text)
      .split(' ')
      .filter((token) => token.length >= 3 && !STOPWORDS.has(token)),
  );
}

function exactActionOverlap(left: EvidenceLike, right: EvidenceLike) {
  const rightActions = new Set((right.actions ?? []).map(normalise).filter(Boolean));
  return (left.actions ?? []).some((action) => rightActions.has(normalise(action)));
}

export function evidenceSimilarity(left: EvidenceLike, right: EvidenceLike) {
  const a = tokens(left);
  const b = tokens(right);
  if (!a.size || !b.size) return 0;

  let intersection = 0;
  for (const token of a) {
    if (b.has(token)) intersection += 1;
  }
  const union = new Set([...a, ...b]).size;
  return union ? intersection / union : 0;
}

export function isLikelyDuplicate(left: EvidenceLike, right: EvidenceLike) {
  const sameTitle = Boolean(
    left.title
    && right.title
    && normalise(left.title) === normalise(right.title),
  );
  const similarity = evidenceSimilarity(left, right);

  if (exactActionOverlap(left, right) && similarity >= 0.45) return true;
  if (sameTitle && similarity >= 0.58) return true;
  return similarity >= 0.78;
}

export function dedupeImportedEvidence<T extends EvidenceLike>(
  suggestions: T[],
  existing: EvidenceLike[],
) {
  const unique: T[] = [];
  let skipped = 0;

  for (const suggestion of suggestions) {
    const duplicate = existing.some((card) => isLikelyDuplicate(suggestion, card))
      || unique.some((card) => isLikelyDuplicate(suggestion, card));
    if (duplicate) {
      skipped += 1;
      continue;
    }
    unique.push(suggestion);
  }

  return { unique, skipped };
}

export function canQuickSaveImportedEvidence(card: EvidenceLike) {
  return Boolean(
    (card.situation?.trim() || card.task?.trim())
    && (card.actions ?? []).some((action) => action.trim())
    && card.outcome?.trim(),
  );
}
