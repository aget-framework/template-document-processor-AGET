# Document Validation Protocol

**Version**: 1.0
**Based on**: L208 lines 247-251 (Validation Pipeline Architecture)
**Last Updated**: 2025-10-26

## Overview

This protocol defines pre-processing and post-processing validation procedures for document processing. Validation occurs at multiple stages to ensure data quality and integrity.

## Validation Stages

1. **Pre-processing validation**: Before document enters pipeline
2. **Schema validation**: After LLM extraction
3. **Output validation**: Before publishing results

## Pre-Processing Validation

### Step 1: File Validation

Validate file existence, size, and format:

```python
from ingestion.validator import (
    DocumentValidator,
    FileExistsValidator,
    FileSizeValidator,
    FileFormatValidator
)
from pathlib import Path

# Create validator with default rules
validator = DocumentValidator()

# Or create with custom rules
custom_validator = DocumentValidator(rules=[
    FileExistsValidator(),
    FileSizeValidator(max_bytes=10_485_760, warn_bytes=8_388_608),  # 10MB max, 8MB warn
    FileFormatValidator(allowed_extensions=['.txt', '.pdf', '.docx'])
])

# Validate document
document_path = "/path/to/document.pdf"
result = validator.validate(document_path)

# Check result
if result.valid:
    print("✅ Document is valid")
else:
    print(f"❌ Validation failed:")
    for error in result.errors:
        print(f"   - {error}")

# Check warnings
if result.has_warnings:
    print("⚠️  Warnings:")
    for warning in result.warnings:
        print(f"   - {warning}")

# Inspect metadata
print(f"File size: {result.metadata.get('size_bytes', 0):,} bytes")
print(f"Extension: {result.metadata.get('extension', 'unknown')}")
```

**Command-line validation**:

```bash
# Quick file check
python3 -c "
from ingestion.validator import DocumentValidator
validator = DocumentValidator()
result = validator.validate('document.pdf')
print(f'Valid: {result.valid}')
if not result.valid:
    for err in result.errors:
        print(f'  Error: {err}')
if result.warnings:
    for warn in result.warnings:
        print(f'  Warning: {warn}')
"
```

### Step 2: Batch Validation

Validate multiple documents:

```python
from pathlib import Path

# Validate batch of documents
document_dir = Path("/path/to/documents")
document_paths = list(document_dir.glob("*.pdf"))

print(f"Validating {len(document_paths)} documents...")

# Batch validate
results = validator.validate_batch([str(p) for p in document_paths])

# Analyze results
valid_count = sum(1 for r in results if r.valid)
invalid_count = len(results) - valid_count

print(f"✅ Valid: {valid_count}/{len(results)}")
print(f"❌ Invalid: {invalid_count}/{len(results)}")

# Get invalid documents
invalid_docs = [r for r in results if not r.valid]
for result in invalid_docs:
    print(f"\n{result.document_path}:")
    for error in result.errors:
        print(f"  - {error}")
```

**Bash batch validation**:

```bash
# Validate all PDFs in directory
find /path/to/documents -name "*.pdf" -type f | while read doc; do
    python3 -c "
from ingestion.validator import DocumentValidator
validator = DocumentValidator()
result = validator.validate('$doc')
status = '✅' if result.valid else '❌'
print(f'{status} $doc')
"
done
```

### Step 3: Custom Validation Rules

Create agent-specific validation rules:

```python
from ingestion.validator import ValidationRule
from pathlib import Path
from typing import List, Tuple, Dict

class ContentLengthValidator(ValidationRule):
    """Validates document content length"""

    def __init__(self, min_chars: int = 100, max_chars: int = 100000):
        self.min_chars = min_chars
        self.max_chars = max_chars

    def validate(self, document_path: Path, metadata: Dict) -> Tuple[List[str], List[str]]:
        errors = []
        warnings = []

        # Read file
        try:
            with open(document_path, 'r', encoding='utf-8') as f:
                content = f.read()

            char_count = len(content)
            metadata['char_count'] = char_count

            if char_count < self.min_chars:
                errors.append(f"Content too short: {char_count} chars (min: {self.min_chars})")
            elif char_count > self.max_chars:
                errors.append(f"Content too long: {char_count} chars (max: {self.max_chars})")
            elif char_count > self.max_chars * 0.8:
                warnings.append(f"Content approaching limit: {char_count} chars")

        except Exception as e:
            errors.append(f"Failed to read content: {e}")

        return errors, warnings

# Use custom validator
custom_validator = DocumentValidator(rules=[
    FileExistsValidator(),
    FileSizeValidator(max_bytes=5_242_880),  # 5MB
    ContentLengthValidator(min_chars=500, max_chars=50000)
])

result = custom_validator.validate("document.txt")
```

## Schema Validation (Post-Extraction)

### Step 1: Define Schema

Define the expected data structure:

```python
from processing.schema_validator import SchemaValidator, Schema, FieldType

# Create schema
schema = Schema()  # Create empty schema
    # Note: name and description would be in metadata, not Schema constructor
    # schema = Schema(
    name="invoice_schema",
    description="Invoice data extraction schema"
)

# Add required fields
schema.add_field("invoice_number", FieldType.STRING, required=True)
schema.add_field("date", FieldType.STRING, required=True)
schema.add_field("total_amount", FieldType.NUMBER, required=True)
schema.add_field("vendor_name", FieldType.STRING, required=True)

# Add optional fields
schema.add_field("line_items", FieldType.ARRAY, required=False)
schema.add_field("notes", FieldType.STRING, required=False)

print(f"Schema created: {schema.name}")
print(f"Fields: {len(schema.fields)} ({sum(1 for f in schema.fields.values() if f.required)} required)")
```

### Step 2: Validate Extracted Data

Validate data extracted by LLM:

```python
# Sample extracted data
extracted_data = {
    "invoice_number": "INV-2025-001",
    "date": "2025-10-26",
    "total_amount": 1234.56,
    "vendor_name": "Acme Corp",
    "line_items": [
        {"description": "Widget A", "quantity": 10, "price": 100.00},
        {"description": "Widget B", "quantity": 5, "price": 150.00}
    ]
}

# Validate
validator = SchemaValidator()
result = validator.validate(extracted_data, schema)

if result.is_valid:
    print("✅ Schema validation passed")
else:
    print("❌ Schema validation failed:")
    for error in result.errors:
        print(f"   - {error}")
```

### Step 3: Handle Validation Failures

```python
def validate_with_fallback(data: dict, schema: Schema) -> dict:
    """Validate data and provide fallback handling"""

    validator = SchemaValidator()
    result = validator.validate(data, schema)

    if result.is_valid:
        return data

    print(f"⚠️  Validation errors detected: {len(result.errors)} errors")

    # Option 1: Fill missing required fields with defaults
    filled_data = data.copy()
    for field_name, field_def in schema.fields.items():
        if field_def.required and field_name not in filled_data:
            # Provide default based on type
            defaults = {
                FieldType.STRING: "",
                FieldType.NUMBER: 0,
                FieldType.BOOLEAN: False,
                FieldType.ARRAY: [],
                FieldType.OBJECT: {}
            }
            filled_data[field_name] = defaults.get(field_def.field_type, None)
            print(f"   Filled missing field: {field_name}")

    # Re-validate
    result = validator.validate(filled_data, schema)
    if result.is_valid:
        print("✅ Validation passed after filling defaults")
        return filled_data
    else:
        raise ValueError(f"Validation still failing: {result.errors}")

# Use fallback validation
try:
    validated_data = validate_with_fallback(extracted_data, schema)
except ValueError as e:
    print(f"❌ Cannot recover from validation errors: {e}")
```

## Output Validation

### Step 1: Validate LLM Output Safety

Check LLM output for manipulation attempts:

```python
from security.input_sanitizer import InputSanitizer

# Get LLM output
llm_output = """
{
    "invoice_number": "INV-2025-001",
    "total_amount": 1234.56
}
"""

# Validate output doesn't contain injection attempts
is_safe = InputSanitizer.validate_output(llm_output)

if not is_safe:
    print("⚠️  Suspicious LLM output detected!")
    print("Output may contain control tokens or injection attempts")
    # Handle suspicious output (reject, sanitize, or flag for review)
else:
    print("✅ LLM output appears safe")
```

### Step 2: Validate Published Output

Verify output before publication:

```python
from output.publisher import Publisher
import json

def validate_before_publish(data: dict, schema: Schema) -> bool:
    """Validate data before publishing"""

    # Schema validation
    validator = SchemaValidator()
    schema_result = validator.validate(data, schema)
    if not schema_result.is_valid:
        print(f"❌ Schema validation failed: {schema_result.errors}")
        return False

    # Data integrity checks
    # Example: Check for null/empty required fields
    for field_name, field_def in schema.fields.items():
        if field_def.required:
            value = data.get(field_name)
            if value is None or value == "" or value == []:
                print(f"❌ Required field is empty: {field_name}")
                return False

    # JSON serialization check
    try:
        json.dumps(data)
    except (TypeError, ValueError) as e:
        print(f"❌ Data not JSON serializable: {e}")
        return False

    print("✅ Pre-publication validation passed")
    return True

# Validate before publishing
if validate_before_publish(extracted_data, schema):
    publisher = Publisher()
    output_path = publisher.publish(
        data=extracted_data,
        document_id="doc_123",
        format='json'
    )
    print(f"✅ Published: {output_path}")
else:
    print("❌ Publishing aborted due to validation failures")
```

## Validation Configuration

### Load Validation Rules from Config

```python
import yaml

# Load validation config
with open("configs/validation_rules.yaml") as f:
    config = yaml.safe_load(f)

# Create validator from config
size_config = config['file_validation']['size']
format_config = config['file_validation']['format']

validator = DocumentValidator(rules=[
    FileSizeValidator(
        max_bytes=size_config['max_bytes'],
        warn_bytes=size_config['warn_bytes']
    ),
    FileFormatValidator(
        allowed_extensions=format_config['allowed_extensions']
    )
])

print(f"Validator configured from validation_rules.yaml")
print(f"Max size: {size_config['max_bytes']:,} bytes")
print(f"Allowed formats: {', '.join(format_config['allowed_extensions'])}")
```

## Common Issues and Troubleshooting

### Issue 1: Empty List Validation Error

**Symptom**: `DocumentValidator(rules=[])` still loads default rules

**Root Cause**: Python falsy empty list gotcha

**Solution**:
```python
# WRONG - Will load defaults
validator = DocumentValidator(rules=[])

# RIGHT - Explicit None check in implementation
# The DocumentValidator handles this correctly:
validator = DocumentValidator(rules=[])  # Will use empty list, not defaults
```

### Issue 2: Schema Validation Passes But Data is Wrong

**Symptom**: Schema validation says valid, but extracted data incorrect

**Solution**: Add custom validation logic
```python
def validate_invoice_logic(data: dict) -> bool:
    """Business logic validation beyond schema"""

    # Check date format
    import re
    if not re.match(r'\d{4}-\d{2}-\d{2}', data.get('date', '')):
        print("❌ Invalid date format (expected YYYY-MM-DD)")
        return False

    # Check amount is positive
    if data.get('total_amount', 0) <= 0:
        print("❌ Invalid amount (must be positive)")
        return False

    # Check line items sum to total (if provided)
    if 'line_items' in data:
        line_total = sum(item.get('price', 0) * item.get('quantity', 0)
                        for item in data['line_items'])
        if abs(line_total - data['total_amount']) > 0.01:
            print(f"⚠️  Line items ({line_total}) don't match total ({data['total_amount']})")
            return False

    return True

# Use custom logic validation
if validate_invoice_logic(extracted_data):
    print("✅ Business logic validation passed")
```

## Validation Pipeline Example

Complete validation pipeline:

```bash
# Create validation script
cat > validate_pipeline.py << 'EOF'
#!/usr/bin/env python3
from ingestion.validator import DocumentValidator
from processing.schema_validator import SchemaValidator, Schema, FieldType
from security.input_sanitizer import InputSanitizer
import json

def validate_pipeline(document_path: str, extracted_data: dict, schema: Schema) -> bool:
    """Run complete validation pipeline"""

    # Stage 1: Pre-processing validation
    print("Stage 1: File validation...")
    doc_validator = DocumentValidator()
    file_result = doc_validator.validate(document_path)
    if not file_result.valid:
        print(f"❌ File validation failed: {file_result.errors}")
        return False
    print("✅ File validation passed")

    # Stage 2: Schema validation
    print("Stage 2: Schema validation...")
    schema_validator = SchemaValidator()
    schema_result = schema_validator.validate(extracted_data, schema)
    if not schema_result.is_valid:
        print(f"❌ Schema validation failed: {schema_result.errors}")
        return False
    print("✅ Schema validation passed")

    # Stage 3: Output safety validation
    print("Stage 3: Output safety validation...")
    output_json = json.dumps(extracted_data)
    is_safe = InputSanitizer.validate_output(output_json)
    if not is_safe:
        print("❌ Output safety validation failed")
        return False
    print("✅ Output safety validation passed")

    print("\n✅ All validation stages passed!")
    return True

if __name__ == "__main__":
    # Test data
    schema = Schema()  # Create empty schema
    # Note: name and description would be in metadata, not Schema constructor
    # schema = Schema()  # Create empty schema
    schema.add_field("name", FieldType.STRING, required=True)

    data = {"name": "Test"}

    validate_pipeline("test.txt", data, schema)
EOF

chmod +x validate_pipeline.py
python3 validate_pipeline.py
```

## Related Protocols

- **PROCESSING_PROTOCOL.md** - End-to-end processing workflow
- **SECURITY_PROTOCOL.md** - Security validation procedures
- **SCHEMA_PROTOCOL.md** - Schema design and validation

## Configuration References

- `configs/validation_rules.yaml` - Validation rules configuration
- `configs/security_policy.yaml` - Security validation policies

## Module References

- `src/ingestion/validator.py` - File validation
- `src/processing/schema_validator.py` - Schema validation
- `src/security/input_sanitizer.py` - Output safety validation
