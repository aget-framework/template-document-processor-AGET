# template-document-processor-AGET

**Version**: 2.7.0
**Type**: AGET Template
**Domain**: Document Processing

A production-ready template for creating document processing agents with LLM pipelines, security protocols, and multi-provider support.

## Overview

This template provides a complete foundation for agents that:
- ✅ Process documents using LLM assistance (OpenAI, Anthropic, Google)
- ✅ Support batch operations with validation pipelines
- ✅ Implement security protocols (injection prevention, content filtering)
- ✅ Provide caching, metrics, and observability
- ✅ Enable task decomposition for large documents
- ✅ Support rollback and version management

## Based on L208

This template is based on **L208: Document Processing Agent Template Pattern**, which analyzed:
- **private-docx-AGET** (v2.7.0) - DOCX processing with OpenAI Structured Outputs
- **private-RKB-CONTENT_ENHANCER-aget** (v4.0) - Wiki content management

**Time Savings**: 60-70% reduction in new agent setup (3-5 hours → 1-2 hours)

## Quick Start

### 1. Clone Template

```bash
gh repo clone aget-framework/template-document-processor-AGET my-document-agent
cd my-document-agent
```

### 2. Customize Configuration

Update these files:

**`.aget/version.json`**:
```json
{
  "agent_name": "my-document-agent",
  "domain": "your-domain"
}
```

**`config/document_type.yaml`**:
```yaml
document_type: "pdf"  # or "docx", "markdown", "wikitext"
file_extensions: [".pdf"]
size_limits:
  max_pages: 100
  max_bytes: 10485760
```

**`config/llm_providers.yaml`**:
```yaml
primary_provider: "openai"
fallback_providers: ["anthropic", "google"]
budget:
  monthly_limit: 300
```

### 3. Update Mission

Edit `AGENTS.md` to describe your agent's specific purpose and domain.

### 4. Run Tests

```bash
python3 -m pytest tests/ -v
```

### 5. Deploy

```bash
git remote set-url origin <your-repo-url>
git add .
git commit -m "feat: Initialize from template-document-processor-AGET v2.7.0"
git push -u origin main
```

## Architecture

### Core Components

- **`src/ingestion/`** - Queue management, validation, batch processing
- **`src/processing/`** - LLM providers, model routing, caching, schema validation
- **`src/output/`** - Publishing, version management, rollback
- **`src/security/`** - Input sanitization, content filtering, resource limiting
- **`src/pipeline/`** - Task decomposition, orchestration, metrics
- **`src/wikitext/`** - Domain-specific support (extensible for other formats)

### Configuration Files

- **`config/document_type.yaml`** - Document format configuration
- **`config/external_system.yaml`** - External API integration
- **`config/validation_rules.yaml`** - Validation criteria
- **`config/llm_providers.yaml`** - LLM provider configuration
- **`config/approval_gates.yaml`** - Authorization settings
- **`config/model_routing.yaml`** - Model selection strategy
- **`config/security_policy.yaml`** - Security configuration
- **`config/caching.yaml`** - Cache settings
- **`config/metrics.yaml`** - Metrics and alerts
- **`config/orchestration.yaml`** - Task decomposition

## Customization Points

### 1. Document Type

Customize `config/document_type.yaml` for your document format:
- File extensions
- Size limits
- Format-specific validation

### 2. External System

Configure `config/external_system.yaml` for integration:
- MediaWiki API
- GitHub API
- S3 bucket
- Filesystem
- Custom APIs

### 3. LLM Providers

Set up providers in `config/llm_providers.yaml`:
- API keys (use environment variables)
- Model selection (cost vs quality)
- Fallback chain
- Budget limits

### 4. Security

Configure security in `config/security_policy.yaml`:
- Input sanitization rules
- Content filtering (PII detection)
- Resource limits (tokens, time, cost)

### 5. Metrics

Define metrics in `config/metrics.yaml`:
- Accuracy tracking
- Latency monitoring (p50/p95/p99)
- Cost tracking
- Alert thresholds

## Protocols

The template includes 9 operational protocols in `.aget/docs/protocols/`:

1. **Queue Management** - Managing document queues
2. **Processing Authorization** - Approval gates and STOP protocol
3. **Validation Pipeline** - Pre/post validation
4. **Rollback** - Version management and recovery
5. **Security Validation** - Input/output sanitization
6. **Task Decomposition** - Breaking large documents into subtasks
7. **Model Routing** - Selecting optimal LLM for each task
8. **Caching** - LLM response caching for cost/speed
9. **Metrics Collection** - Tracking accuracy/latency/cost

Each protocol includes bash commands and code examples.

## Scripts

The template provides 15 operational scripts in `scripts/`:

**Session Management**:
- `session_protocol.py` - Wake up/wind down/sign off
- `queue_status.py` - Queue management CLI
- `health_check.py` - System diagnostics

**Operations**:
- `validate.py` - Pre/post validation
- `process.py` - Document processing CLI
- `audit.py` - Audit trail viewer
- `rollback.py` - Rollback operations
- `security_check.py` - Security validation
- `model_router.py` - Model routing CLI
- `cache_setup.py` - Cache configuration
- `cache_stats.py` - Cache statistics
- `cache_clear.py` - Cache management
- `checkpoint.py` - Checkpoint management
- `metrics.py` - Metrics CLI
- `task_planner.py` - Task decomposition planner

## Testing

Template includes 30+ contract tests:

```bash
# Run all tests
python3 -m pytest tests/ -v

# Run specific test category
python3 -m pytest tests/test_processing.py -v
```

Test coverage:
- Identity validation
- Structure validation
- Configuration validation
- Protocol validation
- Module functionality
- Script functionality
- Integration workflows

## Examples

See `examples/` directory for complete instantiation examples:

- **`examples/pdf_processor/`** - PDF extraction agent
- **`examples/markdown_enhancer/`** - Markdown enhancement agent

## Version History

**v2.7.0** (2025-10-26)
- Initial template release
- Based on L208 document processing pattern
- 18 source modules
- 8 configuration files
- 9 operational protocols
- 30+ contract tests
- Wikitext support included

## Support

For template issues or questions:
- Template repository: https://github.com/aget-framework/template-document-processor-AGET
- AGET framework: https://github.com/aget-framework

## License

[To be determined by aget-framework organization]

---

*Generated by AGET v2.7.0*
