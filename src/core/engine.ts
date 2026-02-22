import { Case, SearchResult, Stats, ContextExport } from './types.js';
import { PolicyConfig } from '../policy/types.js';
import { redactPii, rehydrate } from '../pii/redactor.js';
import { StorageBackend } from '../storage/types.js';
import { searchCases } from '../search/engine.js';
import { exportContext, toCaseContext } from '../context/exporter.js';

const TAG_PATTERNS: Record<string, RegExp> = {
  AMA: /\bAMA\b/i,
  Windows: /\bWindows\b/i,
  Linux: /\bLinux\b|\bRedHat\b/i,
  MetricsExtension: /\bMetricsExtension\b/i,
  InfluxDB: /\bInfluxDb\b/i,
  Telegraf: /\bTelegraf\b/i,
  Timeout: /\btimeout\b/i,
  Connection: /\bconnection\b/i,
  Azure: /\bAzure\b/i,
};

const CASE_ID_PATTERNS = [
  /ICM[:-](\d+)/i,
  /Incident[:-](\d+)/i,
  /Support Request Number:\s*(\d+)/i,
  /Support[:-](\d+)/i,
];

const ENV_PATTERNS: Record<string, RegExp> = {
  subscriptionId: /Subscription ID[:\s]*([a-f0-9-]{36})/i,
  workspaceId: /Workspace ID[:\s]*([a-f0-9-]{36})/i,
  agentVersion: /Agent version[:\s]*([0-9.]+)/i,
  osVersion: /Major OS Version[:\s]*([^:\n]+)/i,
};

function generateTags(content: string): string[] {
  return Object.entries(TAG_PATTERNS)
    .filter(([, p]) => p.test(content))
    .map(([tag]) => tag);
}

function parseEnvironment(content: string): Record<string, string> {
  const env: Record<string, string> = {};
  for (const [key, pattern] of Object.entries(ENV_PATTERNS)) {
    const m = content.match(pattern);
    if (m?.[1]) env[key] = m[1].trim();
  }
  return env;
}

function extractCaseId(content: string): string | null {
  for (const p of CASE_ID_PATTERNS) {
    const m = content.match(p);
    if (m) return m[0];
  }
  return null;
}

function extractSymptoms(content: string): string[] {
  const symptoms: string[] = [];
  const patterns = [/symptom[s]?[:\s]*([^\n]+)/gi, /issue[:\s]*([^\n]+)/gi, /problem[:\s]*([^\n]+)/gi];
  for (const p of patterns) {
    let m;
    while ((m = p.exec(content)) !== null) {
      const s = m[1].trim();
      if (s.length > 10) symptoms.push(s);
    }
  }
  return symptoms;
}

function extractErrorPatterns(lines: string[]): string[] {
  return [
    ...new Set(
      lines
        .filter((l) => /Error|Exception|Failed/.test(l))
        .slice(0, 5),
    ),
  ];
}

export interface AddOptions {
  caseId?: string;
}

export class ScpEngine {
  private cases: Record<string, Case> = {};
  private vault: Record<string, Record<string, string>> = {};
  private storage: StorageBackend;
  private policy: PolicyConfig;
  private initialized = false;

  constructor(storage: StorageBackend, policy: PolicyConfig) {
    this.storage = storage;
    this.policy = policy;
  }

  async init(): Promise<void> {
    if (this.initialized) return;
    [this.cases, this.vault] = await Promise.all([
      this.storage.loadCases(),
      this.storage.loadVault(),
    ]);
    this.initialized = true;
  }

  async addCase(content: string, options: AddOptions = {}): Promise<string> {
    await this.init();
    const now = new Date().toISOString();

    const lines = content.split('\n').map((l) => l.trim()).filter(Boolean);
    const summary =
      lines.find((l) => l.length > 20 && !l.startsWith('---') && !l.includes('ADDITIONAL INFORMATION')) ??
      'No summary found';

    const detectedId = extractCaseId(content);
    const caseId = options.caseId ?? detectedId ?? `CASE-${Date.now()}`;

    const { redacted, mappings } = redactPii(content);

    const c: Case = {
      caseId,
      summary,
      symptoms: extractSymptoms(content),
      environment: parseEnvironment(content),
      errorPatterns: extractErrorPatterns(lines),
      tags: generateTags(content),
      contentRedacted: redacted,
      wordCount: content.split(/\s+/).length,
      createdAt: now,
      updatedAt: now,
    };

    this.cases[caseId] = c;
    await this.storage.saveCases(this.cases);

    if (Object.keys(mappings).length > 0) {
      this.vault[caseId] = mappings;
      await this.storage.saveVault(this.vault);
    }

    return caseId;
  }

  async search(query: string, options: { limit?: number } = {}): Promise<SearchResult[]> {
    await this.init();
    return searchCases(this.cases, query, options);
  }

  async getCase(caseId: string, options: { context?: boolean; full?: boolean } = {}): Promise<Case | ReturnType<typeof toCaseContext> | (Case & { contentFull?: string }) | null> {
    await this.init();
    const c = this.cases[caseId];
    if (!c) return null;

    if (options.context) return toCaseContext(caseId, c);

    if (options.full && this.vault[caseId]) {
      if (!this.policy.allowFullRehydration) {
        throw new Error('Full rehydration not permitted under current policy profile');
      }
      return { ...c, contentFull: rehydrate(c.contentRedacted, this.vault[caseId]) };
    }

    return { ...c };
  }

  async exportContext(caseIds: string[]): Promise<ContextExport> {
    await this.init();
    return exportContext(this.cases, caseIds);
  }

  async stats(): Promise<Stats> {
    await this.init();
    const allTags = Object.values(this.cases).flatMap((c) => c.tags);
    const tagCounts: Record<string, number> = {};
    for (const t of allTags) tagCounts[t] = (tagCounts[t] ?? 0) + 1;

    const storage = this.storage as { getDataSize?: () => number };
    const dataSize = storage.getDataSize ? storage.getDataSize() : 0;

    return {
      totalCases: Object.keys(this.cases).length,
      casesWithPii: Object.keys(this.vault).length,
      topTags: Object.entries(tagCounts)
        .sort(([, a], [, b]) => b - a)
        .slice(0, 10)
        .map(([tag, count]) => ({ tag, count })),
      dataSize,
    };
  }
}
