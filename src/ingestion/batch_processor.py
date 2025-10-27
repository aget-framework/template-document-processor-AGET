"""Batch Processing Coordinator

Coordinates batch processing of multiple documents with:
- Progress tracking
- Error handling
- Dry-run mode
- Status reporting

Based on L208 lines 238-251 (Batch Processing Infrastructure)
"""

from typing import List, Dict, Callable, Optional, Iterator
from dataclasses import dataclass
from enum import Enum
import time


class BatchStatus(Enum):
    """Batch processing status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BatchResult:
    """Result of processing a single document in batch"""
    document_id: str
    success: bool
    processing_time: float
    error_message: Optional[str] = None
    result_data: Optional[Dict] = None


@dataclass
class BatchProgress:
    """Batch processing progress"""
    batch_id: str
    status: BatchStatus
    total: int
    processed: int
    completed: int  # Renamed from 'succeeded' for API consistency
    failed: int
    start_time: float
    end_time: Optional[float] = None

    @property
    def progress_percent(self) -> float:
        """Calculate completion percentage (renamed from percent_complete for API consistency)"""
        if self.total == 0:
            return 100.0
        return (self.processed / self.total) * 100

    @property
    def elapsed_time(self) -> float:
        """Calculate elapsed time in seconds"""
        end = self.end_time or time.time()
        return end - self.start_time

    @property
    def estimated_remaining(self) -> Optional[float]:
        """Estimate remaining time in seconds"""
        if self.processed == 0:
            return None

        time_per_doc = self.elapsed_time / self.processed
        remaining_docs = self.total - self.processed
        return time_per_doc * remaining_docs


class BatchProcessor:
    """Coordinates batch processing of documents

    Provides:
    - Sequential processing of document batches
    - Progress tracking and reporting
    - Dry-run mode (preview without execution)
    - Error handling with graceful degradation
    - Cancellation support

    Design Decision: Sequential processing by default.
    For parallel processing, see src/pipeline/task_decomposer.py
    """

    def __init__(
        self,
        batch_id: str,
        dry_run: bool = False,
        stop_on_failure: bool = False
    ):
        """Initialize batch processor

        Args:
            batch_id: Unique identifier for this batch
            dry_run: If True, simulate processing without executing
            stop_on_failure: If True, stop batch on first failure
        """
        self.batch_id = batch_id
        self.dry_run = dry_run
        self.stop_on_failure = stop_on_failure
        self._cancelled = False

    def process_batch(
        self,
        documents: List[str],
        processor_func: Callable[[str], Dict],
        on_progress: Optional[Callable[[BatchProgress], None]] = None
    ) -> BatchProgress:
        """Process a batch of documents

        Args:
            documents: List of document IDs to process
            processor_func: Function that processes a single document
                           Should accept document_id and return result dict
            on_progress: Optional callback for progress updates
                        Called after each document is processed

        Returns:
            BatchProgress with final results
        """
        progress = BatchProgress(
            batch_id=self.batch_id,
            status=BatchStatus.RUNNING,
            total=len(documents),
            processed=0,
            completed=0,
            failed=0,
            start_time=time.time()
        )

        results: List[BatchResult] = []

        try:
            for doc_id in documents:
                if self._cancelled:
                    progress.status = BatchStatus.CANCELLED
                    break

                # Process document
                result = self._process_document(doc_id, processor_func)
                results.append(result)

                # Update progress
                progress.processed += 1
                if result.success:
                    progress.completed += 1
                else:
                    progress.failed += 1

                # Call progress callback
                if on_progress:
                    on_progress(progress)

                # Stop on failure if configured
                if not result.success and self.stop_on_failure:
                    progress.status = BatchStatus.FAILED
                    break

            # Final status
            if progress.status == BatchStatus.RUNNING:
                progress.status = BatchStatus.COMPLETED

        except Exception as e:
            progress.status = BatchStatus.FAILED
            # Add error to last processed document
            if results:
                results[-1].error_message = f"Batch failed: {e}"
        finally:
            progress.end_time = time.time()

        return progress

    def process_batch_generator(
        self,
        documents: List[str],
        processor_func: Callable[[str], Dict]
    ) -> Iterator[BatchResult]:
        """Process batch with generator pattern

        Yields results as documents are processed, allowing
        for streaming/incremental processing.

        Args:
            documents: List of document IDs to process
            processor_func: Function that processes a single document

        Yields:
            BatchResult for each processed document
        """
        for doc_id in documents:
            if self._cancelled:
                break

            result = self._process_document(doc_id, processor_func)
            yield result

            if not result.success and self.stop_on_failure:
                break

    def _process_document(
        self,
        document_id: str,
        processor_func: Callable[[str], Dict]
    ) -> BatchResult:
        """Process a single document

        Args:
            document_id: Document to process
            processor_func: Processing function

        Returns:
            BatchResult for this document
        """
        start_time = time.time()

        try:
            if self.dry_run:
                # Simulate processing in dry-run mode
                result_data = {
                    'dry_run': True,
                    'document_id': document_id,
                    'simulated': True
                }
                success = True
                error_message = None
            else:
                # Actually process document
                result_data = processor_func(document_id)
                success = True
                error_message = None

        except Exception as e:
            result_data = None
            success = False
            error_message = str(e)

        processing_time = time.time() - start_time

        return BatchResult(
            document_id=document_id,
            success=success,
            processing_time=processing_time,
            error_message=error_message,
            result_data=result_data
        )

    def cancel(self) -> None:
        """Cancel batch processing

        Processing will stop after current document completes.
        """
        self._cancelled = True

    @staticmethod
    def create_dry_run(batch_id: str) -> 'BatchProcessor':
        """Create a dry-run batch processor

        Args:
            batch_id: Batch identifier

        Returns:
            BatchProcessor configured for dry-run mode
        """
        return BatchProcessor(batch_id=batch_id, dry_run=True)

    @staticmethod
    def estimate_time(
        document_count: int,
        avg_time_per_doc: float
    ) -> Dict[str, float]:
        """Estimate batch processing time

        Args:
            document_count: Number of documents in batch
            avg_time_per_doc: Average processing time per document (seconds)

        Returns:
            Dictionary with time estimates (total_seconds, total_minutes, total_hours)
        """
        total_seconds = document_count * avg_time_per_doc

        return {
            'total_seconds': total_seconds,
            'total_minutes': total_seconds / 60,
            'total_hours': total_seconds / 3600,
            'documents': document_count,
            'avg_per_document': avg_time_per_doc
        }
