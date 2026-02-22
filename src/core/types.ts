import { z } from 'zod';

export const CaseSchema = z.object({
  caseId: z.string(),
  summary: z.string(),
  symptoms: z.array(z.string()),
  environment: z.record(z.string(), z.string()),
  errorPatterns: z.array(z.string()),
  tags: z.array(z.string()),
  contentRedacted: z.string(),
  wordCount: z.number(),
  createdAt: z.string(),
  updatedAt: z.string(),
});

export type Case = z.infer<typeof CaseSchema>;

export const SearchResultSchema = z.object({
  caseId: z.string(),
  score: z.number(),
  matches: z.array(z.string()),
  summary: z.string(),
  tags: z.array(z.string()),
  createdAt: z.string(),
});

export type SearchResult = z.infer<typeof SearchResultSchema>;

export interface ContextExport {
  contextType: 'support_cases';
  totalCases: number;
  generatedAt: string;
  cases: CaseContext[];
}

export interface CaseContext {
  caseId: string;
  summary: string;
  symptoms: string[];
  environment: Record<string, string>;
  keyErrors: string[];
  tags: string[];
  contentPreview: string;
}

export interface Stats {
  totalCases: number;
  casesWithPii: number;
  topTags: Array<{ tag: string; count: number }>;
  dataSize: number;
}
