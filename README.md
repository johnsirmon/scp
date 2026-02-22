# Support Context Protocol (SCP)

**Making tribal knowledge searchable, shareable, and AI-ready**

SCP is a lightweight, local-first tool for support engineers. It captures case data, automatically strips sensitive information (PII), stores it locally in a searchable format, and injects relevant context into AI tools like GitHub Copilot and Claude — so you can find and fix problems faster.

---

## The Problem

Support engineers deal with a handful of the same painful problems every day:

**1. Re-solving the same problems**
You spend 2 hours debugging a timeout issue — only to discover a coworker solved the exact same thing last month. That fix exists somewhere in a Slack thread, a closed ticket, or someone's head. You just can't find it.

**2. Context-switching overhead**
To debug one issue, you're juggling: the incident ticket, the related logs, the ADO work item, three browser tabs, and a Slack thread from 6 weeks ago. Getting AI help means copying and pasting all of it manually, over and over.

**3. The access paradox**
You need the logs to fix the problem — but you can't see the logs because of the problem you're trying to fix. The customer is waiting. Escalation calls are scheduled. But first: approval from half the org chart to read data you wrote yourself yesterday.

**4. Sharing context with AI tools is painful**
Pasting raw logs into Copilot or ChatGPT risks leaking customer data. So you either risk it, spend 20 minutes manually redacting, or skip AI assistance entirely. None of these are good options.

---

## The Solution

SCP solves all of this with a single CLI tool:

1. **Ingest** — paste logs, drop a file, or let SCP monitor your clipboard for case data automatically
2. **Redact** — PII (emails, IPs, subscription IDs, GUIDs, file paths, etc.) is stripped and stored in an encrypted local vault before anything is saved or shared
3. **Store** — cases are saved locally in a searchable JSON database
4. **Search** — find similar past cases by symptom, error message, or keyword in seconds
5. **Inject** — export AI-ready context to GitHub Copilot, Claude, or any MCP-compatible tool — with PII already removed

> **SCP breaks the access paradox**: raw data is redacted on ingestion and stored safely. You keep the diagnostic value without the compliance risk. No permission slips required.

---

## Quick Start

**Prerequisites:** Node.js 20+

```bash
# Clone and install
git clone https://github.com/johnsirmon/scp.git
cd scp
npm install

# Copy some case/log data to clipboard, then:
node scp.js add --paste

# Or add from a file
node scp.js add --file case-data.txt

# Search past cases by symptom or error
node scp.js search "timeout"

# Get AI-ready context for a case (PII already redacted)
node scp.js get ICM-123 --context

# Watch clipboard automatically — great for active incident work
node scp.js monitor

# Memory-only mode — nothing written to disk (useful in locked-down environments)
node scp.js --memory add --paste
```

### Windows

```powershell
git clone https://github.com/johnsirmon/scp.git
cd scp
npm install

# Paste from clipboard
node scp.js add --paste

# Monitor clipboard in real time
node scp.js monitor

# Add from file (use quotes for paths with spaces)
node scp.js add --file "C:\path\to\case-data.txt"

# Search and get AI context
node scp.js search "timeout"
node scp.js get ICM-123456 --context
```

**Windows-specific features:**
- Native PowerShell clipboard integration (`Get-Clipboard`)
- Redacts UNC paths (`\\server\share\file`), registry keys (`HKEY_LOCAL_MACHINE\...`), and Windows file paths (`C:\Users\...`)

---

## Key Features

| Feature | What it does |
|---|---|
| **Auto PII redaction** | Strips emails, IPs, GUIDs, Azure resource IDs, file paths, and more on ingestion |
| **Encrypted local vault** | PII tokens stored locally with AES-256; never transmitted |
| **Clipboard monitoring** | Watches clipboard and auto-extracts case data as you copy |
| **Searchable case store** | Find past cases by error message, symptom, or keyword |
| **AI context export** | One command to get a clean, redacted context blob for Copilot or Claude |
| **MCP server** | VS Code integration — auto-injects relevant case context while you code |
| **Memory-only mode** | Run with `--memory` for zero disk writes — ideal for secure environments |
| **Cross-platform** | Works on Windows (PowerShell), macOS (pbpaste), and Linux (xclip) |
| **Security profiles** | Choose from `dev`, `trusted`, `enterprise`, or `strict` to match your environment |

---

## Security Profiles

SCP adapts to your organization's security requirements without changing your workflow:

| Profile | Good for | PII handling | Vault | Network |
|---|---|---|---|---|
| `dev` | Local sandbox / demos | Optional | Plain or encrypted | Unrestricted |
| `trusted` | Startup / internal lab | Recommended, toggleable | Local encrypted | Normal |
| `enterprise` | Large org / internal prod | Redact with override + JIT rehydrate | Encrypted, org escrow optional | Controlled egress |
| `strict` | Regulated / finserv / gov | Mandatory, deny outbound raw | AES-256 + HSM/KMS | Offline by default |

```bash
# Enterprise default
node scp.js --profile=enterprise add --paste

# Strict mode with audit evidence
node scp.js --profile=strict get ICM-123 --context --evidence audit.json

# Dev mode for local testing
node scp.js --profile=dev add sample.log
```

---

## How It Works with AI Tools

SCP includes a [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server. Once configured in VS Code, it automatically surfaces relevant past cases as context when you're debugging — no manual copy-paste needed.

```bash
# Start the MCP server
node mcp-server.js
```

Or export a context blob manually to paste into any AI tool:

```bash
node scp.js get ICM-123 --context
# Output: clean JSON with redacted symptoms, error patterns, and resolution notes
```

---

## Troubleshooting

**Windows: clipboard access denied**
```powershell
# Check and update execution policy if needed
Get-ExecutionPolicy
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Windows: node not found**
Ensure Node.js is in your PATH, or use the full path to `node.exe`.

**Permission denied on `.scp` folder**
Check folder permissions at `%USERPROFILE%\.scp` (Windows) or `~/.scp` (macOS/Linux).

---

## Files

| File | Description |
|---|---|
| `scp.js` | Main CLI — all core commands |
| `mcp-server.js` | MCP server for VS Code integration |
| `src/` | TypeScript source (compiled to `dist/`) |
| `prd.md` | Full product requirements, architecture, and security design |
| `install.sh` / `demo.sh` | Setup and demo scripts |

---

## Contributing

SCP is open source (MIT). It's designed to make support engineering faster without sacrificing security. See [`prd.md`](prd.md) for architecture details, security profile specs, and the implementation roadmap.

---

*"End the Compliance Theater: Be compliant AND productive."*
