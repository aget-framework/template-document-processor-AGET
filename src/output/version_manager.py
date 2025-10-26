"""Version Management for Document Processing

Tracks versions of processed documents to enable:
- Version history
- Comparison between versions
- Rollback to previous versions
- Audit trail

Based on L208 lines 200-227 (Idempotence & Reproducibility - Version Management)
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import json
import time
import hashlib


@dataclass
class DocumentVersion:
    """Represents a version of a processed document"""
    version_id: str
    document_id: str
    content: Any
    timestamp: float
    processing_metadata: Dict
    content_hash: str
    parent_version_id: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary

        Returns:
            Dictionary representation
        """
        return asdict(self)


class VersionManager:
    """Manages document versions with history and rollback support

    Design Decision: File-based version storage for simplicity.
    Each version is stored as a separate file with metadata.

    Based on L208 lines 200-227 (Version Management)
    """

    def __init__(self, versions_dir: str = ".aget/versions"):
        """Initialize version manager

        Args:
            versions_dir: Directory for version storage
        """
        self.versions_dir = Path(versions_dir)
        self.versions_dir.mkdir(parents=True, exist_ok=True)
        self._index: Dict[str, List[str]] = {}  # document_id -> [version_ids]
        self._load_index()

    def create_version(
        self,
        document_id: str,
        content: Any,
        processing_metadata: Dict,
        parent_version_id: Optional[str] = None
    ) -> DocumentVersion:
        """Create a new document version

        Args:
            document_id: Document identifier
            content: Processed content
            processing_metadata: Metadata about processing (model, prompt version, etc.)
            parent_version_id: ID of parent version (if updating)

        Returns:
            Created DocumentVersion

        Example processing_metadata (from L208:207-227):
            {
                'timestamp': '2025-10-26T10:30:00Z',
                'prompt_version': 'extraction_v2.1',
                'model': 'gpt-4o-2024-08-06',
                'temperature': 0.0,
                'seed': 42,
                'cost_usd': 0.023,
                'latency_ms': 1234
            }
        """
        # Generate version ID
        version_id = self._generate_version_id(document_id)

        # Calculate content hash
        content_hash = self._hash_content(content)

        # Create version object
        version = DocumentVersion(
            version_id=version_id,
            document_id=document_id,
            content=content,
            timestamp=time.time(),
            processing_metadata=processing_metadata,
            content_hash=content_hash,
            parent_version_id=parent_version_id
        )

        # Save version
        self._save_version(version)

        # Update index
        if document_id not in self._index:
            self._index[document_id] = []
        self._index[document_id].append(version_id)
        self._save_index()

        return version

    def get_version(self, version_id: str) -> Optional[DocumentVersion]:
        """Retrieve a specific version

        Args:
            version_id: Version identifier

        Returns:
            DocumentVersion if found, None otherwise
        """
        version_file = self.versions_dir / f"{version_id}.json"

        if not version_file.exists():
            return None

        try:
            with open(version_file, 'r') as f:
                data = json.load(f)
            return DocumentVersion(**data)
        except Exception as e:
            print(f"Warning: Could not load version {version_id}: {e}")
            return None

    def get_latest_version(self, document_id: str) -> Optional[DocumentVersion]:
        """Get latest version of a document

        Args:
            document_id: Document identifier

        Returns:
            Latest DocumentVersion if exists, None otherwise
        """
        versions = self.get_version_history(document_id)
        if not versions:
            return None

        # Sort by timestamp, return most recent
        versions.sort(key=lambda v: v.timestamp, reverse=True)
        return versions[0]

    def get_version_history(self, document_id: str) -> List[DocumentVersion]:
        """Get all versions of a document

        Args:
            document_id: Document identifier

        Returns:
            List of DocumentVersion objects, sorted by timestamp
        """
        if document_id not in self._index:
            return []

        versions = []
        for version_id in self._index[document_id]:
            version = self.get_version(version_id)
            if version:
                versions.append(version)

        versions.sort(key=lambda v: v.timestamp)
        return versions

    def compare_versions(
        self,
        version_id_1: str,
        version_id_2: str
    ) -> Dict[str, Any]:
        """Compare two versions

        Args:
            version_id_1: First version ID
            version_id_2: Second version ID

        Returns:
            Dictionary with comparison results
        """
        v1 = self.get_version(version_id_1)
        v2 = self.get_version(version_id_2)

        if not v1 or not v2:
            return {'error': 'One or both versions not found'}

        return {
            'same_document': v1.document_id == v2.document_id,
            'content_changed': v1.content_hash != v2.content_hash,
            'time_diff_seconds': abs(v1.timestamp - v2.timestamp),
            'version_1': {
                'id': v1.version_id,
                'timestamp': v1.timestamp,
                'content_hash': v1.content_hash,
                'metadata': v1.processing_metadata
            },
            'version_2': {
                'id': v2.version_id,
                'timestamp': v2.timestamp,
                'content_hash': v2.content_hash,
                'metadata': v2.processing_metadata
            }
        }

    def delete_version(self, version_id: str) -> bool:
        """Delete a specific version

        Args:
            version_id: Version to delete

        Returns:
            True if deleted, False if not found
        """
        version_file = self.versions_dir / f"{version_id}.json"

        if not version_file.exists():
            return False

        try:
            # Remove file
            version_file.unlink()

            # Update index
            for doc_id, versions in self._index.items():
                if version_id in versions:
                    versions.remove(version_id)
                    self._save_index()
                    break

            return True
        except Exception as e:
            print(f"Warning: Could not delete version {version_id}: {e}")
            return False

    def _generate_version_id(self, document_id: str) -> str:
        """Generate unique version ID

        Args:
            document_id: Document identifier

        Returns:
            Version ID (format: doc_id_timestamp_hash)
        """
        timestamp = str(time.time())
        unique_str = f"{document_id}_{timestamp}"
        hash_suffix = hashlib.sha256(unique_str.encode()).hexdigest()[:8]
        return f"{document_id}_v{int(time.time())}_{hash_suffix}"

    def _hash_content(self, content: Any) -> str:
        """Calculate hash of content

        Args:
            content: Content to hash

        Returns:
            SHA-256 hash
        """
        # Convert content to string representation
        content_str = json.dumps(content, sort_keys=True) if isinstance(content, dict) else str(content)
        return hashlib.sha256(content_str.encode()).hexdigest()

    def _save_version(self, version: DocumentVersion) -> None:
        """Save version to disk

        Args:
            version: Version to save
        """
        version_file = self.versions_dir / f"{version.version_id}.json"

        try:
            with open(version_file, 'w') as f:
                json.dump(version.to_dict(), f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save version {version.version_id}: {e}")

    def _load_index(self) -> None:
        """Load version index from disk"""
        index_file = self.versions_dir / "_index.json"

        if not index_file.exists():
            return

        try:
            with open(index_file, 'r') as f:
                self._index = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load version index: {e}")
            self._index = {}

    def _save_index(self) -> None:
        """Save version index to disk"""
        index_file = self.versions_dir / "_index.json"

        try:
            with open(index_file, 'w') as f:
                json.dump(self._index, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save version index: {e}")
