Support Context Protocol (SCP) PRD

Overview

SCP is a local, secure protocol and toolkit for managing support case context, enabling case triage, search, and automation without exposing PII.

Goals and Objectives

Provide a unified interface for ingesting, storing, and querying case data by ID

Enforce end-to-end PII removal and rehydration workflows

Support integration with MCP servers and LLMs for context injection

Optimize for in-memory performance, storage efficiency, and offline operation

Key Features

Case Ingestion: Clipboard, CLI, REST, file-based inputs

Structured Parser: Extract fields (CaseID, summary, symptoms, metadata)

PII Redaction: Configurable redaction pipeline with token placeholder mapping

PII Rehydration: Secure local vault to rehydrate redacted data post-LLM response

Vector Search: FAISS-based similarity search across cases

Summarization & Tagging: Automated LLM-driven summaries, tags, priorities

APIs & SDK: RESTful API, Python SDK, CLI commands

MCP Integration: VSCode extension embedding SCP context provider

Persistence & Export: JSON import/export, optional disk persistence

PII Handling Workflow

Redaction: On ingest, identify and replace PII with tokens

Storage: Store redacted text and PII mappings separately (encrypted vault)

Context Injection: Send redacted context to LLM/MCP

Rehydration: Upon response, reintegrate PII from vault into output

Architecture

Core Engine (scp/core.py): Orchestrates pipelines

Data Models (scp/models.py): Pydantic schemas

Memory Store (scp/memory.py): In-memory + optional persistence

Search Module (scp/search.py): FAISS index management

Redaction Module (scp/redact.py): Pattern-based and ML-driven PII removal

Vault (scp/vault.py): Encrypted local PII mapping store

API (scp/api.py): FastAPI endpoints

CLI (scp/cli.py): Typer-based commands

MCP Adapter (scp/vscode/adapter.ts): VSCode context provider extension

User Workflows

Ingest a Case

scp add --case-id ICM-123 --input-file ./logs.txt

Redact PII, index data, store mapping in vault

Query Cases

scp search --query "timeout" --context mcp

Returns redacted results; VSCode MCP injects context

Fetch Full Case

scp get --case-id ICM-123 --rehydrate

Retrieves original data with PII rehydrated locally

API Endpoints

Method

Path

Description

GET

/cases/{id}

Get redacted case summary

POST

/cases

Ingest new case data with redaction

GET

/cases/{id}/full

Fetch rehydrated full case data

GET

/search

Vector search across cases

CLI Commands

scp add        # Ingest case data
scp get        # Retrieve case (redacted or full)
scp search     # Query similar cases
scp vault      # Manage PII vault entries
scp serve      # Launch REST API server

Installation & Deployment

git clone <repo>

pip install -r requirements.txt

(Optional) scp serve --host 0.0.0.0 --port 8000

Install VSCode extension: vsix from release/*.vsix

Roadmap

v1.0: Core engine, redaction, vault, CLI, API

v1.1: VSCode MCP extension, summarization service

v2.0: GUI dashboard, multi-user sync, advanced analytics

Adoption & Contribution

Follow semantic versioning

Submit issues and PRs against main

Code of Conduct and contribution guidelines in CONTRIBUTING.md

Compliance & Security

AES-256 encryption for vault

Configurable regex and ML models for PII detection

Audit logs for redaction and rehydration events