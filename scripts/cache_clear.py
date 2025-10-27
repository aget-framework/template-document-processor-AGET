#!/usr/bin/env python3
"""Cache Clearing CLI

Clear cache entries to free up space or reset caching.

Usage:
    python3 scripts/cache_clear.py
    python3 scripts/cache_clear.py --expired-only
    python3 scripts/cache_clear.py --confirm

Examples:
    # Clear all cache (with confirmation)
    python3 scripts/cache_clear.py --confirm

    # Clear only expired entries
    python3 scripts/cache_clear.py --expired-only

    # Dry run (show what would be cleared)
    python3 scripts/cache_clear.py
"""

import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from processing.cache_manager import CacheManager


def clear_cache(expired_only: bool = False, confirm: bool = False, dry_run: bool = True):
    """Clear cache entries

    Args:
        expired_only: Clear only expired entries
        confirm: Confirm clearing (required for actual clear)
        dry_run: Show what would be cleared without clearing
    """
    cache = CacheManager()

    # Get stats before clearing
    stats_before = cache.get_stats()

    print("Cache Clearing")
    print("=" * 60)

    print(f"\nCurrent Cache Status:")
    print(f"  Total entries: {stats_before['total_entries']}")
    print(f"  Cache size: {stats_before['cache_size_mb']:.2f} MB")

    if stats_before['total_entries'] == 0:
        print(f"\n  Cache is already empty - nothing to clear")
        return

    # Determine what to clear
    if expired_only:
        print(f"\nClearing: Expired entries only")
        action = "clear_expired"
    else:
        print(f"\nClearing: All entries")
        action = "clear_all"

    # Dry run or actual clear
    if dry_run:
        print(f"\n⚠️  DRY RUN - No changes will be made")
        print(f"   Add --confirm flag to actually clear cache")

    elif not confirm:
        print(f"\n❌ Confirmation required")
        print(f"   Add --confirm flag to clear cache")
        sys.exit(1)

    else:
        # Actually clear
        print(f"\nClearing cache...")

        if expired_only:
            cleared_count = cache.clear_expired()
        else:
            cleared_count = cache.clear()

        stats_after = cache.get_stats()

        print(f"\n✅ Cache cleared")
        print(f"\nResults:")
        print(f"  Entries before: {stats_before['total_entries']}")
        print(f"  Entries after: {stats_after['total_entries']}")
        print(f"  Entries cleared: {cleared_count}")
        print(f"  Space freed: {stats_before['cache_size_mb'] - stats_after['cache_size_mb']:.2f} MB")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Clear cache entries to free up space or reset caching",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run (show what would be cleared)
  python3 scripts/cache_clear.py

  # Clear all cache (with confirmation)
  python3 scripts/cache_clear.py --confirm

  # Clear only expired entries
  python3 scripts/cache_clear.py --expired-only --confirm
        """
    )

    parser.add_argument(
        '--expired-only',
        action='store_true',
        help='Clear only expired cache entries'
    )

    parser.add_argument(
        '--confirm',
        action='store_true',
        help='Confirm cache clearing (required for actual clear)'
    )

    args = parser.parse_args()

    # Execute
    try:
        clear_cache(
            expired_only=args.expired_only,
            confirm=args.confirm,
            dry_run=not args.confirm
        )

        sys.exit(0)

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
