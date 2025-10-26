"""LLM Response Caching

Implements caching for LLM responses to:
- Reduce API costs
- Improve response times
- Ensure reproducibility
- Enable crash recovery

Based on L208 lines 92-192 (Idempotence & Reproducibility - LLM Response Caching)
"""

from typing import Dict, Optional, Any
import hashlib
import json
import time
from pathlib import Path
from dataclasses import dataclass, asdict


@dataclass
class CacheEntry:
    """Cached LLM response"""
    key: str
    prompt: str
    model: str
    temperature: float
    response: str
    created_at: float
    hit_count: int = 0
    metadata: Optional[Dict] = None

    def is_expired(self, ttl_seconds: int) -> bool:
        """Check if cache entry has expired

        Args:
            ttl_seconds: Time-to-live in seconds

        Returns:
            True if expired
        """
        age = time.time() - self.created_at
        return age > ttl_seconds


class CacheManager:
    """Manages LLM response caching

    Design Decision: File-based cache for simplicity and persistence.
    For production, consider Redis or database backend for:
    - Better performance (faster lookups)
    - Distributed caching (multiple workers)
    - Built-in TTL management
    - Memory limits

    Based on L208 lines 108-149 (Caching Strategy implementation)
    """

    def __init__(
        self,
        cache_dir: str = ".aget/cache",
        ttl_seconds: int = 86400,  # 24 hours default
        enabled: bool = True
    ):
        """Initialize cache manager

        Args:
            cache_dir: Directory for cache storage
            ttl_seconds: Time-to-live for cache entries (seconds)
            enabled: Whether caching is enabled
        """
        self.cache_dir = Path(cache_dir)
        self.ttl_seconds = ttl_seconds
        self.enabled = enabled
        self._cache: Dict[str, CacheEntry] = {}

        if self.enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self._load_cache()

    def get_cache_key(
        self,
        prompt: str,
        model: str,
        temperature: float = 0.0,
        max_tokens: int = 1000,
        seed: Optional[int] = None
    ) -> str:
        """Generate deterministic cache key

        Based on L208 lines 117-127 (Cache key generation)

        Args:
            prompt: LLM prompt
            model: Model name
            temperature: Temperature parameter
            max_tokens: Max tokens parameter
            seed: Random seed (if any)

        Returns:
            SHA-256 hash of inputs
        """
        # Create deterministic representation
        cache_input = {
            'prompt': prompt,
            'model': model,
            'temperature': temperature,
            'max_tokens': max_tokens,
            'seed': seed
        }

        # Serialize to JSON (sorted keys for determinism)
        key_str = json.dumps(cache_input, sort_keys=True)

        # Generate hash
        return hashlib.sha256(key_str.encode()).hexdigest()

    def get(
        self,
        prompt: str,
        model: str,
        temperature: float = 0.0,
        max_tokens: int = 1000,
        seed: Optional[int] = None
    ) -> Optional[str]:
        """Get cached response if available

        Args:
            prompt: LLM prompt
            model: Model name
            temperature: Temperature parameter
            max_tokens: Max tokens parameter
            seed: Random seed

        Returns:
            Cached response if found and not expired, None otherwise
        """
        if not self.enabled:
            return None

        key = self.get_cache_key(prompt, model, temperature, max_tokens, seed)

        if key not in self._cache:
            return None

        entry = self._cache[key]

        # Check expiration
        if entry.is_expired(self.ttl_seconds):
            # Remove expired entry
            del self._cache[key]
            self._remove_cache_file(key)
            return None

        # Update hit count
        entry.hit_count += 1
        self._save_entry(entry)

        return entry.response

    def set(
        self,
        prompt: str,
        model: str,
        response: str,
        temperature: float = 0.0,
        max_tokens: int = 1000,
        seed: Optional[int] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """Cache LLM response

        Args:
            prompt: LLM prompt
            model: Model name
            response: LLM response to cache
            temperature: Temperature parameter
            max_tokens: Max tokens parameter
            seed: Random seed
            metadata: Optional metadata to store with entry

        Returns:
            Cache key
        """
        if not self.enabled:
            return ""

        key = self.get_cache_key(prompt, model, temperature, max_tokens, seed)

        entry = CacheEntry(
            key=key,
            prompt=prompt,
            model=model,
            temperature=temperature,
            response=response,
            created_at=time.time(),
            hit_count=0,
            metadata=metadata
        )

        self._cache[key] = entry
        self._save_entry(entry)

        return key

    def clear(self) -> int:
        """Clear all cache entries

        Returns:
            Number of entries cleared
        """
        count = len(self._cache)
        self._cache.clear()

        # Remove all cache files
        if self.cache_dir.exists():
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()

        return count

    def clear_expired(self) -> int:
        """Remove expired cache entries

        Returns:
            Number of entries removed
        """
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.is_expired(self.ttl_seconds)
        ]

        for key in expired_keys:
            del self._cache[key]
            self._remove_cache_file(key)

        return len(expired_keys)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics

        Based on L208 lines 1227-1237 (Cache stats implementation)

        Returns:
            Dictionary with cache statistics
        """
        total_hits = sum(entry.hit_count for entry in self._cache.values())
        total_entries = len(self._cache)

        # Calculate cache size
        total_size = 0
        if self.cache_dir.exists():
            for cache_file in self.cache_dir.glob("*.json"):
                total_size += cache_file.stat().st_size

        return {
            'total_entries': total_entries,
            'total_hits': total_hits,
            'cache_size_bytes': total_size,
            'cache_size_mb': total_size / (1024 * 1024),
            'enabled': self.enabled
        }

    def _load_cache(self) -> None:
        """Load cache entries from disk"""
        if not self.cache_dir.exists():
            return

        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)

                entry = CacheEntry(**data)

                # Skip expired entries
                if not entry.is_expired(self.ttl_seconds):
                    self._cache[entry.key] = entry

            except Exception as e:
                # Skip corrupted cache files
                print(f"Warning: Could not load cache file {cache_file}: {e}")

    def _save_entry(self, entry: CacheEntry) -> None:
        """Save cache entry to disk

        Args:
            entry: Cache entry to save
        """
        cache_file = self.cache_dir / f"{entry.key}.json"

        try:
            with open(cache_file, 'w') as f:
                json.dump(asdict(entry), f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save cache entry: {e}")

    def _remove_cache_file(self, key: str) -> None:
        """Remove cache file from disk

        Args:
            key: Cache key
        """
        cache_file = self.cache_dir / f"{key}.json"
        if cache_file.exists():
            try:
                cache_file.unlink()
            except Exception as e:
                print(f"Warning: Could not remove cache file: {e}")


class CheckpointManager:
    """Manages processing checkpoints for crash recovery

    Tracks which documents have been processed to enable resumption
    after crashes or interruptions.

    Based on L208 lines 152-192 (Crash Recovery implementation)
    """

    def __init__(self, checkpoint_file: str = ".aget/checkpoints/processing.json"):
        """Initialize checkpoint manager

        Args:
            checkpoint_file: Path to checkpoint state file
        """
        self.checkpoint_file = Path(checkpoint_file)
        self.completed: set = set()
        self._load_checkpoint()

    def is_complete(self, document_id: str) -> bool:
        """Check if document has been processed

        Args:
            document_id: Document identifier

        Returns:
            True if document is in checkpoint
        """
        return document_id in self.completed

    def mark_complete(self, document_id: str) -> None:
        """Mark document as processed

        Args:
            document_id: Document identifier
        """
        self.completed.add(document_id)
        self._save_checkpoint()

    def get_completed_count(self) -> int:
        """Get number of completed documents

        Returns:
            Count of completed documents
        """
        return len(self.completed)

    def clear(self) -> None:
        """Clear all checkpoints"""
        self.completed.clear()
        if self.checkpoint_file.exists():
            self.checkpoint_file.unlink()

    def _load_checkpoint(self) -> None:
        """Load checkpoint from disk"""
        if not self.checkpoint_file.exists():
            return

        try:
            with open(self.checkpoint_file, 'r') as f:
                data = json.load(f)
                self.completed = set(data)
        except Exception as e:
            print(f"Warning: Could not load checkpoint: {e}")
            self.completed = set()

    def _save_checkpoint(self) -> None:
        """Save checkpoint to disk"""
        self.checkpoint_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(self.checkpoint_file, 'w') as f:
                json.dump(list(self.completed), f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save checkpoint: {e}")
