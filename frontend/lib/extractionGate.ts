/** Prevent stale async extraction results from crossing draft or session changes. */
export function createExtractionGate() {
  let generation = 0;
  return {
    begin(): number { return ++generation; },
    invalidate(): void { generation++; },
    isCurrent(token: number): boolean { return token === generation; },
  };
}
