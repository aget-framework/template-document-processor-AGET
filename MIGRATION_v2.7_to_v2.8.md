# Migration Guide: v2.7.0 → v2.8.0

**Purpose**: Guide for upgrading agents from template v2.7.0 to v2.8.0.

**Breaking Changes**: None. v2.8.0 is backward compatible with v2.7.0.

**New Capabilities**: Format preservation framework (optional adoption).

---

## Summary of Changes

**v2.8.0 adds format preservation capabilities** to prevent L245-type catastrophic failures (100% Track Changes loss).

- **New module**: `.aget/tools/format_verification/`
- **New documentation**: `FORMAT_PRESERVING_DECISION_PROTOCOL.md`, `FORMAT_PRESERVATION_GUIDE.md`
- **New protocol**: Format Preservation Protocol (10th protocol)
- **Integration example**: `examples/verify_track_changes_example.py`
- **Test fixtures**: Real DOCX files for validation

**Impact**: Agents processing DOCX files with Track Changes/comments can now verify format preservation.

---

## Who Should Upgrade?

**Upgrade if**:
- Your agent processes DOCX files with Track Changes, comments, or annotations
- You have round-trip requirements (read → modify → write)
- Format loss would invalidate user work
- You want to prevent L245-type failures

**Skip upgrade if**:
- Plain text extraction only (no format preservation needed)
- One-way processing (no round-trip)
- Format loss is acceptable for your use case

**Decision Framework**: Use 5-question checklist in `FORMAT_PRESERVING_DECISION_PROTOCOL.md`.

---

## Migration Steps

### Step 1: Update Template Reference

If you created your agent from v2.7.0 template, note the new version:

```bash
# Check current template version
jq -r '.aget_version' .aget/version.json
# Output: 2.7.0 (if from old template)

# After upgrading (manual update or re-instantiate):
jq -r '.aget_version' .aget/version.json
# Output: 3.0.0
```

**Note**: No action required unless you want to adopt format preservation.

### Step 2: Copy Format Verification Module (Optional)

If you want format preservation capabilities:

```bash
# From updated template
cp -r ~/github/template-document-processor-AGET/.aget/tools/format_verification \
      .aget/tools/

# Verify installation
python3 -c "import sys; sys.path.insert(0, '.aget/tools'); from format_verification import verify_track_changes; print('✅ Installed')"
```

### Step 3: Add Integration (Optional)

**Minimal integration** (Pattern 1: Verify after each processing stage):

```python
# In your document processing pipeline
from format_verification import verify_track_changes

# After processing step
result = verify_track_changes('input.docx', 'output.docx')
if not result.passed:
    logger.error(f"Format lost: {result.message}")
    if result.details.get('loss_rate') == '100%':
        raise ValueError("L245 catastrophic failure - STOP processing")
```

**See**: `FORMAT_PRESERVATION_GUIDE.md` for complete integration patterns.

### Step 4: Update Tests (Optional)

If you adopt format preservation, add verification tests:

```python
def test_format_preservation():
    """Verify Track Changes preserved through processing."""
    from format_verification import verify_track_changes

    process_document('test_input.docx', 'test_output.docx')

    result = verify_track_changes('test_input.docx', 'test_output.docx')
    assert result.passed, f"Format lost: {result.message}"
```

### Step 5: Update Documentation (Optional)

If you adopt format preservation, update your agent's AGENTS.md:

```markdown
## Format Preservation

This agent preserves DOCX formatting (Track Changes, comments, annotations) during processing.

**Verification**: Uses format_verification module to detect format loss.

**L245 Prevention**: 100% Track Changes loss triggers pipeline stop.
```

---

## Backward Compatibility

**v2.8.0 is fully backward compatible with v2.7.0**:
- No breaking changes to existing modules
- Format verification is opt-in (not mandatory)
- All v2.7.0 features work unchanged
- Contract tests updated to accept both v2.x and v2.8.x

**Migration is zero-risk for agents that don't need format preservation.**

---

## New Features (Optional Adoption)

### Format Verification API

**Simple API** (most common):
```python
from format_verification import verify_track_changes

result = verify_track_changes('before.docx', 'after.docx')
if not result.passed:
    print(f"❌ FAIL: {result.message}")
```

**Advanced API** (multi-stage pipelines):
```python
from format_verification import CheckpointManager

manager = CheckpointManager()
manager.add_checkpoint('input.docx', 'pre_processing')
# ... process ...
manager.add_checkpoint('output.docx', 'post_processing')

all_results = manager.verify_all_checkpoints()
# Pinpoints which stage lost format
```

**See**: `FORMAT_PRESERVATION_GUIDE.md` for complete API reference.

### Decision Protocol

**5-question checklist** to determine if you need format preservation:

1. Does the document contain tracked changes, comments, or annotations?
2. Does the document contain complex formatting critical to meaning?
3. Is there a round-trip requirement (read → modify → write)?
4. Is format loss visible to end users?
5. Does format loss constitute data loss?

**Scoring**: 0-1 YES → Text-only, 2-3 YES → Selective preservation, 4-5 YES → Full preservation

**See**: `FORMAT_PRESERVING_DECISION_PROTOCOL.md` for complete checklist.

---

## Testing Your Migration

### Verify Format Verification Installation

```bash
# Test import
python3 -c "
import sys
from pathlib import Path
sys.path.insert(0, str(Path('.') / '.aget' / 'tools'))

from format_verification import verify_track_changes
print('✅ Format verification installed')
"
```

### Run Example

```bash
# Run integration example
python3 examples/verify_track_changes_example.py

# Expected output:
# ✅ PASS: track_changes preserved (5 items)
```

### Run Tests

```bash
# If you copied integration tests
python3 -m pytest tests/integration/test_docx_verification.py -v

# Expected: 15 tests pass
```

---

## Rollback (If Needed)

If you encounter issues after upgrading:

```bash
# Remove format verification module
rm -rf .aget/tools/format_verification

# Remove integration tests (if added)
rm -f tests/integration/test_docx_verification.py

# Revert to v2.7.0 behavior (no format verification)
```

**Note**: Since format verification is opt-in, simply not using it achieves the same rollback effect.

---

## Support

**Questions or issues**:
- Template repository: https://github.com/aget-framework/template-document-processor-AGET
- AGET framework: https://github.com/aget-framework
- Create issue: Label with `migration` or `v2.8.0`

**Post-upgrade validation**: After 3 months of v2.8.0 usage, template maintainers will collect feedback on format preservation adoption and usability.

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for complete v2.8.0 changes.

---

*Migration guide for template-document-processor-AGET v2.8.0 (2025-11-02)*
