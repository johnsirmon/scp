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

> *"I'm cleared to close the incident—but seeing the logs first? Hold on, let's get approval from half the org chart."*

> *"Nothing boosts productivity like waiting two hours for approval to read data I wrote myself yesterday."*

**The Access Paradox**: You need the data to fix the problem, but can't access the data because of the problem you're trying to fix. Meanwhile, the customer is waiting, escalation calls are scheduled, and your manager wants updates on progress you can't make without the data you can't see.

> *"Sure, I'll fix this Sev1 outage right after I fill out form B-47 to request permission to see error messages."*

> *"Day 3 of the incident: Still waiting for data access. Customer asks for updates. I send them a haiku about bureaucracy."*

> *"The approval system is down, so now I need approval to request approval to see why the approval system is down."*

**The Real Cost**: Every minute spent waiting for data access is a minute not spent solving the actual problem. Customers don't care about your compliance theater—they want their services working.

## Solution

**Policy-Adaptive Support Context Protocol**: A **tiny core executable** with modular security that adapts from "air-gapped, sign in triplicate" to "paste logs in Slack" without code forks.

**Core Strategy: Thin Core, Policy-Adaptive Perimeter**

Ship a 50KB dependency-lean core that does 3 things well: **ingest → tokenize/redact → search**. Everything else (vault encryption, enterprise auth, DLP APIs, vector DB, MCP plugins) is modular and lazy-loaded.

A **single executable** that:
1. **Ingests** case data from common sources (clipboard, files, APIs)
2. **Stores** cases locally with automatic PII redaction and hashing
3. **Searches** past cases by symptoms, errors, or keywords
4. **Rehydrates** full data when needed without losing fidelity or specificity
5. **Injects** relevant context into AI tools via MCP (Model Context Protocol)
6. **Adapts** to your organization's security posture via policy profiles

**SCP breaks the access paradox**: Hash and strip PII for safe storage, then rehydrate with full specificity when debugging - no permission slips required.

**End the Compliance Theater**: Be compliant AND productive. Store everything safely, access everything instantly. Your customers get faster fixes, your compliance team gets better sleep, and you get to actually do your job.

**Bring Your Own Paranoia**: Locked-down bank? Run in strict mode—HSM keys, outbound scrub walls, audit bus. Startup lab? Use trusted mode—local AES vault, fast paste-to-search. Same schema. Same CLI. Your paranoia level, your call.

## Key Features

**Minimal & Local-First**
- Single binary/script - no complex setup
- Works offline - all data stored locally
- PII-safe by default - automatic redaction with local vault
- Cross-platform - runs anywhere
- **Policy-adaptive**: Same tool works across security cultures

**Smart Context**
- Pattern-based case matching
- Auto-extract: case IDs, symptoms, error codes, solutions
- Export context in AI-friendly formats
- VSCode MCP integration for seamless LLM context injection
- **Redaction Boundary Contract (RBC)**: Configurable policy enforcement

**Practical Workflows**
- Paste logs → auto-extract case data
- Search symptoms → find similar past cases  
- Query cases → get redacted context for AI tools
- Solve case → store solution for future reference
- **Profile-aware**: Automatic policy detection and configuration

## Security Profiles (Built-in Presets)

| Profile | For | Data Handling | Vault | Network | Default Output | Notes |
|---------|-----|---------------|-------|---------|----------------|-------|
| **strict** | Regulated / finserv / gov | Mandatory redaction; deny outbound raw | AES-256 + HSM/KMS option | Default offline; explicit allowlist | Redacted only | Blocks unknown fields; audit-heavy |
| **enterprise** | Large tech / internal prod | Redact w/ override + JIT rehydrate | Encrypted local vault, org escrow optional | Controlled egress | Redacted unless --full local | Tracks approvals; pluggable IAM |
| **trusted** | Startup / internal lab | Redact recommended, toggleable | Local encrypted (password) | Normal | Mixed | Faster; minimal ceremony |
| **dev** | Personal sandbox | Redaction optional / disabled | Plain or encrypted | Unrestricted | Full | Use for demo/testing only |

**Usage Examples:**
```bash
# Enterprise default: redacted export, encrypted vault
scp --profile=enterprise add --paste

# Quick lab demo: no encryption, minimal regex PII
scp --profile=dev add sample.log

# Regulated mode with enforced outbound scrub + audit bundle
scp --profile=strict get ICM-123 --context --evidence audit.json
```

## Architecture (Minimal + Modular)

**Technology Choice: Go or TypeScript/Node.js**
- Go: Single binary, fast, great CLI tools, cross-platform
- TypeScript: Better VSCode integration, familiar to web devs, rich ecosystem

**Core Components (Minimal Interface Surface)**
```
scp.go/scp.ts          # Main executable with core logic (50KB)
cases.json             # Local case database (simple JSON)
vault.json             # Encrypted PII mappings (AES-256)
```

**Capability Modules (Lazy-Loaded)**
```
ingest/*    # connectors (clipboard, file, API, ServiceNow, Jira, custom)
pii/*       # engines (regex, ml-ner, cloud-dlp, custom pattern packs)
vault/*     # (json+aes, sqlite+kms, s3+kms, hsm-backed)
search/*    # (local grep, sqlite query, vector, hybrid)
ai/*        # exporters (MCP, Copilot, Claude Workbench, REST webhook)
policy/*    # adapters (org YAML → runtime enforcement)
```

**Data Flow**
```
Input → Parse → Policy Check → Redact PII → Store → Search/Query → Export Filter → Context Export
```

**Design Rule**: SCP never assumes why data is restricted—it just enforces a configurable Redaction Boundary Contract (RBC).

## AI Workflow Stack Options (Context-Efficient)

| Stack | When to use | Components | How it reduces context while keeping fidelity |
|-------|-------------|------------|-----------------------------------------------|
| **Local-first MCP** | Laptop/on-call with no outbound data | TypeScript CLI + SQLite/pgvector, small open-source embeddings (e.g., `bge-small`), local cross-encoder reranker (e.g., `bge-reranker-base` via WASM) | Embeddings + rerank keep only top 5–10 passages; structured export preserves field-level fidelity while trimming tokens |
| **Summary + Fingerprint Hybrid** | Large cases with repetitive logs | Fast summarizer (DistilBART/LLM 4k context), hashed token fingerprints stored alongside summaries, MCP export merges summary + requested rehydrate fields | Summaries shrink context; fingerprints ensure exact-match recall for rare strings without sending raw PII |
| **Managed LLM Gateway** | Enterprise wanting hosted inference | MCP server → retrieval (pgvector/Qdrant) → reranker (Bedrock Titan Rerank or Cohere) → policy-aware prompt to Bedrock/Vertex/OpenAI | Gateway enforces prompt contracts, reranker boosts precision, and retrieval limits prompt size while keeping high-signal passages |

**Implementation notes**
- Keep the **schema-first context export** (case ID, symptom, error patterns, resolution, evidence pointers). Structured keys compress token use compared to free-text history.
- Use **chunk-size caps (400–800 tokens) + overlap the greater of 10% of the chunk size or 50 tokens** to avoid context bleed; the overlap keeps semantic continuity and prevents error signatures that span boundaries from being split.
- Prefer **reranking before prompting**; sending only the top passages usually cuts context by 60–80% without losing resolution hints.
- For strict profiles, store **rehydration pointers** (token IDs, file offsets) so fidelity can be restored locally even when prompts stay redacted.

## Essential Commands

```bash
# Install (single command)
curl -sSL get.scp.dev | sh   # or npm install -g scp

# Profile-aware usage
scp --profile=enterprise add "ICM-123: Database timeout in prod"
scp --profile=dev add sample.log
scp search "timeout"

# Export with fidelity modes
scp get ICM-123 --mode=summary      # LLM context (redacted, pattern-preserved)
scp get ICM-123 --mode=diagnostic   # Human triage (redacted w/ structure)
scp get ICM-123 --mode=fingerprint  # Dedupe/match only (hashed tokens)
scp get ICM-123 --mode=full         # Authorized debug (rehydrated)

# Rehydration authority flows
scp rehydrate ICM-123 --authority=self     # Local engineer (fastest)
scp rehydrate ICM-123 --authority=team --request  # Team escrow (JIT workflow)
scp rehydrate ICM-123 --authority=broker --ticket 45678  # Policy service (enterprise)

# Policy testing
scp policy-check sample.log  # Shows what would be redacted under current profile
```

## Export Fidelity Modes

| Mode | Use | PII State | Size | AI-ready? |
|------|-----|-----------|------|----------|
| **fingerprint** | dedupe / match only | hashed tokens only | tiny | no |
| **summary** | LLM context | redacted, pattern-preserved snippets | small | yes |
| **diagnostic** | human triage | redacted w/ structure | medium | yes |
| **full** | authorized debug | rehydrated | large | no external send |

## Rehydration Authority Models

SCP supports 3 pluggable authority flows for accessing full (non-redacted) data:

**1. Self-Authority (local engineer)**
- Key lives in local secure store
- Fastest access for authorized debugging
- Suitable for trusted environments

**2. Delegated (team escrow)**
- Vault tokens rehydrated when engineer + team service both approve
- Meets Just-In-Time (JIT) workflow requirements
- Balances security with operational efficiency

**3. Brokered (policy service)**
- External policy engine signs one-time decrypt token
- Logs to audit bus for compliance
- Enterprise-grade with full audit trail

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

**Relevant Fields for SCP Extraction**

| Field Type | ICM Fields | ADO Fields | SCP Usage |
|------------|------------|------------|----------|
| **Identifiers** | Incident ID, SR ID | Work Item ID | Case linking and deduplication |
| **Metadata** | Service Name, Severity, Status, Region | Tags, State, Priority | Context classification and search |
| **Ownership** | Owner/Assignee, PG contact | Assigned To, Area Path | Responsibility tracking (redacted) |
| **Timestamps** | Created, Last Updated, TTM | Created Date, Resolved Date | Timeline analysis and metrics |
| **Content** | Discussion threads, Root Cause | Comments, Description | Solution pattern extraction |
| **Linkages** | ADO Work Items, Repair Items | Linked ICMs, Parent/Child | Relationship mapping |
| **Environment** | Subscription ID, Workspace ID | Custom fields | Customer context (redacted) |

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

**Enhanced Regex Patterns for Detection**
- **Email addresses**: `[\w\.-]+@[\w\.-]+`
- **IP addresses**: `\b(?:\d{1,3}\.){3}\d{1,3}\b`
- **GUIDs/Subscription IDs**: `\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b`
- **Azure Resource IDs**: `/subscriptions/[^/]+/resourceGroups/[^/]+/providers/[^/]+`
- **ICM/SR IDs**: `ICM-\d+|Support-\d+|Incident-\d+`
- **ADO Work Items**: `(?:Work Item|WI|#)\s*(\d{6,})`
- **File Paths**: `[A-Za-z]:\\[^\s<>:"|?*]+|/[^\s<>:"|?*]+`
- **Internal Aliases**: `[a-zA-Z][a-zA-Z0-9._-]*@(microsoft|corp|redmond)\.(com|net)`

**Best Practices for Data Parsing and Cleansing**
- **Use Field-Based Extraction**: Parse structured fields like Incident ID, Severity, Status, Owner, and TTM directly from JSON or XML exports
- **Normalize Discussion Threads**: Extract only action items, root cause summaries, and fix status. Avoid copying full comment threads unless scrubbed
- **Tag Data Source**: Always label whether data came from ICM, ADO, or support case system to maintain traceability
- **Context-Dependent Redaction**: Even internal aliases may be sensitive depending on audience and usage context

### Data Processing Best Practices

**Field-Based Extraction**
- Parse structured fields directly from JSON/XML exports
- Prioritize metadata over freeform content
- Maintain traceability with data source tags

**Discussion Thread Normalization**
- Extract action items and root cause summaries
- Avoid copying full comment threads
- Focus on technical resolution patterns
- **Tag data source**: Always label whether data came from ICM, ADO, or support case system
- **Maintain traceability**: Link extracted solutions back to original incident/work item

**Advanced Parsing Strategies**

**ICM-Specific Parsing**
- **RATIO Integration**: Automatically detect ADO work items linked via RATIO system
- **Repair Item Tracking**: Extract bug IDs and fix status for solution validation
- **Escalation Context**: Parse severity changes and ownership transfers
- **Customer Environment**: Safely extract region, service, and anonymized resource patterns

**ADO Work Item Processing**
- **Tag Analysis**: Use tags (Supportability, Bug, Feature) for automatic categorization
- **Iteration Tracking**: Extract sprint/iteration data for timeline analysis
- **Parent/Child Relationships**: Map feature→bug→task hierarchies
- **Acceptance Criteria**: Parse structured requirements and validation steps

### Policy Adapter Layer (Critical for Cross-Org Adoption)

Let organizations drop in a policy file that maps classification tags → action:

```yaml
pii_policy_version: 1
rules:
  EMAIL:
    redact: token
    reversible: true
    scope: team
  SUBSCRIPTION_ID:
    redact: hash
    reversible: false
    export: deny
  INTERNAL_ALIAS:
    redact: token
    reversible: true
    export: allow-ai-redacted
defaults:
  export_mode: redacted
  audit: append_only
```

This lets a relaxed org loosen restrictions without forking code; a locked org tightens.

### PII Protection Architecture & Implementation Strategy

**Architecture Options (Ranked by Implementation Priority)**

**1. Local PII Extraction and Redaction Only** *RECOMMENDED FIRST*
- **Design**: All PII detection and redaction occurs locally, before any external model call (LLM, API, etc)
- **Proof**: Log transformations and original-to-placeholder mappings with timestamps in append-only audit log
- **Why it helps**: Proves that raw PII never left the machine
- **Implementation**: Simple regex + local vault, easiest to build and audit

**2. One-Way Hashing or Deterministic Pseudonymization**
- **Technique**: Replace PII with SHA-256 w/ per-session salt or deterministic HMAC-based pseudonyms
- **Output**: Tokenized values like `__USER_34F2__` or `__EMAIL_9A5D__`
- **Benefit**: Non-reversible (SHA-256) or reversible only with local secret (HMAC)

**3. Zero PII in Payload Assertion Layer**
- **Built-in check**: Before any external system call, run PII-free assert() test using rule engine
- **Fail-safe**: Abort operation and log incident if PII detected in outbound payload
- **Auditability**: Complete log of assertion checks and failures

**4. Audit Mode + Evidence Package**
- **Generate**: JSON evidence object for each external interaction:
```json
{
  "timestamp": "2025-07-17T13:00Z",
  "outbound_payload": "sanitized_summary_v1.txt",
  "pii_mapping_used": "pii_map_run42.json", 
  "pii_assertion": true,
  "model_used": "gpt-4o-local",
  "location": "local_machine_only"
}
```

**5. PII Mode Switch** *REQUIRED FOR FLEXIBILITY*
```bash
# PII protection OFF - local development/debugging
scp --no-pii-protection add "ICM-123: john.doe@company.com timeout"
scp --no-pii-protection get ICM-123 --full

# PII protection ON - default for sharing/LLM calls  
scp add "ICM-123: [EMAIL_1] timeout"  # Auto-redacted
scp get ICM-123 --context  # Always redacted for external use
```

## Recommended Implementation Approach

**Start with Option 1: Local PII Extraction + Mode Switch**

This provides the perfect balance of:
- **Security**: All PII handled locally, never transmitted
- **Flexibility**: `--no-pii-protection` for development/debugging
- **Simplicity**: Regex patterns + local vault, easy to implement and audit
- **Compliance**: Complete audit trail without complexity

**Why This First**:
1. **Immediate value**: Solves the access paradox without over-engineering
2. **Audit-friendly**: Simple to explain and verify to compliance teams
3. **Extensible**: Foundation for more sophisticated options later
4. **Developer-friendly**: Can turn off protection for local debugging

**Key Implementation Features**:
- Default PII protection ON for all external operations
- `--no-pii-protection` flag for local-only work
- Encrypted local vault with rehydration capabilities
- Append-only audit log showing all transformations
- Pre-flight assertion checks before external calls

This approach lets support engineers work productively while maintaining enterprise-grade security.

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
    "[SUB_ID_1]": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "[WORKSPACE_1]": "workspace-name-prod", 
    "[EMAIL_1]": "user@example.com",
    "[IP_1]": "10.0.0.100"
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

**Adoption Hooks (Make it Irresistible)**
- **90-second bootstrap** script that detects org policy & auto-configures
- **Policy test harness**: `scp policy-check sample.log` shows what would be redacted/exported under each profile
- **MTTR dashboard** plug-in: Count minutes saved vs JIT delays; leadership candy
- **Out-of-the-box connectors** for 2 common tools (ServiceNow + Jira) to prove value quickly

**Community & Ecosystem**
- Open source (MIT license)
- Plugin architecture for custom PII patterns
- Export/import for team sharing
- Integration docs for common support tools (ServiceNow, Jira, etc.)
- **Policy portability**: Same schema works across security cultures

**Success Metrics**
- Time to first successful case search < 2 minutes
- Support engineer adoption rate 
- Context injection accuracy in AI tools
- PII false positive rate < 5%
- **Policy compliance**: Cross-org schema compatibility
- **Security audit pass rate**: 100% for strict/enterprise profiles

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
