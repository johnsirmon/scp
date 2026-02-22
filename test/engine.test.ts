import { describe, it, expect, beforeEach } from 'vitest';
import { ScpEngine } from '../src/core/engine.js';
import { MemoryStorage } from '../src/storage/memory.js';
import { TRUSTED_POLICY, STRICT_POLICY } from '../src/policy/profiles.js';

describe('ScpEngine', () => {
  let engine: ScpEngine;

  beforeEach(() => {
    engine = new ScpEngine(new MemoryStorage(), TRUSTED_POLICY);
  });

  it('adds a case and returns an ID', async () => {
    const id = await engine.addCase('ICM-123: Database timeout in production cluster');
    expect(id).toBeTruthy();
  });

  it('detects case ID from content', async () => {
    const id = await engine.addCase('ICM-99999: VM connectivity issue');
    expect(id).toContain('ICM-99999');
  });

  it('uses provided case ID over detected one', async () => {
    const id = await engine.addCase('ICM-111: some issue', { caseId: 'MY-CASE-1' });
    expect(id).toBe('MY-CASE-1');
  });

  it('redacts PII in stored content', async () => {
    const id = await engine.addCase('Error from user@example.com on 10.0.0.1');
    const c = await engine.getCase(id) as { contentRedacted: string };
    expect(c).not.toBeNull();
    expect(c.contentRedacted).not.toContain('user@example.com');
    expect(c.contentRedacted).not.toContain('10.0.0.1');
  });

  it('searches and returns ranked results', async () => {
    await engine.addCase('ICM-1: AMA timeout on Windows server');
    await engine.addCase('ICM-2: Linux connection failure');
    const results = await engine.search('timeout');
    expect(results.length).toBeGreaterThan(0);
    expect(results[0].summary).toMatch(/AMA timeout/i);
  });

  it('returns null for unknown case', async () => {
    const result = await engine.getCase('NOT-EXISTS');
    expect(result).toBeNull();
  });

  it('exports AI-ready context', async () => {
    const id = await engine.addCase('ICM-200: Storage latency issue in East US');
    const ctx = await engine.exportContext([id]);
    expect(ctx.contextType).toBe('support_cases');
    expect(ctx.totalCases).toBe(1);
    expect(ctx.cases[0].caseId).toBe(id);
  });

  it('strict policy blocks full rehydration', async () => {
    const strictEngine = new ScpEngine(new MemoryStorage(), STRICT_POLICY);
    const id = await strictEngine.addCase('Error from admin@corp.com');
    await expect(strictEngine.getCase(id, { full: true })).rejects.toThrow(/not permitted/);
  });

  it('returns stats correctly', async () => {
    await engine.addCase('ICM-301: Windows timeout');
    const stats = await engine.stats();
    expect(stats.totalCases).toBe(1);
  });
});
