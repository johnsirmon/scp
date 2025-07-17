#!/usr/bin/env node
/**
 * Support Context Protocol (SCP)
 * Minimal, intelligent case triage for Microsoft support engineers
 * Optimized for MCP/LLM integration with PII safety
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { Command } = require('commander');
const figlet = require('figlet');

class SCP {
  constructor() {
    this.dataPath = path.join(process.env.HOME || process.env.USERPROFILE, '.scp');
    this.casesFile = path.join(this.dataPath, 'cases.json');
    this.vaultFile = path.join(this.dataPath, 'vault.json');
    
    this.ensureDataDir();
    this.vaultKey = this.getOrCreateKey();
    this.cases = this.loadCases();
    this.vault = this.loadVault();
  }

  ensureDataDir() {
    if (!fs.existsSync(this.dataPath)) {
      fs.mkdirSync(this.dataPath, { recursive: true });
    }
  }

  getOrCreateKey() {
    this.ensureDataDir(); // Ensure directory exists first
    const keyFile = path.join(this.dataPath, '.key');
    if (fs.existsSync(keyFile)) {
      return fs.readFileSync(keyFile, 'utf8');
    }
    const key = crypto.randomBytes(32).toString('hex');
    fs.writeFileSync(keyFile, key, { mode: 0o600 });
    return key;
  }

  // PII Redaction patterns optimized for Microsoft ICMs
  getPIIPatterns() {
    return [
      // Azure Resource IDs
      { pattern: /\/subscriptions\/[a-f0-9-]{36}/gi, replacement: '[SUB_ID_#]' },
      { pattern: /\/resourceGroups\/[\w-]+/gi, replacement: '[RG_#]' },
      { pattern: /\/providers\/Microsoft\.[\w\/]+/gi, replacement: '[RESOURCE_#]' },
      
      // Common Microsoft patterns
      { pattern: /[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}/gi, replacement: '[GUID_#]' },
      { pattern: /\b[\w-]+@microsoft\.com\b/gi, replacement: '[MS_EMAIL_#]' },
      { pattern: /\b[\w-]+@[\w-]+\.com\b/gi, replacement: '[EMAIL_#]' },
      
      // IP addresses and hostnames
      { pattern: /\b(?:\d{1,3}\.){3}\d{1,3}\b/g, replacement: '[IP_#]' },
      { pattern: /\bvm-[\w-]+/gi, replacement: '[VM_#]' },
      
      // Phone numbers and other sensitive data
      { pattern: /\b\d{3}-\d{3}-\d{4}\b/g, replacement: '[PHONE_#]' },
      { pattern: /\b[A-Z]{2,}\d{6,}\b/g, replacement: '[ID_#]' }
    ];
  }

  redactPII(text) {
    let redacted = text;
    const mappings = {};
    const counters = {};

    this.getPIIPatterns().forEach(({ pattern, replacement }) => {
      redacted = redacted.replace(pattern, (match) => {
        const baseReplacement = replacement.replace('#', '');
        counters[baseReplacement] = (counters[baseReplacement] || 0) + 1;
        const token = replacement.replace('#', counters[baseReplacement]);
        mappings[token] = match;
        return token;
      });
    });

    return { redacted, mappings };
  }

  encryptVault(data) {
    const cipher = crypto.createCipher('aes-256-cbc', this.vaultKey);
    let encrypted = cipher.update(JSON.stringify(data), 'utf8', 'hex');
    encrypted += cipher.final('hex');
    return encrypted;
  }

  decryptVault(encrypted) {
    try {
      const decipher = crypto.createDecipher('aes-256-cbc', this.vaultKey);
      let decrypted = decipher.update(encrypted, 'hex', 'utf8');
      decrypted += decipher.final('utf8');
      return JSON.parse(decrypted);
    } catch (e) {
      return {};
    }
  }

  // Parse ICM content based on real Microsoft patterns
  parseICM(content) {
    const icm = {
      case_id: null,
      summary: null,
      symptoms: [],
      environment: {},
      error_patterns: [],
      discussion: [],
      metadata: {}
    };

    // Extract case IDs (multiple formats)
    const idPatterns = [
      /ICM[:-](\d+)/i,
      /Incident[:-](\d+)/i,
      /Support Request Number:\s*(\d+)/i,
      /Support[:-](\d+)/i
    ];

    for (const pattern of idPatterns) {
      const match = content.match(pattern);
      if (match) {
        icm.case_id = match[0];
        break;
      }
    }

    // Extract summary (first meaningful line)
    const lines = content.split('\n').map(l => l.trim()).filter(l => l);
    icm.summary = lines.find(line => 
      line.length > 20 && 
      !line.startsWith('---') && 
      !line.includes('ADDITIONAL INFORMATION')
    ) || 'No summary found';

    // Extract environment data
    const envPatterns = {
      subscription_id: /Subscription ID[:\s]*([a-f0-9-]{36})/i,
      workspace_id: /Workspace ID[:\s]*([a-f0-9-]{36})/i,
      agent_version: /Agent version[:\s]*([0-9.]+)/i,
      os_version: /Major OS Version[:\s]*([^:]+)/i
    };

    Object.entries(envPatterns).forEach(([key, pattern]) => {
      const match = content.match(pattern);
      if (match) icm.environment[key] = match[1].trim();
    });

    // Extract error patterns
    const errorLines = lines.filter(line => 
      line.includes('Error') || 
      line.includes('Exception') || 
      line.includes('Failed')
    );
    icm.error_patterns = [...new Set(errorLines.slice(0, 5))]; // Dedupe and limit

    // Extract discussion entries
    const discussionPattern = /^([A-Za-z\s]+)\n.*?Submitted at ([\d-:\s]+)/gm;
    let match;
    while ((match = discussionPattern.exec(content)) !== null) {
      icm.discussion.push({
        author: match[1].trim(),
        timestamp: match[2].trim()
      });
    }

    // Extract symptoms (common problem indicators)
    const symptomPatterns = [
      /symptom[s]?[:\s]*([^\\n]+)/gi,
      /issue[:\s]*([^\\n]+)/gi,
      /problem[:\s]*([^\\n]+)/gi
    ];

    symptomPatterns.forEach(pattern => {
      let symptomMatch;
      while ((symptomMatch = pattern.exec(content)) !== null) {
        const symptom = symptomMatch[1].trim();
        if (symptom.length > 10) {
          icm.symptoms.push(symptom);
        }
      }
    });

    // Auto-generate tags
    icm.metadata.tags = this.generateTags(content);
    icm.metadata.created = new Date().toISOString();
    icm.metadata.word_count = content.split(/\s+/).length;

    return icm;
  }

  generateTags(content) {
    const tagPatterns = {
      'AMA': /\bAMA\b/i,
      'Windows': /\bWindows\b/i,
      'Linux': /\bLinux\b|\bRedHat\b/i,
      'MetricsExtension': /\bMetricsExtension\b/i,
      'InfluxDB': /\bInfluxDb\b/i,
      'Telegraf': /\bTelegraf\b/i,
      'Timeout': /\btimeout\b/i,
      'Connection': /\bconnection\b/i,
      'Version': /version\s*\d+\.\d+/i
    };

    return Object.entries(tagPatterns)
      .filter(([, pattern]) => pattern.test(content))
      .map(([tag]) => tag);
  }

  // Compress repetitive log entries (major space saver for ICMs)
  compressLogs(content) {
    const lines = content.split('\n');
    const compressed = [];
    const seen = new Map();

    lines.forEach(line => {
      const normalized = line.replace(/\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}/, '[TIMESTAMP]')
                           .replace(/TID:\d+/, '[TID]');
      
      if (seen.has(normalized)) {
        seen.set(normalized, seen.get(normalized) + 1);
      } else {
        seen.set(normalized, 1);
        compressed.push(line);
      }
    });

    // Add compression summary for repeated lines
    const repeated = Array.from(seen.entries())
      .filter(([, count]) => count > 1)
      .map(([line, count]) => `[REPEATED ${count}x] ${line.substring(0, 100)}...`);

    if (repeated.length > 0) {
      compressed.push('\\n--- COMPRESSED LOG PATTERNS ---');
      compressed.push(...repeated);
    }

    return compressed.join('\\n');
  }

  addCase(content, options = {}) {
    console.log(`
        .-.
       (o.o)     PROCESSING CASE...
        \\-/      ==================
         |       
      .--'--.    [ SECURE TRIAGE PROTOCOL ]
     /       \\    
    /_________\\  
    `);
    
    // Compress repetitive content first
    const compressed = this.compressLogs(content);
    
    // Parse ICM structure
    const icm = this.parseICM(compressed);
    
    // Generate case ID if not found
    if (!icm.case_id) {
      icm.case_id = options.caseId || `CASE-${Date.now()}`;
    }

    // Redact PII
    const { redacted, mappings } = this.redactPII(compressed);
    icm.content_redacted = redacted;

    // Store PII mappings in encrypted vault
    if (Object.keys(mappings).length > 0) {
      this.vault[icm.case_id] = mappings;
      this.saveVault();
    }

    // Save case
    this.cases[icm.case_id] = icm;
    this.saveCases();

    console.log(`✅ Case ${icm.case_id} added successfully`);
    console.log(`📊 Found ${icm.symptoms.length} symptoms, ${icm.error_patterns.length} error patterns`);
    console.log(`🏷️  Tags: ${icm.metadata.tags.join(', ')}`);
    console.log(`🔒 PII tokens: ${Object.keys(mappings).length}`);
    
    return icm.case_id;
  }

  search(query, options = {}) {
    const results = [];
    const queryLower = query.toLowerCase();

    Object.entries(this.cases).forEach(([caseId, icm]) => {
      let score = 0;
      const matches = [];

      // Search in summary
      if (icm.summary && icm.summary.toLowerCase().includes(queryLower)) {
        score += 10;
        matches.push('summary');
      }

      // Search in symptoms
      icm.symptoms.forEach(symptom => {
        if (symptom.toLowerCase().includes(queryLower)) {
          score += 8;
          matches.push('symptoms');
        }
      });

      // Search in error patterns
      icm.error_patterns.forEach(error => {
        if (error.toLowerCase().includes(queryLower)) {
          score += 9;
          matches.push('errors');
        }
      });

      // Search in tags
      icm.metadata.tags.forEach(tag => {
        if (tag.toLowerCase().includes(queryLower)) {
          score += 5;
          matches.push('tags');
        }
      });

      // Search in redacted content
      if (icm.content_redacted && icm.content_redacted.toLowerCase().includes(queryLower)) {
        score += 3;
        matches.push('content');
      }

      if (score > 0) {
        results.push({
          case_id: caseId,
          score,
          matches: [...new Set(matches)],
          summary: icm.summary,
          tags: icm.metadata.tags,
          created: icm.metadata.created
        });
      }
    });

    return results
      .sort((a, b) => b.score - a.score)
      .slice(0, options.limit || 10);
  }

  getCase(caseId, options = {}) {
    const icm = this.cases[caseId];
    if (!icm) return null;

    const result = { ...icm };

    if (options.context) {
      // Format for MCP/LLM context injection
      return {
        case_id: caseId,
        summary: icm.summary,
        symptoms: icm.symptoms.slice(0, 3), // Limit for context
        environment: icm.environment,
        key_errors: icm.error_patterns.slice(0, 3),
        tags: icm.metadata.tags,
        content_preview: icm.content_redacted.substring(0, 500) + '...'
      };
    }

    if (options.full && this.vault[caseId]) {
      // Rehydrate PII for full view
      const mappings = this.vault[caseId];
      let rehydrated = icm.content_redacted;
      
      Object.entries(mappings).forEach(([token, original]) => {
        rehydrated = rehydrated.replace(new RegExp(token, 'g'), original);
      });
      
      result.content_full = rehydrated;
    }

    return result;
  }

  exportContext(caseIds) {
    const context = caseIds.map(id => this.getCase(id, { context: true }))
                           .filter(Boolean);
    
    return {
      context_type: 'support_cases',
      total_cases: context.length,
      generated: new Date().toISOString(),
      cases: context
    };
  }

  loadCases() {
    try {
      if (fs.existsSync(this.casesFile)) {
        return JSON.parse(fs.readFileSync(this.casesFile, 'utf8'));
      }
    } catch (e) {
      console.warn('Warning: Could not load cases file');
    }
    return {};
  }

  saveCases() {
    fs.writeFileSync(this.casesFile, JSON.stringify(this.cases, null, 2));
  }

  loadVault() {
    try {
      if (fs.existsSync(this.vaultFile)) {
        const encrypted = fs.readFileSync(this.vaultFile, 'utf8');
        return this.decryptVault(encrypted);
      }
    } catch (e) {
      console.warn('Warning: Could not load vault file');
    }
    return {};
  }

  saveVault() {
    const encrypted = this.encryptVault(this.vault);
    fs.writeFileSync(this.vaultFile, encrypted, { mode: 0o600 });
  }

  stats() {
    const totalCases = Object.keys(this.cases).length;
    const totalPII = Object.keys(this.vault).length;
    const allTags = Object.values(this.cases)
      .flatMap(icm => icm.metadata.tags || []);
    const tagCounts = {};
    allTags.forEach(tag => tagCounts[tag] = (tagCounts[tag] || 0) + 1);

    // Generate ASCII art header
    const scpHeader = figlet.textSync('SCP', {
      font: 'ANSI Shadow',
      horizontalLayout: 'default',
      verticalLayout: 'default'
    });

    const statsDisplay = `
🔥 ${scpHeader}
💀 DATABASE STATUS 💀
=====================
🗂️  CASES: ${totalCases}
🔒 SECURED: ${totalPII}
⚡ [ SCP VAULT ACTIVE ] ⚡
    `;

    return {
      total_cases: totalCases,
      cases_with_pii: totalPII,
      stats_display: statsDisplay,
      top_tags: Object.entries(tagCounts)
        .sort(([,a], [,b]) => b - a)
        .slice(0, 10)
        .map(([tag, count]) => ({ tag, count })),
      data_size: fs.existsSync(this.casesFile) ? 
        fs.statSync(this.casesFile).size : 0
    };
  }
}

// CLI Interface
const program = new Command();
const scp = new SCP();

// Generate ASCII art header
const welcomeHeader = figlet.textSync('SCP', {
  font: 'ANSI Shadow',
  horizontalLayout: 'default',
  verticalLayout: 'default'
});

const styledHeader = `\n🔥 ${welcomeHeader}\n💀 SUPPORT CONTEXT PROTOCOL 💀\n`;

program
  .name('scp')
  .description(`${styledHeader}⚡ Intelligent case triage for Microsoft support engineers ⚡`)
  .version('1.0.0');

program
  .command('add')
  .description('Add a new case')
  .option('--case-id <id>', 'Specify case ID')
  .option('--file <path>', 'Read from file')
  .option('--paste', 'Read from clipboard (requires pbpaste/xclip)')
  .action(async (options) => {
    let content = '';
    
    if (options.file) {
      content = fs.readFileSync(options.file, 'utf8');
    } else if (options.paste) {
      // Try to read from clipboard
      try {
        const { spawn } = require('child_process');
        const cmd = process.platform === 'darwin' ? 'pbpaste' : 'xclip -o';
        const proc = spawn('sh', ['-c', cmd]);
        
        proc.stdout.on('data', (data) => {
          content += data.toString();
        });
        
        await new Promise((resolve) => {
          proc.on('close', resolve);
        });
      } catch (e) {
        console.error('Clipboard not available. Please use --file or pipe content.');
        process.exit(1);
      }
    } else {
      // Read from stdin
      content = await new Promise((resolve) => {
        let data = '';
        process.stdin.on('data', chunk => data += chunk);
        process.stdin.on('end', () => resolve(data));
      });
    }

    if (!content.trim()) {
      console.error('No content provided');
      process.exit(1);
    }

    const caseId = scp.addCase(content, { caseId: options.caseId });
    console.log(`Case ID: ${caseId}`);
  });

program
  .command('search <query>')
  .description('Search cases')
  .option('-l, --limit <num>', 'Limit results', 5)
  .option('-c, --context', 'Format for MCP/LLM context')
  .action((query, options) => {
    const results = scp.search(query, { limit: parseInt(options.limit) });
    
    if (results.length === 0) {
      console.log('No matching cases found');
      return;
    }

    if (options.context) {
      const caseIds = results.map(r => r.case_id);
      const context = scp.exportContext(caseIds);
      console.log(JSON.stringify(context, null, 2));
    } else {
      console.log(`Found ${results.length} matching cases:\\n`);
      results.forEach(result => {
        console.log(`📋 ${result.case_id} (score: ${result.score})`);
        console.log(`   ${result.summary}`);
        console.log(`   🏷️  ${result.tags.join(', ')}`);
        console.log(`   📍 Matches: ${result.matches.join(', ')}`);
        console.log('');
      });
    }
  });

program
  .command('get <case-id>')
  .description('Get case details')
  .option('-c, --context', 'Format for MCP/LLM context')
  .option('-f, --full', 'Include rehydrated PII (local only)')
  .action((caseId, options) => {
    const icm = scp.getCase(caseId, options);
    
    if (!icm) {
      console.log('Case not found');
      process.exit(1);
    }

    console.log(JSON.stringify(icm, null, 2));
  });

program
  .command('stats')
  .description('Show database statistics')
  .action(() => {
    const stats = scp.stats();
    console.log(stats.stats_display);
    console.log(`Database size: ${(stats.data_size / 1024).toFixed(2)} KB\n`);
    
    console.log('TOP TAGS:');
    stats.top_tags.forEach(({ tag, count }) => {
      console.log(`   [X] ${tag}: ${count}`);
    });
  });

// Handle stdin for piped input
if (!process.stdin.isTTY) {
  program.parse(['node', 'scp', 'add']);
} else {
  program.parse();
}
