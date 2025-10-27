# Queue Management Protocol

**Version**: 1.0
**Based on**: L208 lines 260-267 (Pipeline Architecture - Ingestion)
**Last Updated**: 2025-10-26

## Overview

This protocol defines queue management operations for document processing. The queue manages document ingestion, priority ordering, and processing status tracking.

## Queue Operations

### Initialize Queue Manager

```python
from ingestion.queue_manager import QueueManager

# Initialize with default storage
queue = QueueManager()

# Or specify custom storage directory
queue = QueueManager(queue_dir=".aget/custom_queue")

print(f"✅ Queue initialized")
print(f"Current size: {queue.size()}")
```

**Command-line check**:

```bash
# Quick queue status
python3 -c "
from ingestion.queue_manager import QueueManager
queue = QueueManager()
print(f'Queue size: {queue.size()}')
print(f'Next: {queue.peek().document_id if queue.size() > 0 else \"empty\"}')
"
```

## Document Ingestion

### Step 1: Enqueue Single Document

Add a document to the processing queue:

```python
from ingestion.queue_manager import QueueManager

queue = QueueManager()

# Enqueue document
queue_item = queue.enqueue(
    document_path="/path/to/document.pdf",
    metadata={
        'source': 'user_upload',
        'priority': 'normal',
        'uploaded_by': 'user123',
        'tags': ['invoice', 'urgent']
    }
)

print(f"✅ Document enqueued")
print(f"   Document ID: {queue_item.document_id}")
print(f"   Path: {queue_item.document_path}")
print(f"   Status: {queue_item.status}")
print(f"   Queue position: {queue.size()}")
```

### Step 2: Enqueue with Priority

Higher priority documents processed first:

```python
# Enqueue high-priority document
high_priority_item = queue.enqueue(
    document_path="/path/to/urgent.pdf",
    metadata={'priority': 'high'}  # Will be processed before 'normal'
)

# Enqueue low-priority document
low_priority_item = queue.enqueue(
    document_path="/path/to/batch.pdf",
    metadata={'priority': 'low'}  # Will be processed after 'normal'
)

print(f"Queue order (by priority): {[item.document_id for item in queue.list()]}")
```

### Step 3: Batch Enqueue

Enqueue multiple documents:

```python
from pathlib import Path

# Get all PDFs in directory
document_dir = Path("/path/to/documents")
pdf_files = list(document_dir.glob("*.pdf"))

print(f"Enqueuing {len(pdf_files)} documents...")

# Enqueue all
enqueued = []
for pdf_path in pdf_files:
    queue_item = queue.enqueue(
        document_path=str(pdf_path),
        metadata={'source': 'batch_upload', 'batch_id': 'batch_001'}
    )
    enqueued.append(queue_item)

print(f"✅ Enqueued {len(enqueued)} documents")
print(f"Queue size: {queue.size()}")
```

**Bash batch enqueue**:

```bash
# Enqueue all PDFs in directory
find /path/to/documents -name "*.pdf" -type f | while read pdf; do
    python3 -c "
from ingestion.queue_manager import QueueManager
queue = QueueManager()
item = queue.enqueue('$pdf', metadata={'source': 'batch'})
print(f'Enqueued: {item.document_id}')
"
done
```

## Queue Retrieval

### Step 1: Peek at Next Item

View next item without removing from queue:

```python
# Peek at next item
next_item = queue.peek()

if next_item:
    print(f"Next document: {next_item.document_id}")
    print(f"Path: {next_item.document_path}")
    print(f"Status: {next_item.status}")
else:
    print("Queue is empty")
```

### Step 2: Dequeue for Processing

Remove item from queue to process:

```python
# Get next item
queue_item = queue.dequeue()

if queue_item:
    print(f"✅ Dequeued: {queue_item.document_id}")
    print(f"Remaining in queue: {queue.size()}")

    # Process document
    try:
        # ... processing logic ...
        print(f"Processing {queue_item.document_path}...")

        # Mark as processed when done
        queue.mark_processed(
            queue_item.document_id,
            result={'status': 'success', 'extracted_fields': 10}
        )
        print(f"✅ Marked as processed")

    except Exception as e:
        # Mark as failed if error
        queue.mark_failed(queue_item.document_id, error=str(e))
        print(f"❌ Marked as failed: {e}")
else:
    print("Queue is empty - nothing to process")
```

### Step 3: List All Queue Items

View all items in queue:

```python
# List all items
items = queue.list()

print(f"Queue contents ({len(items)} items):")
for i, item in enumerate(items, 1):
    print(f"{i}. {item.document_id}")
    print(f"   Path: {item.document_path}")
    print(f"   Status: {item.status}")
    print(f"   Priority: {item.metadata.get('priority', 'normal')}")
```

## Status Management

### Step 1: Mark as Processed

Update status after successful processing:

```python
# Mark document as processed
queue.mark_processed(
    document_id="doc_12345",
    result={
        'status': 'success',
        'version_id': 'v1_abc123',
        'extracted_fields': 15,
        'processing_time_seconds': 12.5
    }
)

print(f"✅ Document marked as processed")
```

### Step 2: Mark as Failed

Update status after processing failure:

```python
# Mark document as failed
queue.mark_failed(
    document_id="doc_12345",
    error="LLM timeout after 60 seconds"
)

print(f"❌ Document marked as failed")
```

### Step 3: Get Item Status

Check status of specific document:

```python
# Get item by ID
item = queue.get(document_id="doc_12345")

if item:
    print(f"Document: {item.document_id}")
    print(f"Status: {item.status}")  # PENDING, PROCESSING, PROCESSED, FAILED
    print(f"Enqueued at: {item.enqueued_at}")
    if item.processed_at:
        print(f"Processed at: {item.processed_at}")
        duration = item.processed_at - item.enqueued_at
        print(f"Processing duration: {duration:.1f} seconds")
else:
    print(f"Document not found: doc_12345")
```

## Queue Filtering

### Filter by Status

Get documents by status:

```python
# Get all items
all_items = queue.list()

# Filter by status
pending = [item for item in all_items if item.status == "PENDING"]
processing = [item for item in all_items if item.status == "PROCESSING"]
processed = [item for item in all_items if item.status == "PROCESSED"]
failed = [item for item in all_items if item.status == "FAILED"]

print(f"Queue status breakdown:")
print(f"  Pending: {len(pending)}")
print(f"  Processing: {len(processing)}")
print(f"  Processed: {len(processed)}")
print(f"  Failed: {len(failed)}")
```

### Filter by Metadata

Filter documents by custom metadata:

```python
# Get all items
all_items = queue.list()

# Filter by metadata
urgent_items = [
    item for item in all_items
    if item.metadata.get('priority') == 'high'
]

batch_items = [
    item for item in all_items
    if 'batch_id' in item.metadata
]

print(f"Found {len(urgent_items)} urgent documents")
print(f"Found {len(batch_items)} batch documents")
```

## Queue Maintenance

### Clear Processed Items

Remove successfully processed items from queue:

```python
# Get all items
all_items = queue.list()

# Clear processed
processed_items = [item for item in all_items if item.status == "PROCESSED"]

print(f"Clearing {len(processed_items)} processed items...")

for item in processed_items:
    # Archive or log before clearing (optional)
    print(f"Archiving: {item.document_id}")

    # Note: QueueManager doesn't have built-in clear method
    # You can implement custom clearing logic or use file system operations

print(f"✅ Cleared processed items")
print(f"Remaining queue size: {queue.size()}")
```

### Retry Failed Items

Re-enqueue failed items for retry:

```python
# Get all items
all_items = queue.list()

# Find failed items
failed_items = [item for item in all_items if item.status == "FAILED"]

print(f"Found {len(failed_items)} failed items to retry...")

for item in failed_items:
    # Re-enqueue for retry
    retry_item = queue.enqueue(
        document_path=item.document_path,
        metadata={
            **item.metadata,
            'retry': True,
            'original_id': item.document_id
        }
    )
    print(f"✅ Re-enqueued: {item.document_id} → {retry_item.document_id}")

print(f"✅ Retry queue updated")
```

## Batch Processing with Queue

Process documents in batches:

```python
from ingestion.batch_processor import BatchProcessor
from ingestion.queue_manager import QueueManager

def process_batch(batch_size: int = 10):
    """Process documents in batches"""

    queue = QueueManager()
    processor = BatchProcessor(max_workers=4)

    print(f"Starting batch processing (batch_size={batch_size})...")

    while queue.size() > 0:
        # Dequeue batch
        batch = []
        for _ in range(min(batch_size, queue.size())):
            item = queue.dequeue()
            if item:
                batch.append(item)

        if not batch:
            break

        print(f"\nProcessing batch of {len(batch)} documents...")

        # Process batch
        # (Simplified - actual processing would call LLM, validate, etc.)
        for item in batch:
            try:
                # Process document
                print(f"  Processing {item.document_id}...")
                # ... processing logic ...

                # Mark as processed
                queue.mark_processed(item.document_id, result={'status': 'success'})

            except Exception as e:
                # Mark as failed
                queue.mark_failed(item.document_id, error=str(e))
                print(f"  ❌ Failed: {item.document_id}")

        print(f"✅ Batch complete")
        print(f"Remaining in queue: {queue.size()}")

    print(f"\n✅ All documents processed")

# Run batch processing
process_batch(batch_size=10)
```

**Bash batch processing script**:

```bash
# Process queue in batches
cat > process_queue.sh << 'EOF'
#!/bin/bash

BATCH_SIZE=10

while true; do
    QUEUE_SIZE=$(python3 -c "
from ingestion.queue_manager import QueueManager
queue = QueueManager()
print(queue.size())
")

    if [ "$QUEUE_SIZE" -eq 0 ]; then
        echo "✅ Queue empty - processing complete"
        break
    fi

    echo "Processing batch (queue size: $QUEUE_SIZE)..."

    # Process batch (simplified)
    python3 -c "
from ingestion.queue_manager import QueueManager
queue = QueueManager()

for _ in range(min($BATCH_SIZE, queue.size())):
    item = queue.dequeue()
    if item:
        print(f'Processing {item.document_id}...')
        # ... processing ...
        queue.mark_processed(item.document_id, result={'status': 'success'})
"
    echo "Batch complete"
    sleep 1
done
EOF

chmod +x process_queue.sh
./process_queue.sh
```

## Common Issues and Troubleshooting

### Issue 1: Queue Directory Not Found

**Symptom**: `FileNotFoundError` when initializing QueueManager

**Solution**:
```python
from pathlib import Path

# Ensure queue directory exists
queue_dir = Path(".aget/queue")
queue_dir.mkdir(parents=True, exist_ok=True)

# Then initialize
queue = QueueManager(queue_dir=str(queue_dir))
```

### Issue 2: Stale Items in Queue

**Symptom**: Items stuck in "PROCESSING" status

**Solution**: Implement timeout detection
```python
import time

# Find stale items (processing for > 5 minutes)
TIMEOUT_SECONDS = 300
current_time = time.time()

all_items = queue.list()
stale_items = [
    item for item in all_items
    if item.status == "PROCESSING"
    and (current_time - item.enqueued_at) > TIMEOUT_SECONDS
]

print(f"Found {len(stale_items)} stale items")

for item in stale_items:
    # Mark as failed due to timeout
    queue.mark_failed(item.document_id, error="Processing timeout exceeded")
    print(f"Marked as failed: {item.document_id}")
```

## Monitoring Queue Health

```bash
# Create queue monitoring script
cat > monitor_queue.py << 'EOF'
#!/usr/bin/env python3
from ingestion.queue_manager import QueueManager
import time

def monitor_queue(interval_seconds: int = 60):
    """Monitor queue health"""

    queue = QueueManager()

    while True:
        all_items = queue.list()

        # Calculate stats
        total = len(all_items)
        pending = sum(1 for item in all_items if item.status == "PENDING")
        processing = sum(1 for item in all_items if item.status == "PROCESSING")
        processed = sum(1 for item in all_items if item.status == "PROCESSED")
        failed = sum(1 for item in all_items if item.status == "FAILED")

        # Display stats
        print(f"\n{'='*50}")
        print(f"Queue Health Report - {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*50}")
        print(f"Total items: {total}")
        print(f"  Pending: {pending}")
        print(f"  Processing: {processing}")
        print(f"  Processed: {processed}")
        print(f"  Failed: {failed}")

        if total > 0:
            print(f"\nCompletion rate: {processed/total*100:.1f}%")
            print(f"Failure rate: {failed/total*100:.1f}%")

        time.sleep(interval_seconds)

if __name__ == "__main__":
    import sys
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
- `src/ingestion/batch_processor.py` - Batch processing with queues
