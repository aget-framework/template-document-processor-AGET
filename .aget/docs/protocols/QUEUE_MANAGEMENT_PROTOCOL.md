# Queue Management Protocol

**Version**: 1.1 (Corrected)
**Based on**: L208 lines 260-267 (Pipeline Architecture - Ingestion)
**Last Updated**: 2025-10-26

## Overview

This protocol defines queue management operations for document processing. The queue manages document ingestion using three states: CANDIDATE, PENDING, PROCESSED, FAILED.

## Queue Operations

### Initialize Queue Manager

```python
from ingestion.queue_manager import QueueManager

# Initialize with default storage
queue = QueueManager()

# Or specify custom storage file
queue = QueueManager(queue_file=".aget/custom_queue.json")

print(f"✅ Queue initialized")

# Get queue status
status = queue.get_status()
print(f"Total items: {status['total']}")
print(f"Candidates: {status['candidates']}")
print(f"Pending: {status['pending']}")
print(f"Processed: {status['processed']}")
print(f"Failed: {status['failed']}")
```

**Command-line check**:

```bash
# Quick queue status
PYTHONPATH=src python3 -c "
from ingestion.queue_manager import QueueManager
queue = QueueManager()
status = queue.get_status()
print(f\"Total: {status['total']}\")
print(f\"Candidates: {status['candidates']}\")
"
```

## Document Ingestion

### Step 1: Add Document to Queue

Add a document to the candidate queue:

```python
from ingestion.queue_manager import QueueManager
from pathlib import Path

queue = QueueManager()

# Get document details
doc_path = "/path/to/document.pdf"
doc_size = Path(doc_path).stat().st_size

# Add to candidate queue
queue_item = queue.add_candidate(
    document_id="doc_001",
    path=doc_path,
    size_bytes=doc_size,
    metadata={
        'source': 'user_upload',
        'priority': 'normal',
        'uploaded_by': 'user123',
        'tags': ['invoice', 'urgent']
    }
)

print(f"✅ Document added to queue")
print(f"   Document ID: {queue_item.document_id}")
print(f"   Path: {queue_item.path}")
print(f"   State: {queue_item.state.value}")
print(f"   Size: {queue_item.size_bytes:,} bytes")
```

### Step 2: Batch Add Documents

Add multiple documents to queue:

```python
from pathlib import Path
import hashlib

# Get all PDFs in directory
document_dir = Path("/path/to/documents")
pdf_files = list(document_dir.glob("*.pdf"))

print(f"Adding {len(pdf_files)} documents to queue...")

# Add all
for pdf_path in pdf_files:
    # Generate document ID from file
    doc_id = hashlib.sha256(str(pdf_path).encode()).hexdigest()[:16]
    doc_size = pdf_path.stat().st_size

    queue_item = queue.add_candidate(
        document_id=doc_id,
        path=str(pdf_path),
        size_bytes=doc_size,
        metadata={'source': 'batch_upload', 'batch_id': 'batch_001'}
    )
    print(f"  Added: {pdf_path.name}")

status = queue.get_status()
print(f"✅ Added {len(pdf_files)} documents")
print(f"Total candidates: {status['candidates']}")
```

**Bash batch add**:

```bash
# Add all PDFs in directory
find /path/to/documents -name "*.pdf" -type f | while read pdf; do
    PYTHONPATH=src python3 -c "
from ingestion.queue_manager import QueueManager
from pathlib import Path
import hashlib

queue = QueueManager()
pdf_path = Path('$pdf')
doc_id = hashlib.sha256(str(pdf_path).encode()).hexdigest()[:16]
doc_size = pdf_path.stat().st_size

item = queue.add_candidate(doc_id, str(pdf_path), doc_size, {'source': 'batch'})
print(f'Added: {doc_id}')
"
done
```

## Queue Retrieval

### Step 1: Get Candidate Documents

Get documents ready for processing:

```python
# Get all candidates
candidates = queue.get_candidates()
print(f"Candidates ready for processing: {len(candidates)}")

# Get limited number of candidates
next_batch = queue.get_candidates(limit=10)
print(f"Next batch: {len(next_batch)} documents")

for item in next_batch:
    print(f"  {item.document_id}: {item.path}")
```

### Step 2: Mark Document as Processing

Move document to PENDING state:

```python
# Get next candidate
candidates = queue.get_candidates(limit=1)
if candidates:
    candidate = candidates[0]

    # Mark as pending (being processed)
    queue.mark_pending(candidate.document_id)
    print(f"✅ Marked as pending: {candidate.document_id}")

    # Process document
    try:
        # ... processing logic ...
        print(f"Processing {candidate.path}...")

        # Mark as processed when done
        queue.mark_processed(
            candidate.document_id,
            result={'status': 'success', 'extracted_fields': 10}
        )
        print(f"✅ Marked as processed")

    except Exception as e:
        # Mark as failed if error
        queue.mark_failed(candidate.document_id, error_message=str(e))
        print(f"❌ Marked as failed: {e}")
else:
    print("No candidates available")
```

### Step 3: Get Queue Items by State

View items in specific states:

```python
# Get items by state
candidates = queue.get_candidates()
pending = queue.get_pending()
processed = queue.get_processed()
failed = queue.get_failed()

print(f"Queue contents:")
print(f"  Candidates: {len(candidates)}")
print(f"  Pending: {len(pending)}")
print(f"  Processed: {len(processed)}")
print(f"  Failed: {len(failed)}")

# List all candidates
if candidates:
    print(f"\nCandidate documents:")
    for item in candidates:
        print(f"  {item.document_id}: {item.path}")
        print(f"    Added: {item.added_timestamp}")
        print(f"    Metadata: {item.metadata}")
```

## Status Management

### Mark as Processed

Update status after successful processing:

```python
# Mark document as processed with result
queue.mark_processed(
    document_id="doc_001",
    result={
        'status': 'success',
        'version_id': 'v1_abc123',
        'extracted_fields': 15,
        'processing_time_seconds': 12.5
    }
)

print(f"✅ Document marked as processed")
```

### Mark as Failed

Update status after processing failure:

```python
# Mark document as failed
queue.mark_failed(
    document_id="doc_001",
    error_message="LLM timeout after 60 seconds"
)

print(f"❌ Document marked as failed")
```

### Get Item Status

Check status of specific document:

```python
# Get item by ID
document_id = "doc_001"
if document_id in queue.items:
    item = queue.items[document_id]

    print(f"Document: {item.document_id}")
    print(f"State: {item.state.value}")  # CANDIDATE, PENDING, PROCESSED, FAILED
    print(f"Added at: {item.added_timestamp}")

    if item.processed_timestamp:
        print(f"Processed at: {item.processed_timestamp}")
        duration = item.processed_timestamp - item.added_timestamp
        print(f"Processing duration: {duration:.1f} seconds")

    if item.result:
        print(f"Result: {item.result}")

    if item.error_message:
        print(f"Error: {item.error_message}")
else:
    print(f"Document not found: {document_id}")
```

## Queue Filtering

### Filter by Metadata

Filter documents by custom metadata:

```python
# Get all items
all_items = list(queue.items.values())

# Filter by metadata
urgent_items = [
    item for item in all_items
    if item.metadata and item.metadata.get('priority') == 'high'
]

batch_items = [
    item for item in all_items
    if item.metadata and 'batch_id' in item.metadata
]

print(f"Found {len(urgent_items)} urgent documents")
print(f"Found {len(batch_items)} batch documents")
```

## Queue Maintenance

### Retry Failed Items

Re-add failed items for retry:

```python
import hashlib

# Get failed items
failed_items = queue.get_failed()

print(f"Found {len(failed_items)} failed items to retry...")

for item in failed_items:
    # Create new document ID for retry
    retry_id = hashlib.sha256(f"{item.document_id}_retry".encode()).hexdigest()[:16]

    # Re-add to queue with retry metadata
    retry_item = queue.add_candidate(
        document_id=retry_id,
        path=item.path,
        size_bytes=item.size_bytes,
        metadata={
            **(item.metadata or {}),
            'retry': True,
            'original_id': item.document_id,
            'original_error': item.error_message
        }
    )
    print(f"✅ Re-added for retry: {item.document_id} → {retry_id}")

print(f"✅ Retry queue updated")
```

## Batch Processing with Queue

Process candidates in batches:

```python
from ingestion.queue_manager import QueueManager

def process_batch(batch_size: int = 10):
    """Process documents in batches"""

    queue = QueueManager()

    print(f"Starting batch processing (batch_size={batch_size})...")

    while True:
        # Get next batch of candidates
        candidates = queue.get_candidates(limit=batch_size)

        if not candidates:
            print("No more candidates - processing complete")
            break

        print(f"\nProcessing batch of {len(candidates)} documents...")

        # Process each document
        for item in candidates:
            try:
                # Mark as pending
                queue.mark_pending(item.document_id)

                # Process document
                print(f"  Processing {item.document_id}...")
                # ... processing logic ...

                # Mark as processed
                queue.mark_processed(item.document_id, result={'status': 'success'})

            except Exception as e:
                # Mark as failed
                queue.mark_failed(item.document_id, error_message=str(e))
                print(f"  ❌ Failed: {item.document_id}")

        # Show progress
        status = queue.get_status()
        print(f"✅ Batch complete")
        print(f"Remaining candidates: {status['candidates']}")
        print(f"Processed: {status['processed']}")
        print(f"Failed: {status['failed']}")

    print(f"\n✅ All documents processed")

# Run batch processing
process_batch(batch_size=10)
```

## Common Issues and Troubleshooting

### Issue 1: Queue File Not Found

**Symptom**: `FileNotFoundError` when initializing QueueManager

**Solution**:
```python
from pathlib import Path

# Ensure queue directory exists
queue_dir = Path(".aget")
queue_dir.mkdir(parents=True, exist_ok=True)

# Then initialize
queue = QueueManager(queue_file=".aget/queue_state.json")
```

### Issue 2: Document Already in Queue

**Symptom**: `ValueError: Document doc_001 already in queue`

**Solution**: Check if document exists before adding
```python
# Check if document already exists
document_id = "doc_001"
if document_id not in queue.items:
    queue.add_candidate(document_id, path, size_bytes, metadata)
else:
    print(f"Document {document_id} already in queue")
    # Option: Skip or generate new ID
```

## Monitoring Queue Health

```bash
# Create queue monitoring script
cat > monitor_queue.py << 'EOF'
#!/usr/bin/env python3
import sys
sys.path.insert(0, 'src')

from ingestion.queue_manager import QueueManager
import time

def monitor_queue(interval_seconds: int = 60):
    """Monitor queue health"""

    queue = QueueManager()

    while True:
        status = queue.get_status()

        # Display stats
        print(f"\n{'='*50}")
        print(f"Queue Health Report - {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*50}")
        print(f"Total items: {status['total']}")
        print(f"  Candidates: {status['candidates']}")
        print(f"  Pending: {status['pending']}")
        print(f"  Processed: {status['processed']}")
        print(f"  Failed: {status['failed']}")

        if status['total'] > 0:
            print(f"\nCompletion rate: {status['processed']/status['total']*100:.1f}%")
            print(f"Failure rate: {status['failed']/status['total']*100:.1f}%")

        time.sleep(interval_seconds)

if __name__ == "__main__":
    interval = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    monitor_queue(interval)
EOF

chmod +x monitor_queue.py

# Run monitoring (updates every 60 seconds)
python3 monitor_queue.py 60
```

## Related Protocols

- **PROCESSING_PROTOCOL.md** - End-to-end processing workflow
- **BATCH_PROCESSING_PROTOCOL.md** - Batch processing operations

## Configuration References

- `configs/processing_limits.yaml` - Queue size limits and concurrency

## Module References

- `src/ingestion/queue_manager.py` - Queue management implementation
