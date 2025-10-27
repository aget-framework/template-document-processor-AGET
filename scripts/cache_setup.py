#!/usr/bin/env python3
"""Cache Setup CLI

Configure and initialize cache for LLM response caching.

Usage:
    python3 scripts/cache_setup.py
    python3 scripts/cache_setup.py --backend simple --max-size 10000
    python3 scripts/cache_setup.py --clear

Examples:
    # Initialize cache with defaults
    python3 scripts/cache_setup.py

    # Initialize with custom configuration
    python3 scripts/cache_setup.py --backend simple --max-size 10000 --ttl 3600

    # Clear cache
    python3 scripts/cache_setup.py --clear
"""

import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from processing.cache_manager import CacheManager


def initialize_cache(cache_dir: str, ttl: int, enabled: bool) -> CacheManager:
    """Initialize cache with configuration

    Args:
        cache_dir: Cache directory path
        ttl: Time-to-live in seconds
        enabled: Whether caching is enabled

    Returns:
        Configured CacheManager instance
    """
    print(f"Initializing cache...")
    print(f"  Cache directory: {cache_dir}")
    print(f"  TTL: {ttl} seconds ({ttl/3600:.1f} hours)")
    print(f"  Enabled: {enabled}")

    cache = CacheManager(
        cache_dir=cache_dir,
        ttl_seconds=ttl,
        enabled=enabled
    )

    print(f"\n✅ Cache initialized")

    # Display initial stats
    stats = cache.get_stats()
    print(f"\nCache Statistics:")
    print(f"  Total entries: {stats['total_entries']}")
    print(f"  Cache size: {stats['cache_size_mb']:.2f} MB")
    print(f"  Enabled: {stats['enabled']}")

    return cache


def clear_cache(cache: CacheManager):
    """Clear all cache entries

    Args:
        cache: CacheManager instance
    """
    stats_before = cache.get_stats()

    print(f"Clearing cache...")
    print(f"  Current entries: {stats_before['size']}")

    cache.clear()

    stats_after = cache.get_stats()

    print(f"\n✅ Cache cleared")
    print(f"  Entries removed: {stats_before['size']}")
    print(f"  Current entries: {stats_after['size']}")


def verify_cache(cache: CacheManager):
    """Verify cache is working

    Args:
        cache: CacheManager instance
    """
    print(f"\nVerifying cache functionality...")

    # Simple verification - check cache directory exists
    import os
    if os.path.exists(cache.cache_dir):
        print(f"  ✅ Cache directory exists: {cache.cache_dir}")
    else:
        print(f"  ❌ Cache directory not found: {cache.cache_dir}")

    # Display stats
    stats = cache.get_stats()
    print(f"\nCache Statistics:")
    print(f"  Total entries: {stats['total_entries']}")
    print(f"  Total hits: {stats['total_hits']}")
    print(f"  Cache size: {stats['cache_size_mb']:.2f} MB")
    print(f"  Enabled: {stats['enabled']}")

    print(f"\n✅ Cache verification complete")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Configure and initialize cache for LLM response caching",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Initialize cache with defaults
  python3 scripts/cache_setup.py

  # Initialize with custom configuration
  python3 scripts/cache_setup.py --cache-dir .aget/cache --ttl 3600

  # Clear cache
  python3 scripts/cache_setup.py --clear

  # Verify cache functionality
  python3 scripts/cache_setup.py --verify
        """
    )

    parser.add_argument(
        '--cache-dir',
        default='.aget/cache',
        help='Cache directory path (default: .aget/cache)'
    )

    parser.add_argument(
        '--ttl',
        type=int,
        default=3600,
        help='Time-to-live in seconds (default: 3600 = 1 hour)'
    )

    parser.add_argument(
        '--enabled',
        type=bool,
        default=True,
        help='Enable caching (default: True)'
    )

    parser.add_argument(
        '--clear',
        action='store_true',
        help='Clear all cache entries'
    )

    parser.add_argument(
        '--verify',
        action='store_true',
        help='Verify cache functionality'
    )

    args = parser.parse_args()

    # Execute requested operation
    try:
        # Initialize cache
        cache = initialize_cache(
            cache_dir=args.cache_dir,
            ttl=args.ttl,
            enabled=args.enabled
        )

        # Clear if requested
        if args.clear:
            print()
            clear_cache(cache)

        # Verify if requested
        if args.verify:
            print()
            verify_cache(cache)

        sys.exit(0)

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
