"""Queue Manager for Document Processing

Manages document processing queues with three states:
- candidates: Documents eligible for processing
- pending: Documents currently being processed
- processed: Documents that have been completed

Based on L208 lines 238-251 (Batch Processing Infrastructure)
"""

from typing import List, Dict, Optional, Set
from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path


class QueueState(Enum):
    """Document queue states"""
    CANDIDATE = "candidate"
    PENDING = "pending"
    PROCESSED = "processed"
    FAILED = "failed"


@dataclass
class DocumentQueueItem:
    """Represents a document in the processing queue"""
    document_id: str
    path: str
    state: QueueState
    size_bytes: int
    added_timestamp: float
    processed_timestamp: Optional[float] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict] = None


class QueueManager:
    """Manages document processing queues

    Provides operations for:
    - Adding documents to candidate queue
    - Moving documents between states
    - Querying queue status
    - Persisting queue state to disk

    Design Decision: File-based queue storage for simplicity and crash recovery.
    For high-volume production use, consider Redis or database-backed queue.
    """

    def __init__(self, queue_file: str = ".aget/queue_state.json"):
        """Initialize queue manager

        Args:
            queue_file: Path to persistent queue state file
        """
        self.queue_file = Path(queue_file)
        self.items: Dict[str, DocumentQueueItem] = {}
        self._load_queue()

    def add_candidate(
        self,
        document_id: str,
        path: str,
        size_bytes: int,
        metadata: Optional[Dict] = None
    ) -> DocumentQueueItem:
        """Add document to candidate queue

        Args:
            document_id: Unique document identifier
            path: Path to document file
            size_bytes: Document size in bytes
            metadata: Optional document metadata

        Returns:
            Created queue item

        Raises:
            ValueError: If document_id already exists in queue
        """
        import time

        if document_id in self.items:
            raise ValueError(f"Document {document_id} already in queue")

        item = DocumentQueueItem(
            document_id=document_id,
            path=path,
            state=QueueState.CANDIDATE,
            size_bytes=size_bytes,
            added_timestamp=time.time(),
            metadata=metadata or {}
        )

        self.items[document_id] = item
        self._save_queue()
        return item

    def mark_pending(self, document_id: str) -> DocumentQueueItem:
        """Mark document as pending (currently processing)

        Args:
            document_id: Document to mark as pending

        Returns:
            Updated queue item

        Raises:
            KeyError: If document not in queue
            ValueError: If document not in candidate state
        """
        item = self.items[document_id]

        if item.state != QueueState.CANDIDATE:
            raise ValueError(f"Document {document_id} not in candidate state (current: {item.state})")

        item.state = QueueState.PENDING
        self._save_queue()
        return item

    def mark_processed(self, document_id: str) -> DocumentQueueItem:
        """Mark document as successfully processed

        Args:
            document_id: Document to mark as processed

        Returns:
            Updated queue item

        Raises:
            KeyError: If document not in queue
        """
        import time

        item = self.items[document_id]
        item.state = QueueState.PROCESSED
        item.processed_timestamp = time.time()
        self._save_queue()
        return item

    def mark_failed(self, document_id: str, error_message: str) -> DocumentQueueItem:
        """Mark document as failed

        Args:
            document_id: Document to mark as failed
            error_message: Error description

        Returns:
            Updated queue item

        Raises:
            KeyError: If document not in queue
        """
        import time

        item = self.items[document_id]
        item.state = QueueState.FAILED
        item.processed_timestamp = time.time()
        item.error_message = error_message
        self._save_queue()
        return item

    def get_candidates(self, limit: Optional[int] = None) -> List[DocumentQueueItem]:
        """Get documents in candidate state

        Args:
            limit: Maximum number of candidates to return (None = all)

        Returns:
            List of candidate documents, sorted by added timestamp
        """
        candidates = [
            item for item in self.items.values()
            if item.state == QueueState.CANDIDATE
        ]
        candidates.sort(key=lambda x: x.added_timestamp)

        if limit:
            return candidates[:limit]
        return candidates

    def get_pending(self) -> List[DocumentQueueItem]:
        """Get documents currently being processed

        Returns:
            List of pending documents
        """
        return [
            item for item in self.items.values()
            if item.state == QueueState.PENDING
        ]

    def get_processed(self) -> List[DocumentQueueItem]:
        """Get successfully processed documents

        Returns:
            List of processed documents
        """
        return [
            item for item in self.items.values()
            if item.state == QueueState.PROCESSED
        ]

    def get_failed(self) -> List[DocumentQueueItem]:
        """Get failed documents

        Returns:
            List of failed documents
        """
        return [
            item for item in self.items.values()
            if item.state == QueueState.FAILED
        ]

    def get_status(self) -> Dict[str, int]:
        """Get queue status summary

        Returns:
            Dictionary with counts by state
        """
        from collections import Counter
        states = [item.state.value for item in self.items.values()]
        counts = Counter(states)

        return {
            "candidates": counts.get(QueueState.CANDIDATE.value, 0),
            "pending": counts.get(QueueState.PENDING.value, 0),
            "processed": counts.get(QueueState.PROCESSED.value, 0),
            "failed": counts.get(QueueState.FAILED.value, 0),
            "total": len(self.items)
        }

    def clear_processed(self) -> int:
        """Remove processed documents from queue

        Returns:
            Number of documents removed
        """
        processed_ids = [
            doc_id for doc_id, item in self.items.items()
            if item.state == QueueState.PROCESSED
        ]

        for doc_id in processed_ids:
            del self.items[doc_id]

        self._save_queue()
        return len(processed_ids)

    def _load_queue(self) -> None:
        """Load queue state from disk"""
        if not self.queue_file.exists():
            return

        try:
            with open(self.queue_file, 'r') as f:
                data = json.load(f)

            for doc_id, item_data in data.items():
                self.items[doc_id] = DocumentQueueItem(
                    document_id=item_data['document_id'],
                    path=item_data['path'],
                    state=QueueState(item_data['state']),
                    size_bytes=item_data['size_bytes'],
                    added_timestamp=item_data['added_timestamp'],
                    processed_timestamp=item_data.get('processed_timestamp'),
                    error_message=item_data.get('error_message'),
                    metadata=item_data.get('metadata', {})
                )
        except Exception as e:
            # If queue file is corrupted, start fresh
            print(f"Warning: Could not load queue state: {e}. Starting with empty queue.")
            self.items = {}

    def _save_queue(self) -> None:
        """Save queue state to disk"""
        self.queue_file.parent.mkdir(parents=True, exist_ok=True)

        data = {
            doc_id: {
                'document_id': item.document_id,
                'path': item.path,
                'state': item.state.value,
                'size_bytes': item.size_bytes,
                'added_timestamp': item.added_timestamp,
                'processed_timestamp': item.processed_timestamp,
                'error_message': item.error_message,
                'metadata': item.metadata
            }
            for doc_id, item in self.items.items()
        }

        with open(self.queue_file, 'w') as f:
            json.dump(data, f, indent=2)
