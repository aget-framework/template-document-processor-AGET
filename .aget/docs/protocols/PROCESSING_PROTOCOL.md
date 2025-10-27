# Document Processing Protocol

**Version**: 1.0
**Based on**: L208 lines 163-199 (LLM Processing Architecture)
**Last Updated**: 2025-10-26

## Overview

This protocol defines the end-to-end workflow for processing documents using the template-document-processor-AGET. It covers ingestion, validation, LLM processing, and output publishing.

## Prerequisites

- Python 3.8+
- Required environment variables:
  ```bash
  export OPENAI_API_KEY="sk-..."  # Or your LLM provider key
  ```

- Dependencies installed:
  ```bash
  pip install -r requirements.txt
  ```

## Protocol Steps

### Step 1: Load Configurations

Load the necessary configuration files:

```bash
# Verify configurations exist
ls -1 configs/*.yaml

# Expected output:
# configs/caching.yaml
# configs/llm_providers.yaml
# configs/model_routing.yaml
# configs/processing_limits.yaml
# configs/security_policy.yaml
# configs/validation_rules.yaml
```

**Python code**:

```python
import yaml
from pathlib import Path

# Load configurations
config_dir = Path("configs")

# Load LLM provider config
with open(config_dir / "llm_providers.yaml") as f:
    llm_config = yaml.safe_load(f)

# Load validation rules
with open(config_dir / "validation_rules.yaml") as f:
    validation_config = yaml.safe_load(f)

# Load processing limits
with open(config_dir / "processing_limits.yaml") as f:
    limits_config = yaml.safe_load(f)
```

### Step 2: Initialize Pipeline Components

Initialize the document processing pipeline:

```python
from ingestion.validator import DocumentValidator, FileSizeValidator, FileFormatValidator
from ingestion.queue_manager import QueueManager
from processing.llm_provider import OpenAIProvider
from processing.schema_validator import SchemaValidator, Schema, FieldType
from security.input_sanitizer import InputSanitizer, PromptBuilder
from security.content_filter import ContentFilterPipeline
from output.version_manager import VersionManager
from output.publisher import Publisher

# Initialize validator with rules from config
size_config = validation_config['file_validation']['size']
format_config = validation_config['file_validation']['format']

validator = DocumentValidator(rules=[
    FileSizeValidator(
        max_bytes=size_config['max_bytes'],
        warn_bytes=size_config['warn_bytes']
    ),
    FileFormatValidator(
        allowed_extensions=format_config['allowed_extensions']
    )
])

# Initialize queue manager
queue = QueueManager()

# Initialize LLM provider
provider_config = llm_config['providers']['openai']
llm_provider = OpenAIProvider(
    api_key=os.getenv(provider_config['api']['api_key_env']),
    model=provider_config['defaults']['model']
)

# Initialize security components
sanitizer = InputSanitizer(max_length=50000)
prompt_builder = PromptBuilder(sanitizer=sanitizer)
content_filter = ContentFilterPipeline()

# Initialize schema validator
schema_validator = SchemaValidator()

# Initialize output components
version_manager = VersionManager(versions_dir=".aget/versions")
publisher = Publisher(output_dir=".aget/output")
```

### Step 3: Validate Document

Validate the input document before processing:

```python
# Validate document
document_path = "/path/to/document.pdf"
validation_result = validator.validate(document_path)

if not validation_result.valid:
    print(f"Validation failed: {validation_result.errors}")
    exit(1)

print(f"✅ Document validated: {document_path}")
print(f"Warnings: {validation_result.warnings}")
```

**Command-line equivalent**:

```bash
# Quick validation check
python3 -c "
from ingestion.validator import DocumentValidator
validator = DocumentValidator()
result = validator.validate('document.pdf')
print('Valid:', result.valid)
print('Errors:', result.errors)
"
```

### Step 4: Enqueue Document

Add document to processing queue:

```python
# Enqueue document
queue_item = queue.enqueue(document_path, metadata={
    'source': 'user_upload',
    'priority': 'normal'
})

print(f"✅ Document enqueued: {queue_item.document_id}")
print(f"Queue position: {queue.size()}")
```

### Step 5: Read and Sanitize Document

Read document content and apply security measures:

```python
# Read document (simplified - use appropriate library for format)
with open(document_path, 'r') as f:
    raw_document = f.read()

# Sanitize input
sanitized_document = sanitizer.sanitize(raw_document)

# Filter sensitive content
scan_passed, filter_matches = content_filter.scan(sanitized_document)

if not scan_passed:
    print(f"⚠️  Security violations detected: {len(filter_matches)} matches")
    # Optionally redact
    redacted_document, matches = content_filter.scan_and_redact(sanitized_document)
    sanitized_document = redacted_document

print(f"✅ Document sanitized and filtered")
```

### Step 6: Define Extraction Schema

Define what data to extract from the document:

```python
# Define extraction schema
schema = Schema(name="invoice_schema", description="Extract invoice data")
schema.add_field("invoice_number", FieldType.STRING, required=True)
schema.add_field("date", FieldType.STRING, required=True)
schema.add_field("total_amount", FieldType.NUMBER, required=True)
schema.add_field("vendor_name", FieldType.STRING, required=True)
schema.add_field("line_items", FieldType.ARRAY, required=False)

print(f"✅ Schema defined: {schema.name} ({len(schema.fields)} fields)")
```

### Step 7: Build Safe Prompt

Build a prompt that's resistant to injection attacks:

```python
# Build extraction prompt with security
extraction_schema_dict = {
    "invoice_number": "string",
    "date": "string (YYYY-MM-DD format)",
    "total_amount": "number (USD)",
    "vendor_name": "string",
    "line_items": "array of objects {description: string, amount: number}"
}

safe_prompt = prompt_builder.build_extraction_prompt(
    document=sanitized_document,
    extraction_schema=extraction_schema_dict
)

print(f"✅ Safe prompt built ({len(safe_prompt)} characters)")
```

### Step 8: Process with LLM

Send to LLM for processing:

```python
# Process with LLM
llm_response = llm_provider.complete(
    prompt=safe_prompt,
    temperature=provider_config['defaults']['temperature'],
    seed=provider_config['defaults']['seed']
)

print(f"✅ LLM processing complete")
print(f"Model used: {llm_response.model}")
print(f"Tokens used: {llm_response.usage.total_tokens}")
print(f"Cost: ${llm_response.cost_usd:.4f}")
```

### Step 9: Validate Extracted Data

Validate the extracted data against the schema:

```python
import json

# Parse LLM response (assumes JSON)
extracted_data = json.loads(llm_response.content)

# Validate against schema
validation_result = schema_validator.validate(extracted_data, schema)

if not validation_result.is_valid:
    print(f"❌ Validation failed: {validation_result.errors}")
    # Handle validation failure
else:
    print(f"✅ Data validation passed")
```

### Step 10: Create Version and Publish

Save the processed output with versioning:

```python
# Create version
version = version_manager.create_version(
    document_id=queue_item.document_id,
    content=extracted_data,
    processing_metadata={
        'model': llm_response.model,
        'temperature': provider_config['defaults']['temperature'],
        'seed': provider_config['defaults']['seed'],
        'cost_usd': llm_response.cost_usd,
        'tokens': llm_response.usage.total_tokens,
        'timestamp': time.time()
    }
)

print(f"✅ Version created: {version.version_id} (v{version.number})")

# Publish output
published_path = publisher.publish(
    data=extracted_data,
    document_id=queue_item.document_id,
    format='json'
)

print(f"✅ Output published: {published_path}")
```

### Step 11: Mark as Processed

Update queue status:

```python
# Mark as processed in queue
queue.mark_processed(
    queue_item.document_id,
    result={'status': 'success', 'version_id': version.version_id}
)

print(f"✅ Document marked as processed")
print(f"Queue size: {queue.size()}")
```

## Complete End-to-End Example

```bash
# Create a test script
cat > process_document.py << 'EOF'
#!/usr/bin/env python3
import os
import yaml
import json
import time
from pathlib import Path

# Import all components
from ingestion.validator import DocumentValidator, FileSizeValidator, FileFormatValidator
from ingestion.queue_manager import QueueManager
from processing.llm_provider import OpenAIProvider
from processing.schema_validator import SchemaValidator, Schema, FieldType
from security.input_sanitizer import InputSanitizer, PromptBuilder
from security.content_filter import ContentFilterPipeline
from output.version_manager import VersionManager
from output.publisher import Publisher

def process_document(document_path: str):
    """Process a document end-to-end"""

    # Load configs
    with open("configs/llm_providers.yaml") as f:
        llm_config = yaml.safe_load(f)
    with open("configs/validation_rules.yaml") as f:
        validation_config = yaml.safe_load(f)

    # Initialize components
    validator = DocumentValidator()
    queue = QueueManager()

    provider_config = llm_config['providers']['openai']
    llm_provider = OpenAIProvider(
        api_key=os.getenv(provider_config['api']['api_key_env']),
        model=provider_config['defaults']['model']
    )

    sanitizer = InputSanitizer(max_length=50000)
    prompt_builder = PromptBuilder(sanitizer=sanitizer)
    content_filter = ContentFilterPipeline()

    schema_validator = SchemaValidator()
    version_manager = VersionManager()
    publisher = Publisher()

    # Process pipeline
    print("Step 1: Validating...")
    validation_result = validator.validate(document_path)
    if not validation_result.valid:
        raise ValueError(f"Validation failed: {validation_result.errors}")

    print("Step 2: Enqueuing...")
    queue_item = queue.enqueue(document_path)

    print("Step 3: Reading and sanitizing...")
    with open(document_path, 'r') as f:
        raw_document = f.read()
    sanitized_document = sanitizer.sanitize(raw_document)

    print("Step 4: Filtering content...")
    scan_passed, _ = content_filter.scan(sanitized_document)
    if not scan_passed:
        sanitized_document, _ = content_filter.scan_and_redact(sanitized_document)

    print("Step 5: Defining schema...")
    schema = Schema(name="generic_extraction")
    schema.add_field("summary", FieldType.STRING, required=True)
    schema.add_field("key_points", FieldType.ARRAY, required=False)

    print("Step 6: Building prompt...")
    safe_prompt = prompt_builder.build_extraction_prompt(
        document=sanitized_document,
        extraction_schema={"summary": "string", "key_points": "array"}
    )

    print("Step 7: Processing with LLM...")
    llm_response = llm_provider.complete(
        prompt=safe_prompt,
        temperature=0.0,
        seed=42
    )

    print("Step 8: Validating extracted data...")
    extracted_data = json.loads(llm_response.content)
    validation_result = schema_validator.validate(extracted_data, schema)
    if not validation_result.is_valid:
        raise ValueError(f"Schema validation failed: {validation_result.errors}")

    print("Step 9: Creating version...")
    version = version_manager.create_version(
        document_id=queue_item.document_id,
        content=extracted_data,
        processing_metadata={'model': llm_response.model, 'cost_usd': llm_response.cost_usd}
    )

    print("Step 10: Publishing...")
    published_path = publisher.publish(
        data=extracted_data,
        document_id=queue_item.document_id,
        format='json'
    )

    print("Step 11: Marking as processed...")
    queue.mark_processed(queue_item.document_id, result={'version_id': version.version_id})

    print(f"\n✅ Processing complete!")
    print(f"   Version: {version.version_id}")
    print(f"   Output: {published_path}")
    print(f"   Cost: ${llm_response.cost_usd:.4f}")

    return extracted_data

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python3 process_document.py <document_path>")
        sys.exit(1)

    result = process_document(sys.argv[1])
    print(json.dumps(result, indent=2))
EOF

chmod +x process_document.py

# Run processing
python3 process_document.py sample_document.txt
```

## Common Issues and Troubleshooting

### Issue 1: API Key Not Set

**Symptom**: `KeyError: 'OPENAI_API_KEY'` or authentication error

**Solution**:
```bash
# Check if API key is set
echo $OPENAI_API_KEY

# If not set, export it
export OPENAI_API_KEY="sk-your-key-here"

# Or add to .env file
echo 'OPENAI_API_KEY=sk-your-key-here' >> .env
```

### Issue 2: Document Validation Fails

**Symptom**: `ValidationResult.valid = False` with size or format errors

**Solution**:
```python
# Check validation details
result = validator.validate(document_path)
print(f"Errors: {result.errors}")
print(f"Warnings: {result.warnings}")
print(f"Metadata: {result.metadata}")

# Adjust validation rules if needed
custom_validator = DocumentValidator(rules=[
    FileSizeValidator(max_bytes=20_000_000),  # Increase limit to 20MB
    FileFormatValidator(allowed_extensions=['.txt', '.pdf', '.docx', '.html'])
])
```

## Related Protocols

- **VALIDATION_PROTOCOL.md** - Detailed validation procedures
- **QUEUE_MANAGEMENT_PROTOCOL.md** - Queue operations
- **VERSIONING_PROTOCOL.md** - Version management
- **SECURITY_PROTOCOL.md** - Security best practices

## Configuration References

- `configs/llm_providers.yaml` - LLM provider settings
- `configs/validation_rules.yaml` - Validation rules
- `configs/security_policy.yaml` - Security policies
- `configs/processing_limits.yaml` - Resource limits

## Module References

- `src/ingestion/validator.py` - Document validation
- `src/ingestion/queue_manager.py` - Queue management
- `src/processing/llm_provider.py` - LLM providers
- `src/processing/schema_validator.py` - Schema validation
- `src/security/input_sanitizer.py` - Input sanitization
- `src/security/content_filter.py` - Content filtering
- `src/output/version_manager.py` - Version management
- `src/output/publisher.py` - Output publishing
