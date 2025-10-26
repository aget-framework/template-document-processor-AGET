"""Rollback Management for Document Processing

Enables rolling back to previous versions when:
- Processing errors occur
- Output validation fails
- User requests revert

Based on L208 lines 247-251 (Validation Pipeline - Rollback capabilities)
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import time


class RollbackReason(Enum):
    """Reasons for rollback"""
    VALIDATION_FAILED = "validation_failed"
    PROCESSING_ERROR = "processing_error"
    USER_REQUESTED = "user_requested"
    QUALITY_ISSUE = "quality_issue"
    SECURITY_CONCERN = "security_concern"


@dataclass
class RollbackRecord:
    """Record of a rollback operation"""
    rollback_id: str
    document_id: str
    from_version_id: str
    to_version_id: str
    reason: RollbackReason
    timestamp: float
    success: bool
    error_message: Optional[str] = None
    metadata: Optional[Dict] = None


class RollbackManager:
    """Manages rollback operations for document processing

    Provides:
    - Version rollback with audit trail
    - Dry-run mode to preview rollback
    - Rollback history tracking
    - Batch rollback support

    Design Decision: Rollback doesn't delete versions, it creates
    a new version with previous content. This preserves full history.

    Based on L208 lines 1021-1031 (Rollback Protocol)
    """

    def __init__(self, version_manager, publisher):
        """Initialize rollback manager

        Args:
            version_manager: VersionManager instance for version operations
            publisher: Publisher instance for re-publishing after rollback
        """
        self.version_manager = version_manager
        self.publisher = publisher
        self.rollback_history: List[RollbackRecord] = []

    def rollback_document(
        self,
        document_id: str,
        target_version_id: Optional[str] = None,
        reason: RollbackReason = RollbackReason.USER_REQUESTED,
        dry_run: bool = False
    ) -> RollbackRecord:
        """Roll back document to a previous version

        Args:
            document_id: Document to roll back
            target_version_id: Version to roll back to (if None, uses previous version)
            reason: Reason for rollback
            dry_run: If True, simulate rollback without executing

        Returns:
            RollbackRecord with outcome
        """
        import hashlib

        # Get current version
        current_version = self.version_manager.get_latest_version(document_id)

        if not current_version:
            return RollbackRecord(
                rollback_id=self._generate_rollback_id(document_id),
                document_id=document_id,
                from_version_id="",
                to_version_id="",
                reason=reason,
                timestamp=time.time(),
                success=False,
                error_message="No current version found"
            )

        # Determine target version
        if target_version_id:
            target_version = self.version_manager.get_version(target_version_id)
        else:
            # Roll back to previous version
            target_version = self._get_previous_version(document_id, current_version.version_id)

        if not target_version:
            return RollbackRecord(
                rollback_id=self._generate_rollback_id(document_id),
                document_id=document_id,
                from_version_id=current_version.version_id,
                to_version_id="",
                reason=reason,
                timestamp=time.time(),
                success=False,
                error_message="Target version not found"
            )

        # Check if already at target version
        if current_version.version_id == target_version.version_id:
            return RollbackRecord(
                rollback_id=self._generate_rollback_id(document_id),
                document_id=document_id,
                from_version_id=current_version.version_id,
                to_version_id=target_version.version_id,
                reason=reason,
                timestamp=time.time(),
                success=False,
                error_message="Already at target version"
            )

        rollback_id = self._generate_rollback_id(document_id)

        if dry_run:
            # Simulate rollback
            return RollbackRecord(
                rollback_id=rollback_id,
                document_id=document_id,
                from_version_id=current_version.version_id,
                to_version_id=target_version.version_id,
                reason=reason,
                timestamp=time.time(),
                success=True,
                metadata={'dry_run': True, 'simulated': True}
            )

        # Execute rollback
        try:
            # Create new version with target content
            new_version = self.version_manager.create_version(
                document_id=document_id,
                content=target_version.content,
                processing_metadata={
                    'rollback': True,
                    'rollback_id': rollback_id,
                    'rollback_from': current_version.version_id,
                    'rollback_to': target_version.version_id,
                    'rollback_reason': reason.value,
                    'original_metadata': target_version.processing_metadata
                },
                parent_version_id=current_version.version_id
            )

            # Re-publish if publisher available
            if self.publisher:
                publish_results = self.publisher.publish(
                    document_id=document_id,
                    content=target_version.content,
                    metadata={'rollback': True, 'rollback_id': rollback_id}
                )

                # Check if publishing succeeded
                publish_success = all(r.success for r in publish_results)
            else:
                publish_success = True  # No publisher, consider success

            record = RollbackRecord(
                rollback_id=rollback_id,
                document_id=document_id,
                from_version_id=current_version.version_id,
                to_version_id=new_version.version_id,
                reason=reason,
                timestamp=time.time(),
                success=publish_success,
                metadata={
                    'target_version': target_version.version_id,
                    'new_version': new_version.version_id
                }
            )

            self.rollback_history.append(record)
            return record

        except Exception as e:
            record = RollbackRecord(
                rollback_id=rollback_id,
                document_id=document_id,
                from_version_id=current_version.version_id,
                to_version_id=target_version.version_id,
                reason=reason,
                timestamp=time.time(),
                success=False,
                error_message=str(e)
            )

            self.rollback_history.append(record)
            return record

    def rollback_batch(
        self,
        batch_id: str,
        reason: RollbackReason = RollbackReason.PROCESSING_ERROR,
        dry_run: bool = False
    ) -> List[RollbackRecord]:
        """Roll back a batch of documents

        Args:
            batch_id: Batch identifier
            reason: Reason for rollback
            dry_run: If True, simulate rollback

        Returns:
            List of rollback records
        """
        # This would need batch tracking to know which documents were in a batch
        # For now, stub implementation
        # In production, integrate with batch_processor.py to track batches

        return []

    def get_rollback_history(
        self,
        document_id: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[RollbackRecord]:
        """Get rollback history

        Args:
            document_id: Filter by document ID (optional)
            limit: Maximum results to return (optional)

        Returns:
            List of rollback records
        """
        if document_id:
            history = [
                r for r in self.rollback_history
                if r.document_id == document_id
            ]
        else:
            history = self.rollback_history

        # Sort by timestamp, most recent first
        history.sort(key=lambda r: r.timestamp, reverse=True)

        if limit:
            return history[:limit]
        return history

    def _get_previous_version(
        self,
        document_id: str,
        current_version_id: str
    ) -> Optional[Any]:
        """Get the version before current

        Args:
            document_id: Document identifier
            current_version_id: Current version ID

        Returns:
            Previous version or None
        """
        versions = self.version_manager.get_version_history(document_id)

        if len(versions) < 2:
            return None

        # Find current version index
        current_index = None
        for i, v in enumerate(versions):
            if v.version_id == current_version_id:
                current_index = i
                break

        if current_index is None or current_index == 0:
            return None

        # Return previous version
        return versions[current_index - 1]

    def _generate_rollback_id(self, document_id: str) -> str:
        """Generate unique rollback ID

        Args:
            document_id: Document identifier

        Returns:
            Rollback ID
        """
        import hashlib
        timestamp = str(time.time())
        unique_str = f"rollback_{document_id}_{timestamp}"
        return hashlib.sha256(unique_str.encode()).hexdigest()[:16]
