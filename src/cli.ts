#!/usr/bin/env node
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { homedir } from 'node:os';
import { spawn } from 'node:child_process';
import { Command } from 'commander';
import { ScpEngine } from './core/engine.js';
import { getPolicy } from './policy/profiles.js';
import { FilesystemStorage } from './storage/filesystem.js';
import { MemoryStorage } from './storage/memory.js';
import { startMcpServer } from './mcp/server.js';

function createEngine(opts: { memory?: boolean; profile?: string }): ScpEngine {
  const policy = getPolicy(opts.profile ?? 'trusted');
  const storage = opts.memory
    ? new MemoryStorage()
    : new FilesystemStorage(join(homedir(), '.scp'));
  return new ScpEngine(storage, policy);
}

async function readClipboard(): Promise<string> {
  return new Promise((resolve, reject) => {
    let cmd: string;
    let args: string[];
    switch (process.platform) {
      case 'darwin':
        cmd = 'pbpaste'; args = []; break;
      case 'win32':
        cmd = 'powershell.exe'; args = ['-Command', 'Get-Clipboard | Out-String']; break;
      case 'linux':
        cmd = 'xclip'; args = ['-o']; break;
      default:
        reject(new Error(`Unsupported platform: ${process.platform}`)); return;
    }
    const proc = spawn(cmd, args);
    let out = '';
    proc.stdout.on('data', (d: Buffer) => { out += d.toString(); });
    proc.on('close', (code) => {
      if (code === 0) resolve(out.trim());
      else reject(new Error(`Clipboard command failed with code ${code ?? 'unknown'}`));
    });
    proc.on('error', reject);
  });
}

async function readStdin(): Promise<string> {
  return new Promise((resolve) => {
    let data = '';
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', (chunk: string) => { data += chunk; });
    process.stdin.on('end', () => resolve(data));
  });
}

const program = new Command();

program
  .name('scp')
  .description('Support Context Protocol – policy-adaptive case ingestion, search, and AI-ready context export')
  .version('1.0.0')
  .option('--memory', 'Run in memory-only mode (no disk persistence)')
  .option('--profile <profile>', 'Policy profile: strict | trusted', 'trusted');

program
  .command('add')
  .description('Add a new support case')
  .option('--case-id <id>', 'Specify case ID')
  .option('--file <path>', 'Read case content from file')
  .option('--paste', 'Read case content from clipboard')
  .action(async (options: { caseId?: string; file?: string; paste?: boolean }) => {
    const globalOpts = program.opts<{ memory?: boolean; profile?: string }>();
    const engine = createEngine(globalOpts);

    let content: string;
    if (options.file) {
      content = readFileSync(options.file, 'utf8');
    } else if (options.paste) {
      try {
        content = await readClipboard();
        console.error(`Clipboard content retrieved (${process.platform})`);
      } catch (e) {
        console.error(`Clipboard not available: ${(e as Error).message}`);
        console.error('Please use --file or pipe content via stdin.');
        process.exit(1);
      }
    } else {
      content = await readStdin();
    }

    if (!content.trim()) {
      console.error('No content provided');
      process.exit(1);
    }

    const caseId = await engine.addCase(content, { caseId: options.caseId });
    const c = await engine.getCase(caseId) as import('./core/types.js').Case;
    console.log(`Case ${caseId} added successfully`);
    console.log(`Found ${c.symptoms.length} symptoms, ${c.errorPatterns.length} error patterns`);
    console.log(`Tags: ${c.tags.join(', ') || '(none)'}`);
    console.log(`Case ID: ${caseId}`);
  });

program
  .command('search <query>')
  .description('Search cases')
  .option('-l, --limit <num>', 'Max results', '5')
  .option('-c, --context', 'Output AI-ready context JSON')
  .action(async (query: string, options: { limit?: string; context?: boolean }) => {
    const globalOpts = program.opts<{ memory?: boolean; profile?: string }>();
    const engine = createEngine(globalOpts);

    const results = await engine.search(query, { limit: parseInt(options.limit ?? '5', 10) });

    if (results.length === 0) {
      console.log('No matching cases found');
      return;
    }

    if (options.context) {
      const ctx = await engine.exportContext(results.map((r) => r.caseId));
      console.log(JSON.stringify(ctx, null, 2));
    } else {
      console.log(`Found ${results.length} matching cases:\n`);
      for (const r of results) {
        console.log(`${r.caseId} (score: ${r.score})`);
        console.log(`   ${r.summary}`);
        console.log(`   Tags: ${r.tags.join(', ')}`);
        console.log(`   Matches: ${r.matches.join(', ')}`);
        console.log('');
      }
    }
  });

program
  .command('get <case-id>')
  .description('Get case details')
  .option('-c, --context', 'Format for AI/MCP context injection')
  .option('-f, --full', 'Include rehydrated PII (trusted profile only)')
  .action(async (caseId: string, options: { context?: boolean; full?: boolean }) => {
    const globalOpts = program.opts<{ memory?: boolean; profile?: string }>();
    const engine = createEngine(globalOpts);

    try {
      const result = await engine.getCase(caseId, options);
      if (!result) {
        console.error('Case not found');
        process.exit(1);
      }
      console.log(JSON.stringify(result, null, 2));
    } catch (e) {
      console.error((e as Error).message);
      process.exit(1);
    }
  });

program
  .command('stats')
  .description('Show database statistics')
  .action(async () => {
    const globalOpts = program.opts<{ memory?: boolean; profile?: string }>();
    const engine = createEngine(globalOpts);

    const stats = await engine.stats();
    console.log('\nSCP DATABASE STATUS');
    console.log('===================');
    console.log(`CASES:    ${stats.totalCases}`);
    console.log(`SECURED:  ${stats.casesWithPii}`);
    console.log(`SIZE:     ${(stats.dataSize / 1024).toFixed(2)} KB\n`);
    console.log('TOP TAGS:');
    for (const { tag, count } of stats.topTags) {
      console.log(`   [${count}] ${tag}`);
    }
  });

program
  .command('mcp')
  .description('Start the MCP server (stdin/stdout JSON-RPC)')
  .action(async () => {
    const globalOpts = program.opts<{ memory?: boolean; profile?: string }>();
    const engine = createEngine(globalOpts);
    await startMcpServer(engine);
  });

program.parse();
