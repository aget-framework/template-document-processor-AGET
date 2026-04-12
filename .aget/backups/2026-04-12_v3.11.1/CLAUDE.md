# Agent Configuration

@aget-version: 2.7.0

## Agent Compatibility
This configuration follows the AGENTS.md open-source standard for universal agent configuration.
Works with Claude Code, Cursor, Aider, Windsurf, and other CLI coding agents.
**Note**: CLAUDE.md is a symlink to this file for backward compatibility.

## Template Identity

**Name**: template-document-processor-AGET
**Type**: Template (for creating document processing agents)
**Version**: 2.7.0
**Instance Type**: AGET (action-taking)
**Domain**: document-processing

## Purpose

This template provides a production-ready foundation for creating document processing agents that:
- Process documents using LLM assistance (OpenAI, Anthropic, Google)
- Support batch operations with validation pipelines
- Implement security protocols (prompt injection prevention, content filtering)
- Provide caching, metrics, and observability
- Enable task decomposition for large documents
- Support rollback and version management

## Based on Learning

This template is based on **L208: Document Processing Agent Template Pattern**, which analyzed production document processing agents to extract common patterns and best practices.

Pattern extraction identified:
- 5 major shared pattern categories
- 30+ shared protocol elements
- 60-70% time reduction potential for new agent creation

## Architecture Overview

### Core Components

**1. LLM-Powered Processing Pipeline** (`src/processing/`)
- Multi-provider abstraction (OpenAI, Anthropic, Google)
- Model routing (static/dynamic/ensemble strategies)
- Response caching with idempotence
- Retry logic with exponential backoff
- Schema validation

**2. Batch Processing Infrastructure** (`src/ingestion/`)
- Queue management (candidates, pending, processed)
- Input validation (format, size, structure)
- Batch coordinator with progress tracking

**3. Output Management** (`src/output/`)
- Version tracking and snapshots
- Rollback capabilities
- Publishing pipeline

**4. Security Protocols** (`src/security/`)
- Input sanitization (prompt injection prevention)
- Content filtering (input and output)
- Resource limiting (tokens, time, cost)

**5. Orchestration** (`src/pipeline/`)
- Task decomposition (parent/child hierarchies)
- Sequential/parallel/mixed execution patterns
- Status tracking and progress monitoring
- Metrics collection (accuracy, latency, cost)

**6. Domain-Specific Support** (`src/wikitext/`)
- Wikitext parsing (GM-RKB format)
- MediaWiki API integration
- Extensible for other document formats (PDF, DOCX, etc.)

## Customization Points

When creating a new agent from this template, customize:

1. **Document Type** (`config/document_type.yaml`)
   - File extensions supported
   - Size limits
   - Format-specific validation rules

2. **External System** (`config/external_system.yaml`)
   - API endpoints (MediaWiki, GitHub, S3, filesystem, etc.)
   - Authentication methods
   - Integration patterns

3. **Validation Rules** (`config/validation_rules.yaml`)
   - Pre-processing checks
   - Post-processing validation
   - Schema compliance requirements

4. **LLM Providers** (`config/llm_providers.yaml`)
   - API configurations
   - Model selection strategy
   - Fallback chain
   - Budget constraints

5. **Approval Gates** (`config/approval_gates.yaml`)
   - Authorization mode (file-by-file, batch, automatic)
   - Timeout settings
   - Failure handling

6. **Model Routing** (`config/model_routing.yaml`)
   - Complexity thresholds
   - Cost optimization rules
   - Quality requirements

7. **Metrics Collection** (`config/metrics.yaml`)
   - Accuracy tracking
   - Latency monitoring
   - Cost tracking
   - Alert thresholds

## Directory Structure

```
template-document-processor-AGET/
├── .aget/
│   ├── version.json                    # Template identity
│   ├── evolution/                      # Learning documents (empty in template)
│   ├── docs/
│   │   ├── protocols/                  # 9 operational protocols
│   │   └── specifications/             # 3 YAML specs
│   └── tools/                          # Helper tools (analyze, instantiate)
│
├── src/
│   ├── ingestion/                      # Input handling (3 modules)
│   ├── processing/                     # LLM processing (5 modules)
│   ├── output/                         # Output management (3 modules)
│   ├── pipeline/                       # Orchestration (4 modules)
│   ├── security/                       # Security protocols (3 modules)
│   └── wikitext/                       # Domain-specific (2 modules)
│
├── config/                             # 8 configuration YAMLs
├── scripts/                            # 15 operational scripts
├── tests/                              # 30+ contract tests
├── examples/                           # Instantiation examples
│
├── AGENTS.md                           # This file
├── CLAUDE.md -> AGENTS.md              # Symlink for compatibility
├── README.md                           # Template documentation
└── CHANGELOG.md                        # Version history
```

## Quick Start

### Creating a New Agent from Template

```bash
# Clone template
gh repo clone aget-framework/template-document-processor-AGET my-new-doc-agent
cd my-new-doc-agent

# Customize configuration
# 1. Update .aget/version.json (agent_name, domain)
# 2. Configure config/*.yaml files
# 3. Update AGENTS.md mission statement
# 4. Implement domain-specific modules if needed

# Run contract tests
python3 -m pytest tests/ -v

# Deploy
git remote set-url origin <your-repo-url>
git push -u origin main
```

See `README.md` for detailed customization guide.

## Protocols

This template includes 9 operational protocols:

1. **Queue Management Protocol** - Queue status, candidate management
2. **Processing Authorization Protocol** - Approval gates, STOP protocol
3. **Validation Pipeline Protocol** - Pre/post validation, dry-run
4. **Rollback Protocol** - Version management, recovery
5. **Security Validation Protocol** - Input sanitization, content filtering
6. **Task Decomposition Protocol** - Parent/child hierarchies, chunking
7. **Model Routing Protocol** - Static/dynamic/ensemble routing
8. **Caching Implementation Protocol** - Response caching, checkpoint management
9. **Metrics Collection Protocol** - Accuracy/latency/cost tracking

All protocols documented in `.aget/docs/protocols/` with bash commands.

## Session Management

Standard AGET session protocols:

### Wake Up
```bash
# Template agents use standard wake up
# Displays: agent identity, configuration status, available capabilities
```

### Wind Down
```bash
# Standard wind down protocol
# Creates session notes, commits changes
```

### Sign Off
```bash
# Quick save and exit
```

## Testing

Template includes 30+ contract tests:
- Identity validation (version.json)
- Structure validation (directories)
- Configuration validation (8 YAMLs)
- Protocol documentation validation (9 protocols)
- Module tests (18 src/ modules)
- Script tests (15 scripts)
- Integration tests (end-to-end workflows)

Run tests: `python3 -m pytest tests/ -v`

## Version History

See `CHANGELOG.md` for complete version history.

**v2.7.0** (2025-10-26) - Initial template release
- Based on L208 document processing pattern
- 18 source modules
- 8 configuration files
- 9 operational protocols
- 30+ contract tests
- Wikitext support included

---

*Generated by AGET v2.7.0 - https://github.com/aget-framework*
