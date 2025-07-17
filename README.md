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
# Install
curl -sSL get.scp.dev | sh

# Add a case
scp add "ICM-123: Database timeout in prod"

# Search for similar issues
scp search "timeout"

# Export context for AI tools
scp get ICM-123 --mode=summary
```

## Security Profiles

| Profile | For | Data Handling | Output |
|---------|-----|---------------|--------|
| **strict** | Regulated/gov | Mandatory redaction | Redacted only |
| **enterprise** | Large tech | Redact w/ JIT rehydrate | Redacted unless --full local |
| **trusted** | Startup/lab | Redact recommended | Mixed |
| **dev** | Personal sandbox | Optional redaction | Full |

## Files

- **`prd.md`** - Complete Product Requirements Document with architecture, security profiles, and implementation roadmap
- **`scp.js`** - Main implementation (Node.js/TypeScript)
- **`mcp-server.js`** - Model Context Protocol server for VSCode integration
- **`install.sh`** & **`demo.sh`** - Setup and demo scripts

## Contributing

This is an open source project focused on making support engineering more efficient while maintaining enterprise-grade security. See `prd.md` for detailed specifications.

---

*"End the Compliance Theater: Be compliant AND productive."*