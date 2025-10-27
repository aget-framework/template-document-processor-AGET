#!/usr/bin/env python3
"""Checkpoint Management CLI

Manage processing checkpoints for resumable workflows.

Usage:
    python3 scripts/checkpoint.py --save <checkpoint_name>
    python3 scripts/checkpoint.py --list
    python3 scripts/checkpoint.py --load <checkpoint_name>

Examples:
    # Save current state as checkpoint
    python3 scripts/checkpoint.py --save batch_001_progress

    # List all checkpoints
    python3 scripts/checkpoint.py --list

    # Load checkpoint
    python3 scripts/checkpoint.py --load batch_001_progress
"""

import sys
import argparse
import json
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


def save_checkpoint(checkpoint_name: str):
    """Save current processing state as checkpoint

    Args:
        checkpoint_name: Name for the checkpoint
    """
    checkpoint_dir = Path('.aget/checkpoints')
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    checkpoint_file = checkpoint_dir / f"{checkpoint_name}.json"

    # Gather current state
    checkpoint_data = {
        'checkpoint_name': checkpoint_name,
        'created_at': datetime.now().isoformat(),
        'queue_status': {},
        'cache_stats': {},
        'version_count': 0
    }

    # Queue status
    try:
        from ingestion.queue_manager import QueueManager
        queue = QueueManager()
        checkpoint_data['queue_status'] = queue.get_status()
    except:
        pass

    # Cache stats
    try:
        from processing.cache_manager import CacheManager
        cache = CacheManager()
        checkpoint_data['cache_stats'] = cache.get_stats()
    except:
        pass

    # Version count
    try:
        versions_dir = Path('.aget/versions')
        if versions_dir.exists():
            index_file = versions_dir / '_index.json'
            if index_file.exists():
                with open(index_file) as f:
                    index = json.load(f)
                checkpoint_data['version_count'] = len(index)
    except:
        pass

    # Save checkpoint
    with open(checkpoint_file, 'w') as f:
        json.dump(checkpoint_data, f, indent=2)

    print(f"Checkpoint Saved")
    print("=" * 60)
    print(f"\nName: {checkpoint_name}")
    print(f"File: {checkpoint_file}")
    print(f"Time: {checkpoint_data['created_at']}")

    if checkpoint_data['queue_status']:
        print(f"\nQueue State:")
        for key, value in checkpoint_data['queue_status'].items():
            print(f"  {key}: {value}")

    print(f"\n✅ Checkpoint saved successfully")


def list_checkpoints():
    """List all saved checkpoints"""
    checkpoint_dir = Path('.aget/checkpoints')

    if not checkpoint_dir.exists():
        print("No checkpoints found")
        return

    checkpoint_files = list(checkpoint_dir.glob('*.json'))

    if not checkpoint_files:
        print("No checkpoints found")
        return

    print("Saved Checkpoints")
    print("=" * 60)

    for checkpoint_file in sorted(checkpoint_files):
        try:
            with open(checkpoint_file) as f:
                checkpoint_data = json.load(f)

            name = checkpoint_data.get('checkpoint_name', checkpoint_file.stem)
            created_at = checkpoint_data.get('created_at', 'unknown')

            print(f"\n{name}")
            print(f"  Created: {created_at}")
            print(f"  File: {checkpoint_file.name}")

            if 'queue_status' in checkpoint_data:
                queue_total = checkpoint_data['queue_status'].get('total', 0)
                print(f"  Queue items: {queue_total}")

        except Exception as e:
            print(f"\n{checkpoint_file.name}")
            print(f"  Error loading: {e}")


def load_checkpoint(checkpoint_name: str):
    """Load checkpoint and display state

    Args:
        checkpoint_name: Name of checkpoint to load
    """
    checkpoint_file = Path('.aget/checkpoints') / f"{checkpoint_name}.json"

    if not checkpoint_file.exists():
        print(f"Checkpoint not found: {checkpoint_name}")
        sys.exit(1)

    with open(checkpoint_file) as f:
        checkpoint_data = json.load(f)

    print("Checkpoint Loaded")
    print("=" * 60)

    print(f"\nName: {checkpoint_data.get('checkpoint_name', checkpoint_name)}")
    print(f"Created: {checkpoint_data.get('created_at', 'unknown')}")

    if 'queue_status' in checkpoint_data:
        print(f"\nQueue State at Checkpoint:")
        for key, value in checkpoint_data['queue_status'].items():
            print(f"  {key}: {value}")

    if 'cache_stats' in checkpoint_data:
        cache_stats = checkpoint_data['cache_stats']
        if cache_stats:
            print(f"\nCache State at Checkpoint:")
            print(f"  Entries: {cache_stats.get('total_entries', 0)}")
            print(f"  Size: {cache_stats.get('cache_size_mb', 0):.2f} MB")

    if 'version_count' in checkpoint_data:
        print(f"\nVersion Count: {checkpoint_data['version_count']}")

    print(f"\n✅ Checkpoint loaded")
    print(f"\nNote: This is a read-only view. Checkpoint data not applied to current state.")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Manage processing checkpoints for resumable workflows",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Save current state as checkpoint
  python3 scripts/checkpoint.py --save batch_001_progress

  # List all checkpoints
  python3 scripts/checkpoint.py --list

  # Load checkpoint
  python3 scripts/checkpoint.py --load batch_001_progress
        """
    )

    parser.add_argument(
        '--save',
        metavar='NAME',
        help='Save current state as checkpoint'
    )

    parser.add_argument(
        '--list',
        action='store_true',
        help='List all saved checkpoints'
    )

    parser.add_argument(
        '--load',
        metavar='NAME',
        help='Load and display checkpoint'
    )

    args = parser.parse_args()

    # Validate arguments
    actions = sum([bool(args.save), bool(args.list), bool(args.load)])
    if actions == 0:
        parser.print_help()
        print("\nError: Must specify --save, --list, or --load")
        sys.exit(1)

    if actions > 1:
        print("Error: Cannot use multiple actions simultaneously")
        sys.exit(1)

    # Execute
    try:
        if args.save:
            save_checkpoint(args.save)
        elif args.list:
            list_checkpoints()
        elif args.load:
            load_checkpoint(args.load)

        sys.exit(0)

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
