#!/usr/bin/env python3
"""Queue Status CLI

Display queue status and manage queue operations.

Usage:
    python3 scripts/queue_status.py
    python3 scripts/queue_status.py --detailed
    python3 scripts/queue_status.py --state CANDIDATE
    python3 scripts/queue_status.py --clear-failed

Examples:
    # Show queue summary
    python3 scripts/queue_status.py

    # Show detailed queue information
    python3 scripts/queue_status.py --detailed

    # Show only candidates
    python3 scripts/queue_status.py --state CANDIDATE

    # Clear failed items
    python3 scripts/queue_status.py --clear-failed
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from ingestion.queue_manager import QueueManager, QueueState


def show_queue_summary(queue: QueueManager):
    """Display queue summary statistics

    Args:
        queue: QueueManager instance
    """
    status = queue.get_status()

    print("Queue Status Summary")
    print("=" * 60)
    print(f"Total items: {status['total']}")
    print(f"  Candidates: {status['candidates']} ({status['candidates']/status['total']*100:.1f}%)" if status['total'] > 0 else "  Candidates: 0")
    print(f"  Pending: {status['pending']} ({status['pending']/status['total']*100:.1f}%)" if status['total'] > 0 else "  Pending: 0")
    print(f"  Processed: {status['processed']} ({status['processed']/status['total']*100:.1f}%)" if status['total'] > 0 else "  Processed: 0")
    print(f"  Failed: {status['failed']} ({status['failed']/status['total']*100:.1f}%)" if status['total'] > 0 else "  Failed: 0")

    if status['total'] > 0:
        success_rate = status['processed'] / (status['processed'] + status['failed']) * 100 if (status['processed'] + status['failed']) > 0 else 0
        print(f"\nSuccess rate: {success_rate:.1f}%")


def show_queue_detailed(queue: QueueManager, state_filter: str = None):
    """Display detailed queue information

    Args:
        queue: QueueManager instance
        state_filter: Optional state filter (CANDIDATE, PENDING, PROCESSED, FAILED)
    """
    print("Queue Detailed View")
    print("=" * 60)

    # Get items by state
    if state_filter:
        state_filter_upper = state_filter.upper()
        if state_filter_upper == "CANDIDATE":
            items = queue.get_candidates()
            print(f"\nCandidate Documents ({len(items)}):")
        elif state_filter_upper == "PENDING":
            items = queue.get_pending()
            print(f"\nPending Documents ({len(items)}):")
        elif state_filter_upper == "PROCESSED":
            items = queue.get_processed()
            print(f"\nProcessed Documents ({len(items)}):")
        elif state_filter_upper == "FAILED":
            items = queue.get_failed()
            print(f"\nFailed Documents ({len(items)}):")
        else:
            print(f"Error: Invalid state '{state_filter}'. Use: CANDIDATE, PENDING, PROCESSED, or FAILED")
            return
    else:
        # Show all states
        items = list(queue.items.values())
        print(f"\nAll Documents ({len(items)}):")

    if not items:
        print("  (none)")
        return

    # Display each item
    for item in items:
        print(f"\n  Document: {item.document_id}")
        print(f"    Path: {item.path}")
        print(f"    State: {item.state.value}")
        print(f"    Size: {item.size_bytes:,} bytes")

        # Format timestamp
        added_time = datetime.fromtimestamp(item.added_timestamp).strftime('%Y-%m-%d %H:%M:%S')
        print(f"    Added: {added_time}")

        # Processed timestamp if available
        if item.processed_timestamp:
            processed_time = datetime.fromtimestamp(item.processed_timestamp).strftime('%Y-%m-%d %H:%M:%S')
            duration = item.processed_timestamp - item.added_timestamp
            print(f"    Processed: {processed_time} (duration: {duration:.1f}s)")

        # Result if available
        if item.result:
            print(f"    Result: {item.result}")

        # Error if available
        if item.error_message:
            print(f"    Error: {item.error_message}")

        # Metadata if available
        if item.metadata:
            print(f"    Metadata: {item.metadata}")


def clear_failed_items(queue: QueueManager) -> int:
    """Clear failed items from queue

    Args:
        queue: QueueManager instance

    Returns:
        Number of items cleared
    """
    failed_items = queue.get_failed()

    if not failed_items:
        print("No failed items to clear")
        return 0

    print(f"Clearing {len(failed_items)} failed items...")

    # Note: QueueManager doesn't have a remove method in current implementation
    # This would need to be added to the actual implementation
    # For now, just report what would be cleared

    for item in failed_items:
        print(f"  Would clear: {item.document_id} (Error: {item.error_message})")

    print(f"\n⚠️  Note: Clear operation not implemented in current QueueManager")
    print(f"   Suggested: Add queue.remove_item(document_id) method")

    return len(failed_items)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Display queue status and manage queue operations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show queue summary
  python3 scripts/queue_status.py

  # Show detailed queue information
  python3 scripts/queue_status.py --detailed

  # Show only candidates
  python3 scripts/queue_status.py --state CANDIDATE

  # Show only failed items
  python3 scripts/queue_status.py --state FAILED

  # Clear failed items
  python3 scripts/queue_status.py --clear-failed
        """
    )

    parser.add_argument(
        '--detailed', '-d',
        action='store_true',
        help='Show detailed queue information'
    )

    parser.add_argument(
        '--state',
        metavar='STATE',
        choices=['CANDIDATE', 'PENDING', 'PROCESSED', 'FAILED'],
        help='Filter by state (CANDIDATE, PENDING, PROCESSED, FAILED)'
    )

    parser.add_argument(
        '--clear-failed',
        action='store_true',
        help='Clear failed items from queue'
    )

    args = parser.parse_args()

    # Initialize queue manager
    try:
        queue = QueueManager()

        # Execute requested operation
        if args.clear_failed:
            clear_failed_items(queue)
        elif args.detailed or args.state:
            show_queue_detailed(queue, state_filter=args.state)
        else:
            show_queue_summary(queue)

        sys.exit(0)

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
