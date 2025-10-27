#!/usr/bin/env python3
"""Cache Statistics CLI

Display cache statistics and performance metrics.

Usage:
    python3 scripts/cache_stats.py
    python3 scripts/cache_stats.py --detailed

Examples:
    # Show cache statistics summary
    python3 scripts/cache_stats.py

    # Show detailed cache statistics
    python3 scripts/cache_stats.py --detailed
"""

import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from processing.cache_manager import CacheManager


def show_cache_stats(detailed: bool = False):
    """Display cache statistics

    Args:
        detailed: Show detailed statistics
    """
    cache = CacheManager()
    stats = cache.get_stats()

    print("Cache Statistics")
    print("=" * 60)

    # Basic stats
    print(f"\nCache Status:")
    print(f"  Enabled: {stats['enabled']}")
    print(f"  Total entries: {stats['total_entries']}")
    print(f"  Total hits: {stats['total_hits']}")
    print(f"  Cache size: {stats['cache_size_mb']:.2f} MB ({stats['cache_size_bytes']:,} bytes)")

    if detailed:
        # Calculate additional metrics
        avg_hits_per_entry = stats['total_hits'] / stats['total_entries'] if stats['total_entries'] > 0 else 0

        print(f"\nDetailed Metrics:")
        print(f"  Average hits per entry: {avg_hits_per_entry:.1f}")

        # Check cache directory
        cache_dir = Path('.aget/cache')
        if cache_dir.exists():
            cache_files = list(cache_dir.glob('*.json'))
            print(f"  Cache files: {len(cache_files)}")

            if cache_files:
                total_file_size = sum(f.stat().st_size for f in cache_files)
                avg_file_size = total_file_size / len(cache_files)
                print(f"  Average file size: {avg_file_size/1024:.2f} KB")

    # Performance indicators
    print(f"\nPerformance Indicators:")
    if stats['total_entries'] == 0:
        print(f"  ℹ️  Cache is empty - no metrics available")
    elif stats['total_hits'] == 0:
        print(f"  ⚠️  No cache hits recorded")
    else:
        print(f"  ✅ Cache is being utilized ({stats['total_hits']} hits)")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Display cache statistics and performance metrics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show cache statistics summary
  python3 scripts/cache_stats.py

  # Show detailed cache statistics
  python3 scripts/cache_stats.py --detailed
        """
    )

    parser.add_argument(
        '--detailed', '-d',
        action='store_true',
        help='Show detailed cache statistics'
    )

    args = parser.parse_args()

    # Execute
    try:
        show_cache_stats(detailed=args.detailed)
        sys.exit(0)

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
