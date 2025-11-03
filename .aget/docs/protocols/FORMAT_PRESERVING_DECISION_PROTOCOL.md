# Format-Preserving Decision Protocol
## Architecture Decision Framework for Document Processing

**Version**: 1.0.0
**Created**: 2025-11-03
**Template Version**: v3.0.0
**Purpose**: Guide document processing agents in choosing appropriate format preservation strategy

---

## Overview

When processing structured documents (DOCX, PDF, HTML, etc.), agents face a critical architecture decision: **text-only extraction** vs **format-preserving processing** vs **hybrid approach**.

**Wrong choice costs**: 10+ hours rework, 100% failure rates, user-discovered defects (see L245 catastrophic failure)

**This protocol provides**:
1. **5-Question Requirement Checklist** - Determine format preservation need
2. **3 Architecture Patterns** - Choose appropriate processing strategy
3. **Decision Matrix** - Map requirements to architecture
4. **Anti-Patterns** - Learn from L245 failure mode (100% Track Changes loss)

---

## The Critical Question

**"Does format preservation failure = data loss or mission failure?"**

- **If YES**: Use format-preserving or hybrid architecture
- **If NO**: Text-only extraction is simpler and faster
- **If UNCERTAIN**: Answer 5-question checklist below

---

## 5-Question Requirement Checklist

Answer these questions to determine your format preservation requirements:

### Question 1: Does the document contain tracked changes, comments, or annotations?

**Examples**:
- DOCX files with Track Changes (`<w:ins>`, `<w:del>`)
- PDF files with review comments
- HTML files with `<ins>` and `<del>` tags
- Collaborative editing markup

**If YES → High format preservation need**

**Why it matters**: Track Changes are OOXML structures that `.text` extraction strips silently. Losing them = losing edit history, authorship, review context.

**L245 Failure Example**: 8/8 back-translations lost Track Changes (100% failure rate) because `.text` extraction used instead of OOXML-preserving processing. 10 hours of work invalidated.

---

### Question 2: Does the document contain complex formatting critical to meaning?

**Examples**:
- Tables with structured data (financial reports, specifications)
- Lists with hierarchical numbering (legal documents, technical specs)
- Styled text conveying semantic meaning (bold = emphasis, strikethrough = deleted)
- Images with captions or embedded metadata

**If YES → Medium-High format preservation need**

**Why it matters**: Formatting can convey semantic information. Plain text extraction loses structure (table cells → linear text), hierarchy (nested lists → flat text), emphasis (bold → undecorated text).

**Example**: Contract with table of payment milestones → Text extraction destroys table structure → Dates/amounts no longer aligned → Semantic loss.

---

### Question 3: Is there a round-trip requirement (read → modify → write)?

**Examples**:
- Translation workflow: original.docx → translated.docx (must preserve formatting)
- Review workflow: draft.docx → reviewed.docx (must preserve Track Changes)
- Enrichment workflow: stub.html → enhanced.html (must preserve structure)

**If YES → High format preservation need**

**Why it matters**: Round-trip workflows require writing back to original format. Text-only extraction is one-way (read-only). Writing requires format preservation.

**Example**: Translate DOCX while preserving corporate template styles, headers, footers → Requires OOXML manipulation, not text extraction.

---

### Question 4: Is format loss visible to end users?

**Examples**:
- Output viewed in Microsoft Word/Google Docs (formatting expected)
- Output published to web (HTML structure expected)
- Output printed (page layout, headers, footers expected)
- Output compared to original (visual fidelity expected)

**If YES → Medium format preservation need**

**Why it matters**: Users expect format fidelity. Text-only extraction produces plain text output that looks nothing like original. Visual quality = user satisfaction.

**Example**: Generate report from DOCX template → Users expect company logo, headers, page numbers → Text extraction loses all visual elements.

---

### Question 5: Does format loss constitute data loss?

**Examples**:
- Track Changes = edit history (data loss if lost)
- Table structure = relationships between values (data loss if flattened)
- Hyperlinks = navigation/references (data loss if stripped)
- Comments/annotations = review context (data loss if removed)

**If YES → Critical format preservation need**

**Why it matters**: This is the "mission failure" question. If format elements carry information, losing them = losing data, not just aesthetics.

**L245 Failure Example**: Back-translation requirement was "preserve Track Changes" → 0/8 preserved → **Mission failure** (not just cosmetic). User rejected deliverable.

---

## Requirement Scoring

Sum your YES answers:

| Score | Interpretation | Recommendation |
|-------|----------------|----------------|
| **0-1 YES** | Low format preservation need | **Pattern A: Text-Only Extraction** |
| **2-3 YES** | Medium format preservation need | **Pattern C: Hybrid Approach** |
| **4-5 YES** | High format preservation need | **Pattern B: Format-Preserving** |

**Special Case**: If Question 5 (data loss) = YES → Always use Pattern B or C, regardless of other scores.

---

## Architecture Pattern Catalog

### Pattern A: Text-Only Extraction

**When to use**:
- ✅ Simple content extraction
- ✅ No round-trip requirement
- ✅ Format is cosmetic only (not semantic)
- ✅ Output is plain text or markdown
- ✅ Speed and simplicity prioritized

**Architecture**:
```python
from docx import Document

# Read
doc = Document('input.docx')
text = '\n'.join([para.text for para in doc.paragraphs])

# Process
processed_text = process(text)  # Translation, summarization, etc.

# Write (plain text only)
with open('output.txt', 'w') as f:
    f.write(processed_text)
```

**Pros**:
- ✅ Simple implementation (few lines of code)
- ✅ Fast execution (no OOXML parsing overhead)
- ✅ Universal (works for any document format)
- ✅ No format-specific dependencies

**Cons**:
- ❌ Loses ALL formatting (bold, italics, colors)
- ❌ Loses structure (tables, lists, headings)
- ❌ Loses metadata (Track Changes, comments, hyperlinks)
- ❌ One-way only (can't write back to DOCX)

**Risk**: Silent data loss if requirements change (e.g., "actually we need Track Changes")

**Example Use Cases**:
- Extract text for keyword search
- Generate plain text summary
- Convert DOCX → Markdown
- Simple translation (no formatting needed)

---

### Pattern B: Format-Preserving Processing

**When to use**:
- ✅ Track Changes, comments, or annotations critical
- ✅ Round-trip requirement (must write back to original format)
- ✅ Format loss = data loss or mission failure
- ✅ Complex formatting must be preserved
- ✅ Visual fidelity required

**Architecture**:
```python
from docx import Document
from docx.oxml import OxmlElement

# Read with format preservation
doc = Document('input.docx')

# Process while preserving OOXML structure
for para in doc.paragraphs:
    # Access runs (formatted text fragments)
    for run in para.runs:
        if run.bold:  # Format-aware processing
            run.text = process(run.text)

        # Track Changes preserved automatically (OOXML untouched)

# Write with format preservation
doc.save('output.docx')
```

**Pros**:
- ✅ Preserves ALL formatting (styles, colors, fonts)
- ✅ Preserves structure (tables, lists, headings)
- ✅ Preserves metadata (Track Changes, comments)
- ✅ Round-trip capable (read → modify → write)

**Cons**:
- ❌ Complex implementation (OOXML manipulation)
- ❌ Slower execution (parsing overhead)
- ❌ Format-specific (separate implementation per format)
- ❌ Fragile (OOXML structure easily corrupted)

**Risk**: Complexity overhead if format preservation not actually needed

**Example Use Cases**:
- Translate DOCX while preserving Track Changes (L245 requirement)
- Enrich document while preserving corporate template
- Review workflow with comment preservation
- Legal document processing (formatting = semantic)

---

### Pattern C: Hybrid Approach (Recommended for Most Cases)

**When to use**:
- ✅ Need SOME format preservation (not all)
- ✅ Want simplicity of text extraction with selective preservation
- ✅ Medium format preservation requirements (2-3 YES in checklist)
- ✅ Balance between simplicity and fidelity

**Architecture**:
```python
from docx import Document
import json

# Step 1: Extract text + minimal format metadata
doc = Document('input.docx')
content = []
for para in doc.paragraphs:
    content.append({
        'text': para.text,
        'style': para.style.name,  # Preserve heading levels
        'bold': any(run.bold for run in para.runs)  # Preserve emphasis
    })

# Step 2: Process text (simple)
for item in content:
    item['text'] = process(item['text'])

# Step 3: Reconstruct with preserved formats
output_doc = Document()
for item in content:
    para = output_doc.add_paragraph(item['text'])
    para.style = item['style']
    if item['bold']:
        for run in para.runs:
            run.bold = True

output_doc.save('output.docx')
```

**Pros**:
- ✅ Simpler than full format preservation
- ✅ More flexible than text-only
- ✅ Preserves critical formats (selectively)
- ✅ Round-trip capable (limited)

**Cons**:
- ❌ Custom logic per format type
- ❌ Incomplete preservation (only selected elements)
- ❌ May not preserve Track Changes (unless explicitly handled)

**Risk**: May still lose critical formats if not explicitly preserved

**Example Use Cases**:
- Translation with heading preservation (not full formatting)
- Enrichment with style preservation (not Track Changes)
- Conversion with structure preservation (tables as tables, not text)

---

## Decision Matrix

**Map your requirements to architecture pattern:**

| Requirement | Pattern A (Text-Only) | Pattern B (Format-Preserving) | Pattern C (Hybrid) |
|-------------|----------------------|------------------------------|-------------------|
| **Track Changes critical** | ❌ | ✅ | ⚠️ (with explicit logic) |
| **Complex formatting** | ❌ | ✅ | ✅ |
| **Round-trip needed** | ❌ | ✅ | ⚠️ (limited) |
| **Format visible to users** | ❌ | ✅ | ✅ |
| **Format loss = data loss** | ❌ | ✅ | ⚠️ (depends) |
| **Simple extraction** | ✅ | ❌ | ⚠️ |
| **Speed critical** | ✅ | ❌ | ⚠️ |

**Legend**: ✅ Well-suited | ⚠️ Conditional | ❌ Not suitable

---

## Implementation Guidance

### Step 1: Answer 5-Question Checklist

Write down your answers to Questions 1-5. Be honest about requirements.

### Step 2: Score Requirements

Count YES answers. Determine if high (4-5), medium (2-3), or low (0-1) format preservation need.

### Step 3: Choose Pattern

- **0-1 YES**: Pattern A (Text-Only)
- **2-3 YES**: Pattern C (Hybrid)
- **4-5 YES** OR Question 5 YES: Pattern B (Format-Preserving)

### Step 4: Validate Architecture Choice (CRITICAL)

**Before implementing full pipeline**, create a round-trip test:

```python
def test_architecture_choice():
    """
    Validate chosen architecture preserves critical formats.
    Run BEFORE implementing full pipeline.
    """
    # Step 1: Create test document with critical formats
    test_doc = create_test_document_with_formats()

    # Step 2: Process using chosen architecture
    output = process_with_chosen_architecture(test_doc)

    # Step 3: Verify critical formats preserved
    assert verify_formats_preserved(output), "FAIL: Critical formats lost"

    print("✓ Architecture choice validated - safe to implement")
```

**Why this matters**: L245 failure could have been prevented with 5-minute round-trip test before 10-hour implementation.

### Step 5: Add Verification Checkpoints

**For every processing stage**, add explicit format verification:

```python
# After Stage 1: Translation
verify_track_changes_present('translated.docx')

# After Stage 2: Enrichment
verify_track_changes_present('enriched.docx')

# After Stage 3: Back-translation
verify_track_changes_present('back_translated.docx')  # ← L245 missed this
```

---

## Anti-Patterns (L245 Failure Mode)

### ❌ Anti-Pattern 1: "Assumed Preservation"

**Problem**: Assuming document processing preserves formats without verification

**L245 Example**:
```python
# WRONG: Assumes .text preserves Track Changes
doc = Document('edited.docx')
text = doc.paragraphs[0].text  # Strips ALL OOXML markup!
translated = translate(text)
# Track Changes lost forever (100% failure rate)
```

**Why it fails**: `.text` property returns resolved text, not OOXML structure

**Fix**: Use format-preserving architecture OR explicitly verify format preservation

---

### ❌ Anti-Pattern 2: "Partial Verification"

**Problem**: Verifying only one stage, assuming others inherit correctness

**L245 Example**:
```python
# WRONG: Only check input
assert has_track_changes('input.docx')  # ✓ Pass

# Assume output also has Track Changes
# (Actual: output has NO Track Changes)
```

**Why it fails**: Each processing stage can lose formats independently

**Fix**: Verify EVERY stage that should preserve formats

**L245 Impact**: 6 checkpoints passed without catching 100% Track Changes loss. User discovered failure, not worker/supervisor.

---

### ❌ Anti-Pattern 3: "Proxy Metric Validation"

**Problem**: Using indirect metrics instead of direct format verification

**L245 Example**:
```python
# WRONG: Check text similarity, not format presence
similarity_score = calculate_similarity(output, expected)
assert similarity_score > 7.0  # Passes even without Track Changes!
```

**Why it fails**: Text similarity doesn't verify format structure

**Fix**: Add explicit format checks alongside semantic checks

---

### ❌ Anti-Pattern 4: "Ambiguous Requirements"

**Problem**: Using vague terms that have multiple interpretations

**L245 Example**:
```
Requirement: "Preserve edits through back-translation"

Interpretation A: Semantic preservation (edit meaning reflected)
Interpretation B: OOXML preservation (Track Changes markup present)
Interpretation C: Visual preservation (edits visible in Word)

(Worker implements A, user expects B+C)
```

**Why it fails**: Ambiguity allows divergent interpretations

**Fix**: Explicit requirements with test criteria

**Better requirement**: "Back-translation must preserve Track Changes OOXML markup (`<w:ins>`, `<w:del>`) so edits remain visible when opening output.docx in Microsoft Word"

---

### ❌ Anti-Pattern 5: "No Round-Trip Test Before Implementation"

**Problem**: Implementing full pipeline without validating architecture choice first

**L245 Example**:
- 10 hours implementing text-based translation pipeline
- 8/8 test cases created and executed
- Grade B+ approval given
- **User discovers**: 0/8 back-translations have Track Changes
- **Root cause**: Architecture choice (text extraction) incompatible with requirement (Track Changes preservation)
- **Could have been caught**: 5-minute round-trip test before 10-hour implementation

**Why it fails**: Architecture validation deferred until after significant investment

**Fix**: Create minimal round-trip test (5-10 minutes) BEFORE implementing full pipeline (hours)

---

## Integration with Template

### Configuration File: `config/format_preservation.yaml`

```yaml
format_preservation:
  # Architecture choice: text_only | format_preserving | hybrid
  mode: format_preserving

  # Critical formats to preserve (for hybrid mode)
  preserve:
    - track_changes
    - comments
    - headings
    - tables

  # Verification checkpoints (after which stages to verify)
  verify_after:
    - translation
    - enrichment
    - back_translation

  # Failure handling: strict (abort) | permissive (warn) | audit (log only)
  on_format_loss: strict
```

### Usage in Agent Code

```python
from config import load_config

config = load_config()

if config['format_preservation']['mode'] == 'format_preserving':
    # Use Pattern B
    from pipelines.format_preserving import process_document
else:
    # Use Pattern A
    from pipelines.text_only import process_document

# Process
output = process_document(input_path)

# Verify (if checkpoints configured)
if 'translation' in config['format_preservation']['verify_after']:
    verify_formats_preserved(output, config['format_preservation']['preserve'])
```

### Contract Tests

Template includes contract tests validating format preservation capability:

```python
def test_track_changes_preservation():
    """Verify agent can preserve Track Changes (if configured)."""
    config = load_config()

    if config['format_preservation']['mode'] == 'text_only':
        pytest.skip("Text-only mode doesn't preserve Track Changes")

    # Create test input with Track Changes
    test_input = create_docx_with_track_changes()

    # Process
    output = process_document(test_input)

    # Verify
    assert has_track_changes(output), "Track Changes not preserved"
```

---

## Success Criteria

This protocol is successful if:

1. **Architecture decision is explicit**: Configuration file documents choice (text_only | format_preserving | hybrid)
2. **Requirements drive choice**: 5-question checklist answered, score documented
3. **Round-trip test passes**: Minimal test validates architecture before full implementation
4. **Verification checkpoints exist**: Every critical stage has format verification
5. **L245 failure mode prevented**: 100% Track Changes loss cannot occur silently

---

## References

- **L245**: OOXML Round-Trip Verification Protocol - Catastrophic failure mode (100% Track Changes loss, 10h waste, user-discovered)
- **L84**: Evidence Before Implementation - Validate approach before committing resources
- **L208**: Document Processing Template Pattern - Template creation basis

---

## Changelog

- **v1.0.0** (2025-11-03): Initial protocol created for template-document-processor-AGET v3.0.0
- Based on L245 learnings (docx-AGET catastrophic failure, 2025-11-02)

---

**Protocol Status**: ✅ Active (template v3.0.0+)
**Maintenance**: Review after each L245-type failure (format loss discovered late)
**Owner**: template-document-processor-AGET maintainers
