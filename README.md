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

This template is based on **L208: Document Processing Agent Template Pattern**, which analyzed production document processing agents to extract common patterns and best practices.

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

**`configs/validation_rules.yaml`**:
```yaml
max_file_size_mb: 10
allowed_extensions: [".pdf", ".docx", ".txt", ".md"]
required_validations:
  - file_size
  - file_format
  - content_safety
```

**`configs/llm_providers.yaml`**:
```yaml
providers:
  openai:
    api_key_env: OPENAI_API_KEY
    enabled: true
  anthropic:
    api_key_env: ANTHROPIC_API_KEY
    enabled: false
budget:
  monthly_limit_usd: 300.0
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

### Configuration Files (9 YAMLs)

- **`configs/validation_rules.yaml`** - Document validation criteria
- **`configs/llm_providers.yaml`** - LLM provider configuration
- **`configs/model_routing.yaml`** - Model selection strategy
- **`configs/models.yaml`** - Model definitions and capabilities
- **`configs/security_policy.yaml`** - Security and content filtering
- **`configs/processing_limits.yaml`** - Resource limits (tokens, time, cost)
- **`configs/caching.yaml`** - Cache settings and TTL
- **`configs/metrics.yaml`** - Metrics collection and alerts
- **`configs/orchestration.yaml`** - Task decomposition and pipeline

## Customization Points

### 1. Document Validation

Customize `configs/validation_rules.yaml` for your document format:
- File extensions
- Size limits
- Format-specific validation rules

### 2. LLM Providers

Set up providers in `configs/llm_providers.yaml`:
- API keys (use environment variables)
- Model selection (cost vs quality)
- Fallback chain
- Budget limits

### 3. Security

Configure security in `configs/security_policy.yaml`:
- Input sanitization rules
- Content filtering (PII detection)
- Resource limits (tokens, time, cost)

### 4. Metrics

Define metrics in `configs/metrics.yaml`:
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

The template provides 17 operational tools (15 scripts + 2 helper tools):

**Session Management**:
- `session_protocol.py` - Wake up/wind down/sign off
- `queue_status.py` - Queue management CLI
- `health_check.py` - System diagnostics

**Core Operations** (`scripts/`):
- `validate.py` - Document validation CLI
- `process.py` - End-to-end processing pipeline
- `queue_status.py` - Queue status and management
- `rollback.py` - Version rollback operations
- `cache_setup.py` - Cache initialization
- `metrics.py` - Metrics display and export

**Supporting Operations** (`scripts/`):
- `health_check.py` - System health diagnostics
- `security_check.py` - Security validation
- `audit.py` - Audit trail viewer
- `model_router.py` - Model routing recommendations
- `cache_stats.py` - Cache statistics
- `cache_clear.py` - Cache clearing

**Specialized Tools** (`scripts/` and `.aget/tools/`):
- `session_protocol.py` - Session lifecycle (wake/wind-down/sign-off)
- `checkpoint.py` - Checkpoint save/load/list
- `task_planner.py` - Task decomposition planning
- `.aget/tools/analyze_agent_fit.py` - Use case fit analysis
- `.aget/tools/instantiate_template.py` - Template instantiation helper

## Testing

Template includes 30 contract tests (100% passing):

```bash
# Run all tests
python3 -m pytest tests/ -v

# Run specific test category
python3 -m pytest tests/test_processing.py -v
```

Test coverage:
- **Smoke tests** (20 tests): All 20 modules tested
- **Integration tests** (10 tests): End-to-end workflows, script integration, contract validation

```bash
# Run smoke tests only
python3 tests/smoke_test.py

# Run integration tests only
python3 tests/test_integration.py
```

## Helper Tools

Two helper tools are provided for template users:

**Analyze Agent Fit**:
```bash
# Check if use case fits this template
python3 .aget/tools/analyze_agent_fit.py "Process legal contracts and extract structured data"

# Interactive mode
python3 .aget/tools/analyze_agent_fit.py --interactive
```

**Instantiate Template**:
```bash
# Create new agent from template
python3 .aget/tools/instantiate_template.py invoice-processor ~/github/invoice-processor-AGET

# Verify instantiation
python3 .aget/tools/instantiate_template.py --check ~/github/invoice-processor-AGET
```

## Version History

**v2.7.0** (2025-10-26)
- Initial template release
- Based on L208 document processing pattern analysis
- **20 source modules** (Gate 2A: 8, Gate 2B: 7, Gate 2C: 5)
- **9 configuration files** (YAML-based)
- **9 operational protocols** (tested and validated)
- **3 formal specifications** (168 EARS requirements)
- **17 operational tools** (15 scripts + 2 helper tools)
- **30 contract tests** (20 smoke + 10 integration, 100% passing)
- Multi-provider LLM support (OpenAI, Anthropic, Google)
- Security protocols (input sanitization, content filtering, resource limits)
- Wikitext support (extensible to other formats)

## Support

For template issues or questions:
- Template repository: https://github.com/aget-framework/template-document-processor-AGET
- AGET framework: https://github.com/aget-framework

## License

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) file for details.

Copyright 2025 AGET Framework Contributors

---

*Generated by AGET v2.7.0*
