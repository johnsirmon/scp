# Support Context Protocol (SCP)

**Making tribal knowledge searchable, shareable, and AI-ready**

## The Problem

> *"When you're responsible for solving the issue but apparently not responsible enough to see the logs without asking permission from a team of coworkers, 2 robots, and someone who left the company."*

> *"I'm cleared to close the incidentbut seeing the logs first? Hold on, let's get approval from half the org chart."*

> *"Nothing boosts productivity like waiting two hours for approval to read data I wrote myself yesterday."*

**The Access Paradox**: You need the data to fix the problem, but can't access the data because of the problem you're trying to fix. Meanwhile, the customer is waiting, escalation calls are scheduled, and your manager wants updates on progress you can't make without the data you can't see.

> *"Sure, I'll fix this Sev1 outage right after I fill out form B-47 to request permission to see error messages."*

> *"Day 3 of the incident: Still waiting for data access. Customer asks for updates. I send them a haiku about bureaucracy."*

> *"The approval system is down, so now I need approval to request approval to see why the approval system is down."*

## The Solution

**Policy-Adaptive Support Context Protocol**: A tiny core executable with modular security that adapts from "air-gapped, sign in triplicate" to "paste logs in Slack" without code forks.

**SCP breaks the access paradox**: Hash and strip PII for safe storage, then rehydrate with full specificity when debugging - no permission slips required.

**Bring Your Own Paranoia**: Locked-down bank? Run in strict modeHSM keys, outbound scrub walls, audit bus. Startup lab? Use trusted modelocal AES vault, fast paste-to-search. Same schema. Same CLI. Your paranoia level, your call.

## Quick Start

```bash
# Install dependencies
npm install

# Add a case from clipboard
node scp.js add --paste

# Add a case from file
node scp.js add --file case-data.txt

# Search for similar issues
node scp.js search "timeout"

# Export context for AI tools
node scp.js get ICM-123 --context

# Monitor clipboard for automatic case detection
node scp.js monitor

# Run in memory-only mode (no disk persistence)
node scp.js --memory add --paste
```

## Windows QuickStart

**Prerequisites:** Node.js 18+ installed on Windows 10/11

```powershell
# Clone and setup
git clone <repository-url>
cd scp
npm install

# Test clipboard functionality (copy some text first)
node scp.js add --paste

# Start real-time clipboard monitoring for ICM/case data
node scp.js monitor

# Add a case from file
node scp.js add --file "C:\path\to\case-data.txt"

# Search cases
node scp.js search "timeout"

# Get AI-ready context
node scp.js get ICM-123456 --context

# Memory-only mode (no disk writes - perfect for secure environments)
node scp.js --memory monitor
```

**Windows-Specific Features:**
- Native PowerShell clipboard integration (`Get-Clipboard`)
- UNC path detection and redaction (`\\server\share\file`)
- Windows registry key patterns (`HKEY_LOCAL_MACHINE\...`)
- Windows file paths (`C:\Users\...`) 
- Compatible with Windows Security policies

## Core Features

- **Cross-platform clipboard support** (Windows PowerShell, macOS pbpaste, Linux xclip)
- **In-memory mode** for lightweight operation with `--memory` flag
- **Enhanced PII detection** with dual-pass regex and contextual AI patterns
- **Real-time clipboard monitoring** with smart case ID extraction
- **AES-256 encrypted PII vault** with rehydration capabilities
- **Model Context Protocol server** for VSCode integration
- **Windows-specific patterns** (UNC paths, registry keys, Windows IDs)

## Windows Testing & Troubleshooting

**PowerShell Execution Policy Issues:**
```powershell
# If clipboard access fails, check execution policy
Get-ExecutionPolicy
# If restricted, temporarily allow for current session:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Testing Clipboard Functionality:**
```powershell
# Manual test of PowerShell clipboard command
Get-Clipboard | Out-String

# Test with sample ICM data
"ICM-123456: Sample case data for testing" | Set-Clipboard
node scp.js add --paste
```

**Common Windows Issues:**
- **Clipboard access denied**: Run PowerShell as Administrator or adjust execution policy
- **File path issues**: Use double quotes around paths with spaces
- **Node.js not found**: Ensure Node.js is in PATH or use full path to node.exe
- **Permission denied on .scp folder**: Check Windows folder permissions in %USERPROFILE%\.scp

## Files

- **`prd.md`** - Complete Product Requirements Document with architecture, security profiles, and implementation roadmap
- **`scp.js`** - Main implementation (Node.js/TypeScript)
- **`mcp-server.js`** - Model Context Protocol server for VSCode integration
- **`install.sh`** & **`demo.sh`** - Setup and demo scripts

## Contributing

This is an open source project focused on making support engineering more efficient while maintaining enterprise-grade security. See `prd.md` for detailed specifications.

---

*"End the Compliance Theater: Be compliant AND productive."*