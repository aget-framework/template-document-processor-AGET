# Version Management Protocol

**Version**: 1.0
**Based on**: L208 lines 200-227 (Idempotence & Reproducibility - Version Management)
**Last Updated**: 2025-10-26

## Overview

This protocol defines version management for processed documents. Versioning enables history tracking, comparison, and rollback capabilities.

## Version Creation

### Create First Version

```python
from output.version_manager import VersionManager

# Initialize manager
vm = VersionManager(versions_dir=".aget/versions")

# Create version
version = vm.create_version(
    document_id="doc_001",
    content={"invoice_number": "INV-001", "amount": 1000.00},
    processing_metadata={
        'timestamp': '2025-10-26T10:30:00Z',
        'prompt_version': 'extraction_v2.1',
        'model': 'gpt-4o-2024-08-06',
        'temperature': 0.0,
        'seed': 42,
        'cost_usd': 0.023,
        'latency_ms': 1234
    }
)

print(f"✅ Version created: {version.version_id}")
print(f"Version number: {version.number}")  # Sequential: 1, 2, 3, ...
print(f"Content hash: {version.content_hash}")
```

### Create Subsequent Versions

```python
# Update document - creates v2
updated_version = vm.create_version(
    document_id="doc_001",
    content={"invoice_number": "INV-001", "amount": 1050.00},  # Amount changed
    processing_metadata={
        'timestamp': '2025-10-26T11:00:00Z',
        'prompt_version': 'extraction_v2.1',
        'model': 'gpt-4o-2024-08-06',
        'reason': 'Amount correction'
    },
    parent_version_id=version.version_id  # Link to previous version
)

print(f"✅ New version created: v{updated_version.number}")
```

**Command-line version creation**:

```bash
python3 -c "
from output.version_manager import VersionManager
import time

vm = VersionManager()
v = vm.create_version(
    document_id='doc_001',
    content={'data': 'test'},
    processing_metadata={'timestamp': time.time(), 'model': 'gpt-4o'}
)
print(f'Created: {v.version_id} (v{v.number})')
"
```

## Version Retrieval

### Get Specific Version

```python
# Get version by ID
version_id = "doc_001_v1730000000_abc12345"
version = vm.get_version(version_id)

if version:
    print(f"Version: v{version.number}")
    print(f"Content: {version.content}")
    print(f"Timestamp: {version.timestamp}")
    print(f"Metadata: {version.processing_metadata}")
else:
    print(f"Version not found: {version_id}")
```

### Get Latest Version

```python
# Get most recent version of document
latest = vm.get_latest_version(document_id="doc_001")

if latest:
    print(f"Latest version: v{latest.number}")
    print(f"Content: {latest.content}")
    print(f"Created: {latest.timestamp}")
else:
    print("No versions found for document")
```

### Get Version History

```python
# Get all versions of document
history = vm.get_version_history(document_id="doc_001")

print(f"Version history ({len(history)} versions):")
for version in history:
    print(f"  v{version.number}: {version.version_id}")
    print(f"    Created: {version.timestamp}")
    print(f"    Hash: {version.content_hash[:16]}...")
    print(f"    Model: {version.processing_metadata.get('model', 'unknown')}")
```

**Bash version history**:

```bash
python3 -c "
from output.version_manager import VersionManager
vm = VersionManager()
history = vm.get_version_history('doc_001')
for v in history:
    print(f'v{v.number}: {v.version_id} | {v.content_hash[:8]}')
"
```

## Version Comparison

### Compare Two Versions

```python
# Compare versions
v1_id = "doc_001_v1730000000_abc12345"
v2_id = "doc_001_v1730003600_def67890"

comparison = vm.compare_versions(v1_id, v2_id)

print("Version Comparison:")
print(f"Same document: {comparison['same_document']}")
print(f"Content changed: {comparison['content_changed']}")
print(f"Time difference: {comparison['time_diff_seconds']:.1f} seconds")

print("\nVersion 1:")
print(f"  ID: {comparison['version_1']['id']}")
print(f"  Hash: {comparison['version_1']['content_hash'][:16]}...")
print(f"  Metadata: {comparison['version_1']['metadata']}")

print("\nVersion 2:")
print(f"  ID: {comparison['version_2']['id']}")
print(f"  Hash: {comparison['version_2']['content_hash'][:16]}...")
print(f"  Metadata: {comparison['version_2']['metadata']}")
```

### Detect Content Changes

```python
def detect_changes(v1_id: str, v2_id: str) -> dict:
    """Detect specific changes between versions"""

    v1 = vm.get_version(v1_id)
    v2 = vm.get_version(v2_id)

    if not v1 or not v2:
        return {'error': 'Version not found'}

    changes = {
        'added_keys': [],
        'removed_keys': [],
        'modified_keys': []
    }

    # Find added/removed keys
    v1_keys = set(v1.content.keys())
    v2_keys = set(v2.content.keys())

    changes['added_keys'] = list(v2_keys - v1_keys)
    changes['removed_keys'] = list(v1_keys - v2_keys)

    # Find modified values
    for key in v1_keys & v2_keys:
        if v1.content[key] != v2.content[key]:
            changes['modified_keys'].append({
                'key': key,
                'old_value': v1.content[key],
                'new_value': v2.content[key]
            })

    return changes

# Use change detection
changes = detect_changes(v1_id, v2_id)
print(f"Added keys: {changes['added_keys']}")
print(f"Removed keys: {changes['removed_keys']}")
print(f"Modified: {len(changes['modified_keys'])} keys")
```

## Version Deletion

### Delete Specific Version

```python
# Delete version
deleted = vm.delete_version(version_id="doc_001_v1730000000_abc12345")

if deleted:
    print(f"✅ Version deleted")
else:
    print(f"❌ Version not found or could not delete")
```

**Warning**: Deleting versions breaks version history. Use with caution.

## Integration with Processing Pipeline

### Auto-versioning After Processing

```python
from processing.llm_provider import OpenAIProvider
from output.version_manager import VersionManager
import time

def process_with_versioning(document_id: str, document_content: str):
    """Process document and auto-create version"""

    # Process with LLM
    provider = OpenAIProvider(api_key=os.getenv("OPENAI_API_KEY"), model="gpt-4o")
    response = provider.complete(prompt=f"Extract data: {document_content}")

    # Parse result
    import json
    extracted_data = json.loads(response.content)

    # Create version
    vm = VersionManager()
    version = vm.create_version(
        document_id=document_id,
        content=extracted_data,
        processing_metadata={
            'timestamp': time.time(),
            'model': response.model,
            'cost_usd': response.cost_usd,
            'tokens': response.usage.total_tokens,
            'prompt_hash': response.prompt_hash
        }
    )

    print(f"✅ Processed and versioned: v{version.number}")
    return version

# Use auto-versioning
version = process_with_versioning("doc_001", "Invoice data...")
```

## Common Issues and Troubleshooting

### Issue 1: Version Directory Not Found

**Solution**:
```python
from pathlib import Path

versions_dir = Path(".aget/versions")
versions_dir.mkdir(parents=True, exist_ok=True)

vm = VersionManager(versions_dir=str(versions_dir))
```

### Issue 2: Content Hash Collisions

**Symptom**: Two different contents produce same hash (very rare)

**Solution**: Verify content equality
```python
v1 = vm.get_version(v1_id)
v2 = vm.get_version(v2_id)

if v1.content_hash == v2.content_hash:
    # Verify actual content
    if v1.content == v2.content:
        print("✅ Content is identical (same hash)")
    else:
        print("⚠️  Hash collision detected (different content, same hash)")
```

## Version Pruning Strategy

```python
def prune_old_versions(document_id: str, keep_recent: int = 10):
    """Keep only N most recent versions"""

    history = vm.get_version_history(document_id)

    if len(history) <= keep_recent:
        print(f"No pruning needed ({len(history)} <= {keep_recent})")
        return

    # Sort by timestamp (newest first)
    history.sort(key=lambda v: v.timestamp, reverse=True)

    # Keep recent, delete old
    to_delete = history[keep_recent:]

    print(f"Pruning {len(to_delete)} old versions...")
    for version in to_delete:
        vm.delete_version(version.version_id)
        print(f"  Deleted: v{version.number}")

    print(f"✅ Kept {keep_recent} most recent versions")

# Prune old versions
prune_old_versions("doc_001", keep_recent=5)
```

## Related Protocols

- **ROLLBACK_PROTOCOL.md** - Version rollback procedures
- **PROCESSING_PROTOCOL.md** - Integration with processing

## Configuration References

- `configs/processing_limits.yaml` - Version quotas (max_versions_per_document)

## Module References

- `src/output/version_manager.py` - Version management implementation
