# Format Preservation Guide

**Purpose**: Prevent catastrophic format loss (L245-type failures) when processing DOCX files.

**What This Prevents**: 100% Track Changes loss, comment loss, markup stripping that invalidates hours of work.

**Who Needs This**: Agents processing DOCX files that contain Track Changes, comments, or critical formatting.

---

## Quick Start (5 Minutes)

**80% of users stop here.** If you just need to verify Track Changes preservation, this section covers everything.

### Basic Verification

Verify Track Changes preserved between input and output:

```python
from format_verification import verify_track_changes

result = verify_track_changes('input.docx', 'output.docx')

if not result.passed:
    print(f"❌ FAIL: {result.message}")
    print(result.report())

    # Check for L245 catastrophic failure (100% loss)
    if result.details.get('loss_rate') == '100%':
        raise ValueError("STOP: L245 catastrophic failure detected")
else:
    print(f"✅ PASS: {result.message}")
```

**That's it.** This catches L245-type failures (100% format loss) that cost docx-AGET 10 hours of wasted work.

### Integration Example

See `examples/verify_track_changes_example.py` for a complete working example:

```python
#!/usr/bin/env python3
"""Minimal Integration Example: Track Changes Verification"""

import sys
from pathlib import Path

# Add .aget/tools to path
sys.path.insert(0, str(Path(__file__).parent.parent / '.aget' / 'tools'))

from format_verification import verify_track_changes

def main():
    """Simple Track Changes verification example."""

    input_path = "input.docx"
    output_path = "output.docx"

    print(f"Verifying: {input_path} → {output_path}")

    result = verify_track_changes(input_path, output_path)

    if result.passed:
        print(f"✅ PASS: {result.message}")
    else:
        print(f"❌ FAIL: {result.message}")
        print("\nDetailed Report:")
        print(result.report())

        # Check for L245 catastrophic failure
        if result.details and result.details.get('loss_rate') == '100%':
            print("\n🚨 L245 CATASTROPHIC FAILURE DETECTED")
            print("STOP processing immediately and review architecture!")
            return 1

    return 0 if result.passed else 1

if __name__ == "__main__":
    sys.exit(main())
```

**Usage**:
```bash
python3 examples/verify_track_changes_example.py
```

### Common Patterns

#### Pattern 1: Verify After Each Processing Stage

```python
from format_verification import verify_track_changes

# After translation
result = verify_track_changes('input.docx', 'translated.docx')
if not result.passed:
    raise ValueError(f"Translation lost format: {result.message}")

# After enrichment
result = verify_track_changes('translated.docx', 'enriched.docx')
if not result.passed:
    raise ValueError(f"Enrichment lost format: {result.message}")
```

#### Pattern 2: Verify Multiple Formats

```python
from format_verification import verify_round_trip

# Verify both Track Changes and Comments
results = verify_round_trip('input.docx', 'output.docx')

failed = [r for r in results if not r.passed]
if failed:
    for result in failed:
        print(f"❌ {result.format_type.value}: {result.message}")
    raise ValueError(f"{len(failed)} format checks failed")
```

#### Pattern 3: Quick Format Check (Boolean Only)

```python
from format_verification import has_track_changes

# Quick check without details
if not has_track_changes('output.docx'):
    raise ValueError("Track Changes lost (L245 failure)")
```

### When to Use

**Use format verification when**:
- Processing DOCX files with Track Changes, comments, or annotations
- Round-trip requirements (read → modify → write)
- Format loss would invalidate user work
- You need to prevent L245-type catastrophic failures

**Skip format verification when**:
- Plain text extraction (no format preservation needed)
- One-way processing (no round-trip)
- Format loss is acceptable

**Decision Framework**: See `.aget/docs/protocols/FORMAT_PRESERVING_DECISION_PROTOCOL.md` for 5-question checklist to determine if you need format preservation.

---

## Advanced Patterns (Optional - Most Users Skip)

⚠️ **Most users won't need these advanced features.** The Quick Start section covers 80% of use cases.

If you have multi-stage pipelines or need detailed evidence tracking, these patterns may help.

### Multi-Stage Verification (Checkpoint System)

For complex pipelines with multiple processing stages, you can create checkpoints to detect exactly where format loss occurs:

```python
from format_verification import CheckpointManager

manager = CheckpointManager()

# Stage 1: Input
manager.add_checkpoint('input.docx', 'pre_modification')

# Stage 2: After modification
manager.add_checkpoint('modified.docx', 'post_modification')

# Stage 3: After translation
manager.add_checkpoint('translated.docx', 'post_translation')

# Verify all stages
all_results = manager.verify_all_checkpoints()

for transition, results in all_results.items():
    failed = [r for r in results if not r.passed]
    if failed:
        print(f"❌ Format loss in {transition}")
        for r in failed:
            print(f"   {r.format_type.value}: {r.message}")
```

**When to use**: Pipelines with 3+ stages where you need to pinpoint which stage loses format.

### Custom Reporting

For detailed evidence presentation (debugging, auditing):

```python
from format_verification import (
    verify_round_trip,
    format_verification_report
)

# Verify multiple formats
results = verify_round_trip('input.docx', 'output.docx')

# Generate detailed report
report = format_verification_report(results)
print(report)
```

**Output example**:
```
======================================================================
FORMAT VERIFICATION REPORT
======================================================================

Summary: 2/2 checks passed
✅ All checks PASSED

----------------------------------------------------------------------
Individual Results:
----------------------------------------------------------------------

1. ✅ TRACK_CHANGES
   Status: PASS
   Message: Track Changes preserved (10 items)
   Details:
     count: 10

2. ✅ COMMENTS
   Status: PASS
   Message: Comments preserved (3 items)
   Details:
     count: 3

======================================================================
```

**When to use**: Audit trails, debugging format loss, evidence for validation reports.

### API Reference (Quick)

**Core Functions** (most common):
- `verify_track_changes(before, after)` → VerificationResult
- `verify_comments(before, after)` → VerificationResult
- `verify_round_trip(before, after)` → List[VerificationResult]
- `has_track_changes(docx_path)` → bool
- `has_comments(docx_path)` → bool

**Advanced Functions** (multi-stage pipelines):
- `create_checkpoint(doc_path, name)` → Checkpoint
- `compare_checkpoints(current_path, previous_checkpoint)` → List[VerificationResult]
- `CheckpointManager()` → Multi-stage verification manager

**Reporting Functions** (detailed output):
- `format_verification_report(results)` → str
- `format_checkpoint_report(checkpoint)` → str

**For complete API**: See `.aget/tools/format_verification/__init__.py` docstrings.

---

## Implementation Guide

### Adding Format Preservation to Your Agent

**Step 1**: Determine if you need format preservation

See `.aget/docs/protocols/FORMAT_PRESERVING_DECISION_PROTOCOL.md` and answer these 5 questions:

1. Does the document contain tracked changes, comments, or annotations?
2. Does the document contain complex formatting critical to meaning?
3. Is there a round-trip requirement (read → modify → write)?
4. Is format loss visible to end users?
5. Does format loss constitute data loss?

**Scoring**:
- 0-1 YES → Text-only processing (no verification needed)
- 2-3 YES → Selective verification (verify critical formats only)
- 4-5 YES → Full verification (verify all formats)

**Step 2**: Add verification to your processing pipeline

```python
# Before processing
from format_verification import verify_track_changes

# After each stage that modifies DOCX
result = verify_track_changes('input.docx', 'output.docx')
if not result.passed:
    logger.error(result.report())
    raise ValueError(f"Format lost: {result.message}")
```

**Step 3**: Configure error handling

```python
# Strict mode (fail on any loss)
if not result.passed:
    raise ValueError("Format verification failed")

# Permissive mode (warn on partial loss, fail on 100% loss)
if not result.passed:
    if result.details.get('loss_rate') == '100%':
        raise ValueError("L245 catastrophic failure")
    else:
        logger.warning(f"Partial format loss: {result.message}")
```

### Testing Your Integration

**Minimal test**:
```python
def test_format_preservation():
    """Verify Track Changes preserved through processing."""
    from format_verification import verify_track_changes

    # Process document
    process_document('test_input.docx', 'test_output.docx')

    # Verify
    result = verify_track_changes('test_input.docx', 'test_output.docx')
    assert result.passed, f"Format lost: {result.message}"
```

**What to test**:
1. ✅ Documents with Track Changes preserved
2. ✅ Documents with comments preserved
3. ✅ L245 failure detection (100% loss)
4. ❌ Don't test partial loss (edge case, framework handles)
5. ❌ Don't test all 4 report types (over-testing)

---

## Troubleshooting

### "Track Changes lost (L245 failure)"

**Cause**: Processing stripped OOXML markup (common with `.text` extraction or text-only operations).

**Fix**:
1. Check if you're using `.text` extraction (strips markup)
2. Switch to OOXML-preserving operations (e.g., python-docx element manipulation)
3. See FORMAT_PRESERVING_DECISION_PROTOCOL.md Anti-Patterns section

### "document.xml not found"

**Cause**: File is not a valid DOCX (corrupted or wrong format).

**Fix**:
1. Verify file is .docx (not .doc, .txt, .pdf)
2. Try opening in Microsoft Word to verify integrity
3. Check file size > 0 bytes

### "Partial format loss (50%)"

**Cause**: Some Track Changes preserved but not all (not L245, but still data loss).

**Action**:
1. Review result.details for before/after counts
2. Check which processing stage caused loss
3. If acceptable: Continue with warning
4. If unacceptable: Review processing logic for partial stripping

### "ImportError: No module named 'format_verification'"

**Cause**: Module not in Python path.

**Fix**:
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / '.aget' / 'tools'))
```

Or install as package (if distributed separately).

---

## Background: The L245 Failure

**What happened**: docx-AGET lost 100% of Track Changes across 8/8 back-translation files, invalidating 10 hours of work. User discovered the failure, not the agent.

**Root cause**: `.text` extraction stripped OOXML markup silently. No verification checkpoint caught the loss.

**Prevention**: This verification framework catches L245-type failures before they invalidate user work.

**Learn more**: See `private-docx-AGET/.aget/evolution/L245_ooxml_round_trip_verification.md` for full analysis and anti-patterns.

---

## Related Documentation

- **Decision Protocol**: `.aget/docs/protocols/FORMAT_PRESERVING_DECISION_PROTOCOL.md` - 5-question checklist to determine if you need format preservation
- **API Reference**: `.aget/tools/format_verification/__init__.py` - Complete API docstrings
- **Test Suite**: `tests/unit/tools/format_verification/` - Test examples and patterns
- **Integration Example**: `examples/verify_track_changes_example.py` - Complete working example

---

**Version**: 1.0.0 (template-document-processor-AGET v3.0.0)
