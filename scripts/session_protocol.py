#!/usr/bin/env python3
"""Session Protocol CLI

Manage session lifecycle (wake up, wind down, sign off).

Usage:
    python3 scripts/session_protocol.py wake
    python3 scripts/session_protocol.py wind-down
    python3 scripts/session_protocol.py sign-off

Examples:
    # Wake up session
    python3 scripts/session_protocol.py wake

    # Wind down session
    python3 scripts/session_protocol.py wind-down

    # Sign off session
    python3 scripts/session_protocol.py sign-off
"""

import sys
import argparse
from pathlib import Path
import json
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


def wake_session():
    """Execute wake up protocol"""
    # Read version info
    version_file = Path('.aget/version.json')
    if version_file.exists():
        with open(version_file) as f:
            version_info = json.load(f)

        agent_name = version_info.get('agent_name', 'unknown')
        version = version_info.get('aget_version', 'unknown')
        instance_type = version_info.get('instance_type', 'unknown')

        print(f"{agent_name} v{version} ({instance_type})")
    else:
        print("Document Processor Template")

    print("=" * 60)

    # Show current directory
    import os
    cwd = os.getcwd()
    print(f"\n📍 Location: {cwd}")

    # Show git status
    try:
        import subprocess
        result = subprocess.run(['git', 'status', '--short'], capture_output=True, text=True)
        if result.returncode == 0:
            status = result.stdout.strip()
            if status:
                print(f"📊 Git: Changes detected")
            else:
                print(f"📊 Git: Clean")
        else:
            print(f"📊 Git: Not a repository")
    except:
        print(f"📊 Git: Status unavailable")

    # Show capabilities
    print(f"\n🎯 Key Capabilities:")
    print(f"  • Document validation and processing")
    print(f"  • Queue management and batch operations")
    print(f"  • Version control and rollback")
    print(f"  • Cache management and metrics")
    print(f"  • Security validation")

    print(f"\nReady for processing.")


def wind_down_session():
    """Execute wind down protocol"""
    print("Session Wind Down")
    print("=" * 60)

    # Check for uncommitted changes
    try:
        import subprocess
        result = subprocess.run(['git', 'status', '--short'], capture_output=True, text=True)
        if result.returncode == 0:
            status = result.stdout.strip()
            if status:
                print(f"\n⚠️  Uncommitted changes detected:")
                print(status)
                print(f"\nRecommendation: Commit changes before ending session")
            else:
                print(f"\n✅ No uncommitted changes")
    except:
        pass

    # Check queue status
    try:
        from ingestion.queue_manager import QueueManager
        queue = QueueManager()
        queue_status = queue.get_status()

        print(f"\nQueue Status:")
        print(f"  Candidates: {queue_status['candidates']}")
        print(f"  Pending: {queue_status['pending']}")
        print(f"  Processed: {queue_status['processed']}")
        print(f"  Failed: {queue_status['failed']}")

        if queue_status['pending'] > 0:
            print(f"\n⚠️  {queue_status['pending']} documents still pending")
    except:
        pass

    print(f"\nWind down complete.")


def sign_off_session():
    """Execute sign off protocol"""
    print("Session Sign Off")
    print("=" * 60)

    # Quick status check
    try:
        import subprocess
        result = subprocess.run(['git', 'status', '--short'], capture_output=True, text=True)
        if result.returncode == 0:
            status = result.stdout.strip()
            if status:
                print(f"\n⚠️  Uncommitted changes - consider committing")
    except:
        pass

    print(f"\n✅ Session ended")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Manage session lifecycle (wake up, wind down, sign off)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Wake up session
  python3 scripts/session_protocol.py wake

  # Wind down session
  python3 scripts/session_protocol.py wind-down

  # Sign off session
  python3 scripts/session_protocol.py sign-off
        """
    )

    parser.add_argument(
        'action',
        choices=['wake', 'wind-down', 'sign-off'],
        help='Session action to perform'
    )

    args = parser.parse_args()

    # Execute
    try:
        if args.action == 'wake':
            wake_session()
        elif args.action == 'wind-down':
            wind_down_session()
        elif args.action == 'sign-off':
            sign_off_session()

        sys.exit(0)

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
