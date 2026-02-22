import { describe, it, expect } from 'vitest';
import { searchCases } from '../src/search/engine.js';
import { Case } from '../src/core/types.js';

function makeCase(partial: Partial<Case> & { caseId: string }): Case {
  return {
    summary: '',
    symptoms: [],
    environment: {},
    errorPatterns: [],
    tags: [],
    contentRedacted: '',
    wordCount: 0,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    ...partial,
  };
}

describe('searchCases', () => {
  const cases: Record<string, Case> = {
    'ICM-1': makeCase({ caseId: 'ICM-1', summary: 'AMA timeout on Windows', tags: ['Windows', 'Timeout'], contentRedacted: 'AMA timeout error' }),
    'ICM-2': makeCase({ caseId: 'ICM-2', summary: 'Linux connection failure', tags: ['Linux', 'Connection'], contentRedacted: 'Linux conn failed' }),
    'ICM-3': makeCase({ caseId: 'ICM-3', summary: 'Storage latency', tags: ['Azure'], errorPatterns: ['StorageException timeout'] }),
  };

  it('finds cases by summary keyword', () => {
    const results = searchCases(cases, 'timeout');
    expect(results.length).toBeGreaterThan(0);
    expect(results.some((r) => r.caseId === 'ICM-1')).toBe(true);
  });

  it('ranks summary matches higher than content matches', () => {
    const results = searchCases(cases, 'timeout');
    const summaryMatch = results.find((r) => r.caseId === 'ICM-1');
    const contentMatch = results.find((r) => r.caseId === 'ICM-3');
    if (summaryMatch && contentMatch) {
      expect(summaryMatch.score).toBeGreaterThan(contentMatch.score);
    }
  });

  it('finds cases by tag', () => {
    const results = searchCases(cases, 'linux');
    expect(results.some((r) => r.caseId === 'ICM-2')).toBe(true);
  });

  it('returns empty array when no matches', () => {
    const results = searchCases(cases, 'zyxwvuts');
    expect(results).toHaveLength(0);
  });

  it('respects limit option', () => {
    const results = searchCases(cases, 'timeout', { limit: 1 });
    expect(results).toHaveLength(1);
  });
});
