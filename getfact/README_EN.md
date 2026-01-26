# GetFact - Fact and Relationship Extractor

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![LLMaaS](https://img.shields.io/badge/LLMaaS-Compatible-green.svg)

This script automatically extracts facts and relationships between facts from a text file using the Cloud Temple LLMaaS API. It can optionally use a provided ontology to improve extraction accuracy and saves results in JSON or YAML format.

## 🌟 Features

- **Intelligent Extraction**: Automatically identifies entities, events, relationships, attributes, temporal, and spatial information.
- **Ontology Support**: Optionally uses an ontology file (JSON/YAML/TXT) to guide extraction.
- **Intelligent Chunking**: Processes long documents by splitting them into logical chunks.
- **Output Formats**: Saves in JSON or YAML format with an organized structure.
- **Interactive Mode**: Allows validation/modification of extraction for each chunk.
- **Rich Interface**: Colorful display with progress bars and detailed summaries.
- **Flexible Configuration**: Parameters configurable via command line and environment variables.
- **Reasoning Model Support**: Automatically handles responses from models that include thinking blocks (e.g., `<think>...</think>`) before JSON.
- **Robust JSON Parsing**: Reliably extracts JSON content even from malformed responses or those containing extraneous text.

## 🧠 Specialized Ontologies

GetFact includes 6 ready-to-use business ontologies for optimized contextual extraction. These files are located in the `ontologies/` folder.

| Ontology | Domain | File | Description & Usage |
|---|---|---|---|
| 🏛️ **Legal** | Law, litigation, compliance | `ontologie_droit.yaml` | **Entities**: Lawyers, Judges, Legal articles, Contracts.<br>**Relationships**: "violates", "stipulates that", "sues".<br>**Usage**: Analysis of contracts, judgments, and compliance documents. |
| 👥 **HR** | Human Resources, HRIS | `ontologie_rh.yaml` | **Entities**: Candidates, Positions, Skills, Degrees.<br>**Relationships**: "has skill", "worked at", "applies for".<br>**Usage**: Analysis of CVs, interview reports, career plans. |
| 💻 **Development** | DevOps, software engineering | `ontologie_developpement.yaml` | **Entities**: Languages, Frameworks, Bugs, Features, PR.<br>**Relationships**: "depends on", "fixes", "implements".<br>**Usage**: Analysis of technical documentation, Jira tickets, code reviews. |
| 🔒 **Security** | Cybersecurity, CISO | `ontologie_securite_logique.yaml` | **Entities**: Threats, Vulnerabilities (CVE), Assets, Attackers.<br>**Relationships**: "exploites", "mitigates", "affects".<br>**Usage**: Incident reports, security audits, threat analysis. |
| ☁️ **Infrastructure** | Cloud, datacenters, networks | `ontologie_infrastructure_cloud.yaml` | **Entities**: VMs, Containers, VPCs, Load Balancers.<br>**Relationships**: "hosted on", "connected to", "protected by".<br>**Usage**: Inventory reports, architecture documents, infrastructure logs. |
| 🤝 **IT Management** | Managed services, ITIL | `ontologie_infogerance.yaml` | **Entities**: SLAs, Tickets, Incidents, Changes.<br>**Relationships**: "resolved by", "escalated to", "impacts".<br>**Usage**: Service quality monitoring, activity reports, incident management. |

### Usage Examples by Domain

```bash
# Legal analysis - commercial contract
python getfact.py --file contract.txt --ontology ontologie_droit.yaml

# HR - CV analysis
python getfact.py --file candidate_cv.txt --ontology ontologie_rh.yaml

# Security - incident report
python getfact.py --file security_incident.txt --ontology ontologie_securite_logique.yaml

# Infrastructure - performance report
python getfact.py --file perf_report.txt --ontology ontologie_infrastructure_cloud.yaml
```

## 📋 Extracted Fact Types

| Type | Description | Examples |
|---|---|---|
| **Entities** | People, organizations, places, objects, concepts | John Doe, Cloud Temple, Paris, server |
| **Events** | Actions, processes, incidents, situations | meeting, deployment, incident, training |
| **Relationships** | Connections between entities | works for, located in, depends on |
| **Attributes** | Properties, characteristics, qualities | color, size, performance, status |
| **Temporal** | Dates, durations, temporal sequences | 2025-06-04, 2 hours, before/after |
| **Spatial** | Locations, relative positions | north of, next to, datacenter |

## 🚀 Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Configuration
cp .env.example .env
# Edit the .env file with your parameters
```

## ⚙️ Configuration

### Environment Variables (.env)

```bash
# LLMaaS API Key (required)
LLMAAS_API_KEY=your_api_key_here

# LLMaaS API URL
LLMAAS_API_URL=https://api.ai.cloud-temple.com/v1

# Model to use for extraction
LLMAAS_GETFACT_MODEL=qwen3:14b

# Default output format (json or yaml)
LLMAAS_OUTPUT_FORMAT=json

# Maximum number of tokens for responses
LLMAAS_MAX_TOKENS=4096

# Chunk size in words
LLMAAS_CHUNK_SIZE_WORDS=500

# Output directory
LLMAAS_OUTPUT_DIR=extracted_facts

# Optional custom system prompt
LLMAAS_CUSTOM_PROMPT=""
```

## 💡 Usage

### Basic Usage

```bash
# Simple extraction from a text file
python getfact.py --file document.txt

# With ontology to guide extraction
python getfact.py --file document.txt --ontology example_ontology.yaml

# Output in YAML format
python getfact.py --file document.txt --output-format yaml
```

### Advanced Options

```bash
# Interactive mode with validation
python getfact.py --file document.txt --interactive

# Specific fact types
python getfact.py --file document.txt --fact-types entities events relationships

# Custom model and parameters
python getfact.py --file document.txt --model granite3:8b --max-tokens 2048

# Debug mode to see chunking
python getfact.py --file document.txt --debug

# With custom system prompt
python getfact.py --file document.txt --custom-prompt "Focus on financial aspects and amounts"
```

### Custom System Prompt

The custom prompt feature allows adding specific instructions to guide extraction according to your needs:

```bash
# Focus on regulatory compliance
python getfact.py --file audit_report.txt \
  --custom-prompt "Pay particular attention to non-compliances, regulatory references, and corrective actions"

# Performance-oriented extraction
python getfact.py --file system_logs.txt \
  --custom-prompt "Prioritize identification of performance metrics, response times, and bottlenecks"

# Sentiment analysis in customer feedback
python getfact.py --file feedback_clients.txt \
  --custom-prompt "Extract emotions, positive/negative sentiments, and customer satisfaction level"
```

**Via environment variable:**
```bash
export LLMAAS_CUSTOM_PROMPT="Focus on operational and financial risks"
python getfact.py --file risk_assessment.txt
```

### Help and Version

```bash
# Display full help
python getfact.py --help

# Display version
python getfact.py --version
```

## 📄 File Formats

### Input File
- **Supported formats**: TXT, MD, or any UTF-8 text file
- **Size**: Automatic chunking for large documents
- **Encoding**: UTF-8 recommended

### Ontology (optional)
The ontology can be provided in several formats:

#### JSON
```json
{
  "entities": {
    "person": ["first_name", "last_name", "title"],
    "organization": ["name", "type", "sector"],
    "location": ["city", "country", "region"]
  },
  "relationships": {
    "employment": ["works for", "employed by"],
    "location": ["located in", "based in"],
    "hierarchy": ["manages", "supervises"]
  }
}
```

#### YAML
```yaml
entities:
  person:
    - first_name
    - last_name
    - title
  organization:
    - name
    - type
    - sector
relationships:
  employment:
    - "works for"
    - "employed by"
```

#### TXT (free format)
```
Important entity types:
- People: first name, last name, function
- Organizations: name, industry
- Locations: city, country

Relationships to identify:
- Hierarchy: who manages whom
- Location: where is what
- Temporality: when does what happen
```

## 📊 Output Format

### JSON/YAML Structure

```json
{
  "facts": [
    {
      "id": "fact_1",
      "type": "entity",
      "content": "John Doe is a DevOps engineer",
      "entities_involved": ["John Doe", "DevOps engineer"],
      "confidence": 0.95,
      "source_text": "John Doe, DevOps engineer at Cloud Temple",
      "context": "Team presentation",
      "chunk_source": 1
    }
  ],
  "relationships": [
    {
      "id": "rel_1",
      "type": "employment",
      "source_fact_id": "fact_1",
      "target_fact_id": "fact_2",
      "relationship_description": "John Doe works for Cloud Temple",
      "confidence": 0.90,
      "chunk_source": 1
    }
  ],
  "summary": {
    "total_facts": 42,
    "total_relationships": 15,
    "fact_types_count": {
      "entity": 18,
      "event": 12,
      "relationship": 8,
      "attribute": 4
    },
    "main_entities": ["John Doe", "Cloud Temple", "Paris"],
    "key_themes": ["infrastructure", "team", "project"],
    "chunks_processed": 3
  },
  "metadata": {
    "extraction_version": "1.0.0",
    "timestamp": "2025-06-04T20:15:30",
    "source_file": "document.txt"
  }
}
```

## 🎯 Usage Examples

### CV Analysis
```bash
python getfact.py --file candidate_cv.txt --fact-types entities attributes temporal
```

### Incident Report Analysis
```bash
python getfact.py --file incident_report.txt --ontology example_ontology.yaml --interactive
```

### Extraction for Knowledge Base
```bash
python getfact.py --file documentation.md --output-format yaml --chunk-size-words 800
```

## 🔧 Recommended Models

| Model | Usage | Advantages |
|---|---|---|
| `qwen3:14b` | General use | Good precision/speed balance |
| `granite3:8b` | Short documents | Fast, efficient |
| `deepseek-r1:7b` | Complex analysis | Advanced reasoning |
| `cogito:7b` | Specialized texts | Excellent for technical domains |

## 📈 Performance Optimization

### Recommended Parameters by Document Size

| Document Size | chunk-size-words | max-tokens | Model |
|---|---|---|---|
| < 1000 words | 500 | 4096 | granite3:8b |
| 1000-5000 words | 400 | 8192 | qwen3:14b |
| > 5000 words | 300 | 16384 | qwen3:14b |

### Optimization Tips
- **Ontology**: Use a specialized ontology for your domain.
- **Chunks**: Reduce size for information-dense texts.
- **Interactive Mode**: Use it to refine your approach on small samples.
- **Fact Types**: Limit to relevant types for your use case.

## 🐛 Troubleshooting

### Common Errors

**API Key Error**
```
Error: LLMAAS_API_KEY environment variable is not defined.
```
→ Check your `.env` file and the value of `LLMAAS_API_KEY`.

**Invalid JSON Response**
```
Warning: Invalid JSON response for chunk 2
```
→ The script is now more robust and attempts to extract JSON even if the response is malformed. If the error persists, it may be due to a response truncated by the API. In this case, try increasing the `--max-tokens` value.

**API Timeout**
```
API error for chunk 1: timeout
```
→ The model may be overloaded, try again or change model.

### Debug Mode
Use `--debug` for advanced diagnostics. This option enables very detailed logs, including:
- Precise text chunking breakdown.
- Complete JSON payload sent to the API for each chunk.
- Raw response (status code, headers, and body) received from the API.

```bash
# Enable debug mode for thorough analysis
python getfact.py --file document.txt --debug
```

## 🤝 Contribution

This example is part of the Cloud Temple LLMaaS project. For any improvement suggestions:

1. Open an issue to discuss proposed changes.
2. Respect existing code style and conventions.
3. Test your changes with different document types.
4. Document new features.

## 📄 License

This script is distributed under the same license as the main LLMaaS project.

---

**Cloud Temple - LLMaaS Team**  
*Sovereign and Secure Artificial Intelligence*
