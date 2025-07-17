# Support Context Protocol (SCP)

An intelligent, memory-based case triage system for support engineering automation.

## Features

- Dynamic case data storage and management per ICM/SupportCase ID
- Real-time querying and structured context injection
- Automated summarization, tagging, and categorization
- EPS flagging and RenderedDescription analysis
- Vector search for similar cases using FAISS
- REST API and CLI interfaces
- JSON export/import capabilities
- Integration-friendly design for VSCode MCPs and LLM systems

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

### CLI Usage

```bash
# Start interactive CLI
python -m scp.cli

# Add a case directly
python -m scp.cli add-case --case-id ICM-123456 --summary "Database connection timeout"

# Query cases
python -m scp.cli search --query "database timeout"
```

### API Usage

```bash
# Start the API server
python -m scp.api

# The API will be available at http://localhost:8000
# Interactive docs at http://localhost:8000/docs
```

### Python Usage

```python
from scp.core import SCPManager

# Initialize SCP
scp = SCPManager()

# Add case data
case_data = {
    "case_id": "ICM-123456",
    "summary": "Database connection timeout",
    "symptoms": ["Connection refused", "Timeout after 30s"],
    "priority": "high"
}
scp.add_case(case_data)

# Query similar cases
similar = scp.find_similar_cases("database connection issues", limit=5)
```

## Architecture

The SCP system consists of several key components:

- **Core Engine** (`scp/core.py`): Main case management logic
- **Data Models** (`scp/models.py`): Pydantic models for structured data
- **Memory Store** (`scp/memory.py`): In-memory storage with persistence
- **Vector Search** (`scp/search.py`): FAISS-based similarity search
- **Parsers** (`scp/parsers.py`): ICM/case data parsing utilities
- **API Interface** (`scp/api.py`): FastAPI REST endpoints
- **CLI Interface** (`scp/cli.py`): Command-line interface

## Integration

SCP is designed to integrate with:
- VSCode Model Context Protocol (MCP) servers
- LLM systems for context injection
- Support ticketing systems
- Monitoring and alerting platforms
