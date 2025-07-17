# Support Context Protocol (SCP)

## Overview

SCP is a **minimal, local-first** case triage system that helps support engineers quickly find relevant context and solutions from past cases. Think of it as "grep for support cases" with smart context injection for AI tools.

## Core Problem

Support engineers waste time:
- Re-solving problems they've seen before
- Context-switching between tickets, logs, and documentation  
- Manually feeding case context to LLMs/AI tools
- Searching through scattered case histories

## Solution

A **single executable** that:
1. **Ingests** case data from common sources (clipboard, files, APIs)
2. **Stores** cases locally with automatic PII redaction
3. **Searches** past cases by symptoms, errors, or keywords
4. **Injects** relevant context into AI tools via MCP (Model Context Protocol)

## Key Features

**Minimal & Local-First**
- Single binary/script - no complex setup
- Works offline - all data stored locally
- PII-safe by default - automatic redaction with local vault
- Cross-platform - runs anywhere

**Smart Context**
- Pattern-based case matching
- Auto-extract: case IDs, symptoms, error codes, solutions
- Export context in AI-friendly formats
- VSCode MCP integration for seamless LLM context injection

**Practical Workflows**
- Paste logs → auto-extract case data
- Search symptoms → find similar past cases  
- Query cases → get redacted context for AI tools
- Solve case → store solution for future reference

## Architecture (Minimal)

**Technology Choice: Go or TypeScript/Node.js**
- Go: Single binary, fast, great CLI tools, cross-platform
- TypeScript: Better VSCode integration, familiar to web devs, rich ecosystem

**Core Components (3 files maximum)**
```
scp.go/scp.ts          # Main executable with all logic
cases.json             # Local case database (simple JSON)
vault.json             # Encrypted PII mappings (AES-256)
```

**Data Flow**
```
Input → Parse → Redact PII → Store → Search/Query → Context Export
```

## Essential Commands

```bash
# Install (single command)
curl -sSL get.scp.dev | sh   # or npm install -g scp

# Basic usage
scp add "ICM-123: Database timeout in prod"
scp search "timeout"
scp get ICM-123 --context     # For AI tools
scp get ICM-123 --full        # With PII restored
```

## VSCode Integration

**Model Context Protocol (MCP) Server**
- Auto-inject relevant case context when coding/debugging
- Right-click → "Find similar cases" 
- Seamlessly provide context to GitHub Copilot/Claude

## PII Handling (Simplified)

**Auto-Redaction Patterns**
- Email addresses → `[EMAIL_1]`, `[EMAIL_2]`
- IP addresses → `[IP_1]`, `[IP_2]`  
- Phone numbers → `[PHONE_1]`
- Custom patterns via config

**Local Vault**
- Encrypted JSON file with token mappings
- Never leaves local machine
- Restore context after AI processing

## Data Structure (Learned from Real ICMs)

**Standard ICM Fields**
```json
{
  "case_id": "ICM-588573816 | Support-2506230030001929",
  "summary": "AMA reporting operating system as Windows 10 Pro instead of Windows 11 PRO",
  "symptoms": [
    "AMA reporting operating system as Windows 10 Pro instead of Windows 11 PRO",
    "Issue persists across AMA version 1.35+",
    "PowerShell shows correct OS: Microsoft Windows 11 Pro"
  ],
  "environment": {
    "subscription_id": "[REDACTED]",
    "workspace_id": "[REDACTED]", 
    "agent_version": "1.35",
    "os_version": "Windows 11 Pro | RedHat 8.10",
    "vm_resource_id": "[REDACTED]"
  },
  "error_patterns": [
    "InfluxDbProcessor ProcessPayload",
    "Metrics were received and no default monitoring account was specified",
    "Error writing to outputs.socket_writer"
  ],
  "resolution": "Downgrade to version 1.34, fix expected in 1.37 (August)",
  "tags": ["AMA", "Windows", "OS Detection", "MetricsExtension", "InfluxDB"]
}
```

**Auto-Extraction Patterns**
- ICM IDs: `ICM-\d+`, `Support-\d+`, `Incident-\d+`
- Azure Resource IDs: `/subscriptions/.../resourceGroups/.../providers/...`
- Error codes: `TID:\d+`, specific error patterns
- Versions: `\d+\.\d+(\.\d+)?`
- Timestamps: `2025-06-20T01:56:40.499`

**PII Patterns Found**
- Subscription IDs → `[SUB_ID_1]`
- Workspace IDs → `[WORKSPACE_1]` 
- VM names → `[VM_NAME_1]`
- File paths → `[PATH_1]`
- User aliases → `[USER_1]`

## Adoption Strategy

**Distribution**
- Single binary download (no dependencies)
- Package managers: `brew install scp`, `npm install -g scp`, `apt install scp`
- VSCode Extension Marketplace
- Docker image for CI/CD integration

**Community & Ecosystem**
- Open source (MIT license)
- Plugin architecture for custom PII patterns
- Export/import for team sharing
- Integration docs for common support tools (ServiceNow, Jira, etc.)

**Success Metrics**
- Time to first successful case search < 2 minutes
- Support engineer adoption rate 
- Context injection accuracy in AI tools
- PII false positive rate < 5%

## Example Use Cases (Based on Real ICMs)

**Scenario 1: AMA Windows OS Detection Issue**
```bash
# Engineer pastes ICM content
scp add --paste "ICM-588573816: AMA reporting OS as Windows 10 Pro instead of Windows 11 PRO..."

# Later, similar issue occurs
scp search "AMA Windows OS version detection"
# Returns: ICM-588573816 with solution pattern

# Export context for AI
scp get ICM-588573816 --context | pbcopy
# Paste into GitHub Copilot: "Help me debug this AMA issue: [CONTEXT]"
```

**Scenario 2: MetricsExtension InfluxDB Errors** 
```bash
scp add --case-id "Support-2506230030001929" --from-file error.log
scp search "InfluxDbProcessor no default monitoring account"
# Finds: Version 1.35+ regression, downgrade to 1.34, fix in 1.37 (August)
```

## Implementation Roadmap

**MVP (Week 1-2)**
- Single TypeScript/Node.js script
- Basic add/search/get commands
- Simple JSON storage
- Regex-based PII redaction

**v1.0 (Week 3-4)**  
- Compiled binary (pkg/nexe)
- Encrypted PII vault
- VSCode MCP server
- Import/export features

**v1.1 (Month 2)**
- Advanced PII detection
- Case similarity scoring
- Web dashboard
- Team sync capabilities

---

*"Support Context Protocol - Making tribal knowledge searchable, shareable, and AI-ready"*