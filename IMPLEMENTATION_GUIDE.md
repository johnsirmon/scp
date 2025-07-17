# Support Context Protocol (SCP) - Implementation Guide

## 🎯 Overview

The Support Context Protocol (SCP) is an intelligent, memory-based case triage system designed for support engineering automation and context management. It provides dynamic case data storage, real-time querying, and structured context injection for chat systems and LLM integrations.

## ✨ Key Features

### Core Capabilities
- **Dynamic Case Storage**: In-memory storage with JSON export/import
- **Intelligent Parsing**: Automatic ICM summary and case data extraction
- **Real-time Search**: Text-based and optional vector similarity search
- **Context Management**: Structured case context for LLM injection
- **Automated Analysis**: Auto-tagging, categorization, and EPS flagging

### Integration Features
- **REST API**: FastAPI-based HTTP endpoints
- **CLI Interface**: Command-line tools for case management
- **VSCode MCP Ready**: Designed for Model Context Protocol integration
- **Export/Import**: JSON-based data persistence and migration

## 🏗️ Architecture

```
SCP System Architecture
├── Core Engine (scp/core.py)
│   ├── Case Management
│   ├── Search Orchestration
│   └── Data Persistence
├── Data Models (scp/models.py)
│   ├── SupportCase
│   ├── CaseQuery/Update
│   └── Search Results
├── Memory Store (scp/memory.py)
│   ├── Thread-safe Storage
│   ├── JSON Export/Import
│   └── Statistics
├── Parsers (scp/parsers.py)
│   ├── ICM Text Parser
│   ├── Log Parser
│   └── Auto-tagging
├── Search Engine (scp/search.py)
│   ├── Vector Search (FAISS)
│   ├── Simple Text Search
│   └── Similarity Scoring
├── REST API (scp/api.py)
│   ├── FastAPI Endpoints
│   ├── Case CRUD Operations
│   └── Search & Analytics
└── CLI Interface (scp/cli.py)
    ├── Interactive Commands
    ├── Batch Operations
    └── Data Management
```

## 🚀 Quick Start

### Installation

```bash
# Clone/create the project
git clone <repository> # or use the provided code
cd scp

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install basic dependencies
pip install -r requirements-basic.txt

# Optional: Install vector search dependencies
pip install faiss-cpu sentence-transformers numpy
```

### Basic Usage

```python
from scp.core import SCPManager

# Initialize SCP
scp = SCPManager()

# Add a case from dict
case_data = {
    "case_id": "ICM-123456",
    "title": "Database connection timeout",
    "priority": "high",
    "symptoms": ["Connection refused", "Timeout errors"],
    "customer": "Contoso Corp"
}
case = scp.add_case(case_data)

# Parse ICM text
icm_text = """
ICM-789012: API Gateway 503 errors
Priority: Critical
Customer: Fabrikam Inc

Symptoms:
• Service unavailable
• High latency
"""
parsed_case = scp.add_case(icm_text)

# Search cases
results = scp.search_cases("database timeout")
for result in results:
    print(f"{result.case.case_id}: {result.case.title}")

# Get case context for LLM
context = scp.get_case_context("ICM-123456")
```

## 💻 CLI Usage

### Basic Commands

```bash
# Add a case
python -m scp add-case --case-id ICM-001 --title "Network Issue" --priority high

# Parse ICM text
echo "ICM-123: Database error..." | python -m scp parse-case

# Search cases
python -m scp search "database connection"

# Get case details
python -m scp get-case ICM-001

# Find similar cases
python -m scp similar ICM-001

# System statistics
python -m scp stats

# Interactive mode
python -m scp interactive
```

### Data Management

```bash
# Export all data
python -m scp export > backup.json

# Import data
python -m scp import-data -f backup.json

# Use custom data directory
python -m scp --data-dir /path/to/data stats
```

## 🌐 API Usage

### Start the API Server

```bash
python -m scp api
# Server runs on http://localhost:8000
# Docs available at http://localhost:8000/docs
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/cases` | POST | Create new case |
| `/cases/parse` | POST | Parse case from text |
| `/cases/{id}` | GET | Get case details |
| `/cases/{id}` | PUT | Update case |
| `/cases/{id}` | DELETE | Delete case |
| `/search` | POST | Search cases |
| `/cases/{id}/similar` | GET | Find similar cases |
| `/cases/{id}/context` | GET | Get case context |
| `/stats` | GET | System statistics |
| `/export` | GET | Export all data |
| `/import` | POST | Import data |

### Example API Usage

```bash
# Create a case
curl -X POST "http://localhost:8000/cases" \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": "API-001",
    "title": "API Test Case",
    "priority": "medium"
  }'

# Search cases
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "database",
    "limit": 5
  }'

# Get case context
curl "http://localhost:8000/cases/API-001/context"
```

## 📊 Data Models

### SupportCase
The main case entity with comprehensive fields:

```python
{
  "case_id": "ICM-123456",
  "title": "Database connection timeout",
  "status": "open",
  "priority": "high",
  "customer": "Contoso Corp",
  "product": "Azure SQL Database",
  "symptoms": ["Connection refused", "Timeout errors"],
  "error_messages": ["SqlException: Timeout expired"],
  "tags": [{"name": "database", "confidence": 0.9}],
  "escalation_flags": ["eps_high"],
  "logs": [...],
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### Search and Context
- **CaseQuery**: Flexible search with filters
- **SearchResult**: Cases with similarity scores
- **Case Context**: Structured data for LLM injection

## 🔍 Search Capabilities

### Text Search
Basic keyword matching across all case fields:
- Title, description, symptoms
- Error messages, logs, notes
- Tags and custom fields

### Vector Search (Optional)
Semantic similarity using sentence transformers:
- FAISS-based vector indexing
- Configurable similarity thresholds
- Similar case recommendations

```python
# Enable vector search
scp = SCPManager(use_vector_search=True, vector_model="all-MiniLM-L6-v2")

# Find semantically similar cases
similar = scp.find_similar_cases("ICM-123", limit=5, threshold=0.2)
```

## 🏷️ Auto-Tagging and Analysis

### Automatic Tag Generation
Based on keyword detection:
- **performance**: slow, timeout, latency
- **connectivity**: network, connection, dns
- **database**: sql, database, query
- **api**: api, rest, endpoint
- **security**: auth, permission, certificate

### EPS Flag Detection
Automatic escalation flag detection:
- **eps_critical**: outage, down, critical
- **customer_escalation**: complaint, dissatisfied
- **media_attention**: media, press, public

### ICM Parser Features
- Case ID extraction (multiple formats)
- Priority/severity normalization
- Symptom and error extraction
- Timestamp parsing
- Customer/product identification

## 🔌 Integration Patterns

### VSCode MCP Integration
```typescript
// MCP Server integration
const scp = new SCPClient("http://localhost:8000");

// Inject case context into chat
const context = await scp.getCaseContext(caseId);
const prompt = `Context: ${JSON.stringify(context)}\n\nUser query: ${userMessage}`;
```

### LLM Context Injection
```python
# Get structured context for LLM
context = scp.get_case_context("ICM-123456")

# Context includes:
# - Full case details
# - Similar cases with solutions
# - Summary statistics
# - Escalation status

llm_prompt = f"""
You are a support engineer. Here's the case context:

Case: {context['case']['title']}
Status: {context['case']['status']}
Similar Cases: {len(context['similar_cases'])} found

Previous Solutions:
{[case['solution'] for case in context['similar_cases'] if case['solution']]}

How can I help with this case?
"""
```

### Monitoring Integration
```python
# Real-time case updates
@app.on_event("case_updated")
async def handle_case_update(case_id: str):
    case = scp.get_case(case_id)
    if case.escalation_flags:
        await notify_management(case)
```

## 📈 Performance and Scaling

### Memory Usage
- Efficient in-memory storage
- Configurable persistence intervals
- Automatic cleanup of old data

### Search Performance
- Simple search: O(n) text matching
- Vector search: O(log n) with FAISS index
- Caching for frequent queries

### Scalability Options
- Horizontal scaling via API clustering
- Database backend integration (future)
- Distributed vector search (future)

## 🛡️ Security Considerations

### Data Protection
- No sensitive data persistence by default
- Configurable data retention policies
- Export/import with encryption support

### API Security
- Rate limiting (configurable)
- Input validation and sanitization
- Authentication hooks (extendable)

### Access Control
- Case-level permissions (planned)
- Role-based access (planned)
- Audit logging (planned)

## 🧪 Testing and Development

### Running Tests
```bash
# Basic functionality test
python demo.py

# Full test suite (requires pytest)
pip install pytest
pytest test_scp.py

# Manual testing
python test_scp.py
```

### Development Setup
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Code formatting
black scp/

# Type checking
mypy scp/

# Linting
flake8 scp/
```

## 🔧 Configuration

### Environment Variables
```bash
# Data directory
export SCP_DATA_DIR="/path/to/scp/data"

# Vector search model
export SCP_VECTOR_MODEL="all-MiniLM-L6-v2"

# API configuration
export SCP_API_HOST="0.0.0.0"
export SCP_API_PORT="8000"
```

### Configuration File (Future)
```yaml
# scp-config.yaml
storage:
  data_dir: "./scp_data"
  auto_save_interval: 300
  max_cases: 10000

search:
  vector_enabled: true
  vector_model: "all-MiniLM-L6-v2"
  similarity_threshold: 0.1

api:
  host: "0.0.0.0"
  port: 8000
  cors_enabled: true
```

## 🚀 Deployment Options

### Local Development
```bash
# Start API server
python -m scp api

# Use with custom data directory
python -m scp --data-dir /custom/path api
```

### Docker Deployment (Future)
```dockerfile
FROM python:3.11-slim
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
EXPOSE 8000
CMD ["python", "-m", "scp", "api"]
```

### Cloud Deployment
- **Azure Container Instances**: Direct API deployment
- **AWS Lambda**: Serverless case processing
- **Google Cloud Run**: Auto-scaling API service

## 📋 Roadmap

### Short Term (v0.2)
- [ ] Database backend support (SQLite, PostgreSQL)
- [ ] Enhanced vector search with multiple models
- [ ] Case templates and workflows
- [ ] Advanced filtering and sorting

### Medium Term (v0.3)
- [ ] Real-time collaboration features
- [ ] Integration with major ticketing systems
- [ ] Advanced analytics and reporting
- [ ] Machine learning recommendations

### Long Term (v1.0)
- [ ] Distributed architecture
- [ ] Enterprise security features
- [ ] Custom plugin system
- [ ] Multi-tenant support

## 🤝 Contributing

### Development Process
1. Fork the repository
2. Create feature branch
3. Implement changes with tests
4. Submit pull request

### Code Standards
- Python 3.8+ compatibility
- Type hints for all functions
- Comprehensive docstrings
- Unit test coverage >80%

## 📄 License

MIT License - see LICENSE file for details.

## 🆘 Support

### Common Issues

**Q: Vector search not working?**
A: Install optional dependencies: `pip install faiss-cpu sentence-transformers numpy`

**Q: API won't start?**
A: Check port availability and install: `pip install fastapi uvicorn`

**Q: Memory usage too high?**
A: Configure auto-save and implement case cleanup policies

### Getting Help
- Check the demo: `python demo.py`
- Review examples: `python example.py`
- Use interactive mode: `python -m scp interactive`
- Check API docs: http://localhost:8000/docs

---

**SCP - Intelligent Case Triage for Modern Support Teams** 🚀
