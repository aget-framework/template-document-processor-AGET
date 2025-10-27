#!/usr/bin/env python3
"""Audit Trail Viewer CLI

View audit trail and processing history.

Usage:
    python3 scripts/audit.py
    python3 scripts/audit.py --document <document_id>
    python3 scripts/audit.py --recent 10

Examples:
    # View complete audit trail
    python3 scripts/audit.py

    # View audit trail for specific document
    python3 scripts/audit.py --document doc_001

    # View recent 10 audit entries
    python3 scripts/audit.py --recent 10
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from ingestion.queue_manager import QueueManager
from output.version_manager import VersionManager


def view_queue_audit(document_id: str = None, recent: int = None):
    """View queue processing audit trail

    Args:
        document_id: Optional document ID to filter
        recent: Optional limit to recent N entries
    """
    queue = QueueManager()

    print("Queue Processing Audit Trail")
    print("=" * 60)

    # Get all items
    all_items = list(queue.items.values())

    if not all_items:
        print("\nNo audit entries found")
        return

    # Filter by document_id if specified
    if document_id:
        all_items = [item for item in all_items if item.document_id == document_id]
        if not all_items:
            print(f"\nNo audit entries found for document: {document_id}")
            return

    # Sort by timestamp (newest first)
    all_items.sort(key=lambda x: x.added_timestamp, reverse=True)

    # Limit if requested
    if recent:
        all_items = all_items[:recent]

    print(f"\nShowing {len(all_items)} audit entries:\n")

    # Display each entry
    for idx, item in enumerate(all_items, 1):
        added_time = datetime.fromtimestamp(item.added_timestamp).strftime('%Y-%m-%d %H:%M:%S')

        print(f"[{idx}] {item.document_id}")
        print(f"    State: {item.state.value}")
        print(f"    Path: {item.path}")
        print(f"    Added: {added_time}")

        if item.processed_timestamp:
            processed_time = datetime.fromtimestamp(item.processed_timestamp).strftime('%Y-%m-%d %H:%M:%S')
            duration = item.processed_timestamp - item.added_timestamp
            print(f"    Processed: {processed_time} (duration: {duration:.1f}s)")

        if item.result:
            print(f"    Result: {item.result}")

        if item.error_message:
            print(f"    Error: {item.error_message}")

        if item.metadata:
            print(f"    Metadata: {item.metadata}")

        print()


def view_version_audit(document_id: str = None):
    """View version history audit trail

    Args:
        document_id: Optional document ID to filter
    """
    version_manager = VersionManager()

    print("Version History Audit Trail")
    print("=" * 60)

    if document_id:
        # Show versions for specific document
        versions = version_manager.get_version_history(document_id)

        if not versions:
            print(f"\nNo versions found for document: {document_id}")
            return

        print(f"\nDocument: {document_id}")
        print(f"Total versions: {len(versions)}\n")

        for version in versions:
            timestamp = datetime.fromtimestamp(version.timestamp).strftime('%Y-%m-%d %H:%M:%S')

            print(f"Version #{version.number} - {version.version_id}")
            print(f"  Created: {timestamp}")
            print(f"  Content hash: {version.content_hash[:16]}...")

            if version.parent_version_id:
                print(f"  Parent: {version.parent_version_id}")

            if version.processing_metadata:
                print(f"  Metadata:")
                for key, value in version.processing_metadata.items():
                    print(f"    {key}: {value}")

            print()

    else:
        # Show all documents with versions
        versions_dir = Path('.aget/versions')

        if not versions_dir.exists():
            print("\nNo version history found")
            return

        # Load index
        index_file = versions_dir / '_index.json'
        if not index_file.exists():
            print("\nNo version index found")
            return

        import json
        with open(index_file) as f:
            index = json.load(f)

        print(f"\nDocuments with versions: {len(index)}\n")

        for doc_id, version_ids in index.items():
            print(f"Document: {doc_id}")
            print(f"  Versions: {len(version_ids)}")
            print(f"  Latest: {version_ids[-1] if version_ids else 'N/A'}")
            print()


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="View audit trail and processing history",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # View complete queue audit trail
  python3 scripts/audit.py

  # View audit trail for specific document
  python3 scripts/audit.py --document doc_001

  # View recent 10 audit entries
  python3 scripts/audit.py --recent 10

  # View version history for document
  python3 scripts/audit.py --document doc_001 --versions
        """
    )

    parser.add_argument(
        '--document',
        metavar='DOCUMENT_ID',
        help='Filter by document ID'
    )

    parser.add_argument(
        '--recent',
        metavar='N',
        type=int,
        help='Show only recent N entries'
    )

    parser.add_argument(
        '--versions',
        action='store_true',
        help='Show version history instead of queue audit'
    )

    args = parser.parse_args()

    # Execute
    try:
        if args.versions:
            view_version_audit(document_id=args.document)
        else:
            view_queue_audit(document_id=args.document, recent=args.recent)

        sys.exit(0)

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
