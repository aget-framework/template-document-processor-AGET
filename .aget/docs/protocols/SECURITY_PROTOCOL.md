# Security Protocol

**Version**: 1.0
**Based on**: L208 lines 541-548, 549-570 (Security Protocols)
**Last Updated**: 2025-10-26

## Overview

This protocol defines security procedures for document processing, including input sanitization, content filtering, and output validation.

## Input Sanitization

### Sanitize User Input

```python
from security.input_sanitizer import InputSanitizer

# Initialize sanitizer
sanitizer = InputSanitizer(max_length=50000)

# Sanitize raw input
raw_document = """
User provided document with potential <|system|> tokens...
"""

sanitized = sanitizer.sanitize(raw_document)
print(f"✅ Input sanitized ({len(sanitized)} chars)")
```

### Build Safe Prompts

```python
from security.input_sanitizer import PromptBuilder

# Initialize prompt builder
builder = PromptBuilder()

# Build extraction prompt with security
safe_prompt = builder.build_extraction_prompt(
    document=sanitized,
    extraction_schema={"field1": "string", "field2": "number"}
)

# Or build summarization prompt
summary_prompt = builder.build_summarization_prompt(
    document=sanitized,
    max_length=200
)

print(f"✅ Safe prompt built")
```

## Content Filtering

### Scan for Sensitive Content

```python
from security.content_filter import ContentFilterPipeline

# Initialize filter
content_filter = ContentFilterPipeline()

# Scan document
text = "Contact me at john@example.com or SSN: 123-45-6789"
passed, matches = content_filter.scan(text)

if not passed:
    print(f"⚠️  Found {len(matches)} security violations:")
    for match in matches:
        print(f"   {match.filter_name}: {match.matched_text} (severity: {match.severity})")
```

### Redact Sensitive Content

```python
# Scan and redact
redacted_text, matches = content_filter.scan_and_redact(text)

print(f"Original: {text}")
print(f"Redacted: {redacted_text}")
# Output: "Contact me at [REDACTED:email] or SSN: [REDACTED:ssn]"
```

## Output Validation

### Validate LLM Output

```python
from security.input_sanitizer import InputSanitizer

llm_output = '{"data": "extracted content"}'

is_safe = InputSanitizer.validate_output(llm_output)

if not is_safe:
    print("⚠️  Suspicious LLM output detected")
else:
    print("✅ Output validation passed")
```

## Related Protocols

- **PROCESSING_PROTOCOL.md** - Integration with processing
- **VALIDATION_PROTOCOL.md** - Validation procedures

## Configuration References

- `configs/security_policy.yaml` - Security policies

## Module References

- `src/security/input_sanitizer.py` - Input sanitization
- `src/security/content_filter.py` - Content filtering
