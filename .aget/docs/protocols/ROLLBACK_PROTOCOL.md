# Rollback Protocol

**Version**: 1.0
**Based on**: L208 lines 200-227 (Version Management - Rollback)
**Last Updated**: 2025-10-26

## Overview

This protocol defines procedures for rolling back to previous document versions when errors occur or corrections are needed.

## Rollback Operations

### Simple Rollback

```python
from output.rollback_manager import RollbackManager, RollbackReason
from output.version_manager import VersionManager

# Initialize managers
vm = VersionManager()
rm = RollbackManager(version_manager=vm)

# Rollback to previous version
rollback = rm.rollback_document(
    document_id="doc_001",
    target_version_id="doc_001_v1730000000_abc12345",
    reason=RollbackReason.USER_REQUESTED,
    dry_run=False  # Set True to preview without executing
)

if rollback.success:
    print(f"✅ Rollback successful")
    print(f"From: v{rollback.from_version.number}")
    print(f"To: v{rollback.to_version.number}")
else:
    print(f"❌ Rollback failed: {rollback.error}")
```

### Dry-Run Rollback

Preview rollback without executing:

```python
# Dry-run to preview changes
rollback = rm.rollback_document(
    document_id="doc_001",
    target_version_id="doc_001_v1730000000_abc12345",
    reason=RollbackReason.DATA_CORRECTION,
    dry_run=True
)

print(f"Dry-run preview:")
print(f"  Would rollback from: v{rollback.from_version.number}")
print(f"  Would rollback to: v{rollback.to_version.number}")
print(f"  Reason: {rollback.reason}")

# Execute if preview looks good
if input("Proceed? (y/n): ").lower() == 'y':
    actual_rollback = rm.rollback_document(
        document_id="doc_001",
        target_version_id="doc_001_v1730000000_abc12345",
        reason=RollbackReason.DATA_CORRECTION,
        dry_run=False
    )
```

### Rollback Reasons

Available rollback reasons (enum):

```python
from output.rollback_manager import RollbackReason

# USER_REQUESTED - User explicitly requested rollback
# DATA_CORRECTION - Correcting erroneous data
# PROCESSING_ERROR - LLM processing produced incorrect result
# VALIDATION_FAILURE - Schema validation failed
# SECURITY_ISSUE - Security concern with current version
```

**Bash rollback**:

```bash
python3 -c "
from output.rollback_manager import RollbackManager, RollbackReason
from output.version_manager import VersionManager

vm = VersionManager()
rm = RollbackManager(version_manager=vm)

rollback = rm.rollback_document(
    document_id='doc_001',
    target_version_id='doc_001_v1730000000_abc12345',
    reason=RollbackReason.USER_REQUESTED,
    dry_run=False
)

print('Success:', rollback.success)
"
```

## Rollback History

### Track Rollback Events

```python
# Get rollback history (if implemented)
# Note: Current implementation creates new version on rollback
# Rollback history can be tracked via version metadata

history = vm.get_version_history("doc_001")

# Find rollback events
rollbacks = [
    v for v in history
    if v.processing_metadata.get('rollback_from')
]

print(f"Rollback events: {len(rollbacks)}")
for v in rollbacks:
    print(f"  v{v.number}: Rolled back from {v.processing_metadata['rollback_from']}")
```

## Common Issues

### Issue: Cannot Rollback - Target Version Not Found

**Solution**:
```python
# Verify target version exists
target_version = vm.get_version(target_version_id)
if not target_version:
    print(f"Target version not found: {target_version_id}")
    # List available versions
    history = vm.get_version_history(document_id)
    print("Available versions:")
    for v in history:
        print(f"  v{v.number}: {v.version_id}")
```

## Related Protocols

- **VERSIONING_PROTOCOL.md** - Version management
- **PROCESSING_PROTOCOL.md** - Processing workflow

## Module References

- `src/output/rollback_manager.py` - Rollback implementation
- `src/output/version_manager.py` - Version management
