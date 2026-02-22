import { Case, ContextExport, CaseContext } from '../core/types.js';

export function toCaseContext(caseId: string, c: Case): CaseContext {
  return {
    caseId,
    summary: c.summary,
    symptoms: c.symptoms.slice(0, 3),
    environment: c.environment as Record<string, string>,
    keyErrors: c.errorPatterns.slice(0, 3),
    tags: c.tags,
    contentPreview: c.contentRedacted.substring(0, 500) + (c.contentRedacted.length > 500 ? '...' : ''),
  };
}

export function exportContext(cases: Record<string, Case>, caseIds: string[]): ContextExport {
  const contextCases = caseIds
    .map((id) => (cases[id] ? toCaseContext(id, cases[id]) : null))
    .filter((c): c is CaseContext => c !== null);

  return {
    contextType: 'support_cases',
    totalCases: contextCases.length,
    generatedAt: new Date().toISOString(),
    cases: contextCases,
  };
}
