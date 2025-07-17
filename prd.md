# Support Context Protocol (SCP)

## Overview

SCP is a **minimal, local-first** case triage system that helps support engineers quickly find relevant context and solutions from past cases. Think of it as "grep for support cases" with smart context injection for AI tools.

## Core Problem

Support engineers waste time:
- Re-solving problems they've seen before
- Context-switching between tickets, logs, and documentation  
- Manually feeding case context to LLMs/AI tools
- Searching through scattered case histories

> *"When you're responsible for solving the issue but apparently not responsible enough to see the logs without asking permission from a team of coworkers, 2 robots, and someone who left the company."*

**The Access Paradox**: You need the data to fix the problem, but can't access the data because of the problem you're trying to fix.

## Solution

A **single executable** that:
1. **Ingests** case data from common sources (clipboard, files, APIs)
2. **Stores** cases locally with automatic PII redaction and hashing
3. **Searches** past cases by symptoms, errors, or keywords
4. **Rehydrates** full data when needed without losing fidelity or specificity
5. **Injects** relevant context into AI tools via MCP (Model Context Protocol)

**SCP breaks the access paradox**: Hash and strip PII for safe storage, then rehydrate with full specificity when debugging - no permission slips required.

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

## PII Handling & Data Security

### Data Sources and Structures

**ICM (Incident and Case Management)**
- Incident ID (e.g., 633627204)
- Service Name (e.g., Azure Monitor, AMA) 
- Severity (e.g., Sev2, Sev3)
- Status (e.g., Active, Closed)
- Owner/Assignee (often includes alias or full name)
- Discussion Threads (comments, updates, timestamps)
- Linked Support Request (SR) or Case ID
- Linked ADO Work Items (via RATIO or manual linkage)
- Repair Items (e.g., bug IDs, fix status)
- Customer Environment Metadata (e.g., subscription ID, workspace ID, region)

**Azure DevOps (ADO) Work Items**
- Work Item ID (e.g., 32672506)
- Title and Description
- Tags (e.g., Supportability, Bug, Feature)
- Discussion Comments
- Linked Incidents or SRs
- Assigned To (user alias or name)
- State (e.g., New, Active, Resolved)
- Custom Fields (e.g., TTM, TSH, TSM metrics)

### PII Categories and Redaction

**Critical PII to Cleanse**
| PII Category | Examples | Redaction Pattern |
|--------------|----------|------------------|
| Customer Identifiers | Subscription ID, Workspace ID, Tenant ID | `[SUB_ID_1]`, `[WORKSPACE_1]`, `[TENANT_1]` |
| Network Data | IP addresses, domain names | `[IP_1]`, `[DOMAIN_1]` |
| User Information | Email addresses, usernames, aliases | `[EMAIL_1]`, `[USER_1]` |
| System Paths | File paths, directory structures | `[PATH_1]`, `[PATH_2]` |
| Log Content | Customer data in logs, credentials | `[LOG_DATA_1]` |
| Freeform Text | Unstructured text with customer context | Context-aware redaction |

**Regex Patterns for Detection**
- Email addresses: `[\w\.-]+@[\w\.-]+`
- IP addresses: `\b(?:\d{1,3}\.){3}\d{1,3}\b`
- GUIDs/Subscription IDs: `\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b`
- Azure Resource IDs: `/subscriptions/[^/]+/resourceGroups/[^/]+/providers/[^/]+`

### Data Processing Best Practices

**Field-Based Extraction**
- Parse structured fields directly from JSON/XML exports
- Prioritize metadata over freeform content
- Maintain traceability with data source tags

**Discussion Thread Normalization**
- Extract action items and root cause summaries
- Avoid copying full comment threads
- Focus on technical resolution patterns

**Local Vault Security & PII Rehydration**
- AES-256 encryption for PII mappings in local `vault.json`
- Never transmitted or shared externally
- Lightweight JSON structure for easy team sharing when needed

**PII Rehydration Capabilities**
```bash
# Standard context export (always redacted)
scp get ICM-123 --context > context.json

# Local rehydration for authorized debugging (local only)
scp get ICM-123 --full --local-only
# Expands [SUB_ID_1] back to actual subscription ID

# Team vault sharing for debugging sessions
scp export-vault --team-file team_pii_map.json  # Encrypted team file
scp import-vault --from-file team_pii_map.json  # Import team mappings
```

**Vault Structure (Lightweight)**
```json
{
  "tokens": {
    "[SUB_ID_1]": "12345678-1234-1234-1234-123456789abc",
    "[WORKSPACE_1]": "workspace-name-prod", 
    "[EMAIL_1]": "customer@company.com",
    "[IP_1]": "192.168.1.100"
  },
  "metadata": {
    "created": "2025-07-17T12:00:00Z",
    "case_count": 42
  }
}
```

### Compliance Considerations

**Internal Alias Handling**
- Even internal Microsoft aliases may be sensitive
- Context-dependent redaction based on audience
- Option to preserve internal identifiers for authorized use

**Data Retention**
- Local-only storage approach
- User-controlled data lifecycle
- Export capabilities for team knowledge sharing (with PII stripped)

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