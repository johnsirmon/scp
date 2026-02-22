import { Case, SearchResult } from '../core/types.js';

export function searchCases(
  cases: Record<string, Case>,
  query: string,
  options: { limit?: number } = {},
): SearchResult[] {
  const q = query.toLowerCase();
  const results: SearchResult[] = [];

  for (const [caseId, c] of Object.entries(cases)) {
    let score = 0;
    const matches: string[] = [];

    if (c.summary.toLowerCase().includes(q)) { score += 10; matches.push('summary'); }
    for (const s of c.symptoms) {
      if (s.toLowerCase().includes(q)) { score += 8; matches.push('symptoms'); break; }
    }
    for (const e of c.errorPatterns) {
      if (e.toLowerCase().includes(q)) { score += 9; matches.push('errors'); break; }
    }
    for (const t of c.tags) {
      if (t.toLowerCase().includes(q)) { score += 5; matches.push('tags'); break; }
    }
    if (c.contentRedacted.toLowerCase().includes(q)) { score += 3; matches.push('content'); }

    if (score > 0) {
      results.push({ caseId, score, matches: [...new Set(matches)], summary: c.summary, tags: c.tags, createdAt: c.createdAt });
    }
  }

  return results.sort((a, b) => b.score - a.score).slice(0, options.limit ?? 10);
}
