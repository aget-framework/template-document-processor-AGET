# Changelog

All notable changes to template-document-processor-AGET will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.8.0] - 2025-11-02

**Note**: This release introduces dual versioning for specialized templates:
- **Template Version**: v2.8.0 (template-specific features, incremental from v2.7.0)
- **AGET Framework**: v2.7.0 (framework compliance)

See version.json for `template_version` and `aget_version` fields.

### Added
- **Format Preservation Framework**: Prevent L245-type catastrophic failures (100% Track Changes loss)
- **OOXML Verification Module** (`.aget/tools/format_verification/`):
  - `verification_framework.py` - Core verification logic with VerificationResult dataclass
  - `docx_verifier.py` - DOCX-specific OOXML inspection (Track Changes, comments)
  - `checkpoint_manager.py` - Multi-stage checkpoint system for pipeline verification
  - `verification_report.py` - Human-readable reporting (4 report types)
  - Complete API with simple and advanced usage patterns
- **Integration Tests** (15 tests with real DOCX files):
  - Programmatic DOCX creation with Track Changes markup
  - End-to-end L245 failure detection validation
  - Test coverage: Overall 53%, docx_verifier.py 68% (exceeds 60% target)
- **Documentation**:
  - `FORMAT_PRESERVING_DECISION_PROTOCOL.md` - 5-question architecture checklist
  - `FORMAT_PRESERVATION_GUIDE.md` - Simple-first implementation guide (59% Quick Start, 41% Advanced)
  - Integration example: `examples/verify_track_changes_example.py`
- **Test Fixtures**: Real DOCX files for integration testing (test_with_track_changes.docx, test_clean.docx)

### Changed
- **Versioning clarification**: Introduced dual versioning for specialized templates
  - `template_version`: 2.8.0 (template-specific features, incremental from v2.7.0)
  - `aget_version`: 2.7.0 (framework compliance)
  - `template_base`: "worker" (base template)
- README updated with format preservation capabilities and versioning clarification
- Protocol count updated (9 → 10 protocols)
- Contract tests updated to validate template versioning fields

### Fixed
- Integration example now uses test fixture paths (copy-paste ready, dogfooding feedback)

### Technical Details
- **Coverage Improvements**: docx_verifier.py 15% → 68% (+53 pts)
- **Test Suite**: 62 total tests (20 smoke + 10 integration + 15 format verification + 17 unit)
- **API Exports**: 18 functions/classes in format_verification module
- **Lines Added**: ~1,700 lines (verification framework + tests + docs)

### Validation
- **Dogfooding**: 3min 18sec pilot agent creation using Quick Start only
- **L245 Detection**: 100% format loss correctly detected with real DOCX files
- **Multi-Stage Verification**: Pattern 1 (verify after each stage) validated

### Impact
- **L245 Prevention**: Template now prevents catastrophic format loss that cost docx-AGET 10 hours
- **Decision Framework**: 5-question checklist helps agents choose text-only vs format-preserving architecture
- **Post-Release Validation**: v3.0.0 + 3 months user feedback will validate Option C (Hybrid) approach

### Related Learnings
- Based on L245_ooxml_round_trip_verification.md from private-docx-AGET

---

## [2.7.0] - 2025-10-26

### Added
- Initial template release
- Based on L208: Document Processing Agent Template Pattern
- Core infrastructure (18 source modules):
  - `src/ingestion/` - Queue management, validation, batch processing
  - `src/processing/` - LLM providers, model routing, caching, schema validation
  - `src/output/` - Publishing, version management, rollback
  - `src/security/` - Input sanitization, content filtering, resource limiting
  - `src/pipeline/` - Task decomposition, orchestration, metrics
  - `src/wikitext/` - Wikitext parsing, MediaWiki integration
- Configuration framework (8 YAML files):
  - Document type configuration
  - External system integration
  - Validation rules
  - LLM provider settings
  - Approval gates
  - Model routing strategy
  - Security policy
  - Caching configuration
  - Metrics collection
  - Orchestration settings
- Operational protocols (9 documented):
  - Queue Management Protocol
  - Processing Authorization Protocol
  - Validation Pipeline Protocol
  - Rollback Protocol
  - Security Validation Protocol
  - Task Decomposition Protocol
  - Model Routing Protocol
  - Caching Implementation Protocol
  - Metrics Collection Protocol
- Scripts and tools (15 operational scripts + 2 helper tools)
- Contract tests (30+ tests)
- Wikitext support for GM-RKB format documents
- Example instantiations (PDF processor, Markdown enhancer)

### Analysis
- Analyzed production document processing agents (pattern analysis per L208)
- Extracted 30+ shared protocol elements
- Identified 5 major pattern categories
- Defined 7 customization points

### Impact
- Time savings: 60-70% reduction in new agent setup (3-5 hours → 1-2 hours)
- Consistency: 100% protocol alignment across fleet
- Quality: Pre-tested validation and security boundaries
- Maintenance: Single template to improve, all agents benefit

---

## Template Versioning

Template versions follow AGET framework versions:
- **2.7.0** - Includes portfolio governance, learning discovery, multi-tier routing
- Future updates will align with AGET framework releases

## Source Documentation

- **Learning Document**: L208_document_processing_template_pattern.md
- **Framework**: AGET v2.7.0
- **Standard**: AGENTS.md open-source configuration standard

[2.7.0]: https://github.com/aget-framework/template-document-processor-AGET/releases/tag/v2.7.0
