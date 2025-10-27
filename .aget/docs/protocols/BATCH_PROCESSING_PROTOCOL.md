# Batch Processing Protocol

**Version**: 1.0
**Based on**: L208 lines 260-267 (Pipeline Architecture)
**Last Updated**: 2025-10-26

## Overview

This protocol defines batch processing procedures for processing multiple documents efficiently.

## Batch Operations

### Initialize Batch Processor

```python
from ingestion.batch_processor import BatchProcessor

# Initialize with workers
processor = BatchProcessor(
    max_workers=4,
    batch_size=10
)

print(f"✅ Batch processor initialized ({processor.max_workers} workers)")
```

### Process Batch

```python
# Define processing function
def process_document(doc_path: str) -> dict:
    """Process single document"""
    # Simplified processing
    return {"path": doc_path, "status": "success"}

# Process batch of documents
document_paths = ["/path/to/doc1.pdf", "/path/to/doc2.pdf", "/path/to/doc3.pdf"]

results = processor.process_batch(
    items=document_paths,
    process_func=process_document
)

print(f"✅ Batch complete:")
print(f"  Total: {results.total}")
print(f"  Completed: {results.completed}")
print(f"  Failed: {results.failed}")
print(f"  Progress: {results.progress_percent:.1f}%")
```

### Track Batch Progress

```python
import time

# Start batch processing (non-blocking)
batch_id = processor.start_batch(
    items=document_paths,
    process_func=process_document
)

# Monitor progress
while True:
    progress = processor.get_progress(batch_id)

    print(f"Progress: {progress.progress_percent:.1f}% ({progress.completed}/{progress.total})")

    if progress.completed + progress.failed >= progress.total:
        break

    time.sleep(1)

print(f"✅ Batch processing complete")
```

**Bash batch processing**:

```bash
# Process all PDFs in directory
find /path/to/documents -name "*.pdf" -type f > batch_list.txt

python3 -c "
from ingestion.batch_processor import BatchProcessor

processor = BatchProcessor(max_workers=4)

# Read batch list
with open('batch_list.txt') as f:
    docs = [line.strip() for line in f]

# Process
def process_doc(path):
    print(f'Processing {path}...')
    return {'status': 'success'}

results = processor.process_batch(docs, process_doc)
print(f'Completed: {results.completed}/{results.total}')
"
```

## Related Protocols

- **QUEUE_MANAGEMENT_PROTOCOL.md** - Queue operations
- **PROCESSING_PROTOCOL.md** - Single document processing

## Configuration References

- `configs/processing_limits.yaml` - Batch limits and concurrency

## Module References

- `src/ingestion/batch_processor.py` - Batch processing implementation
