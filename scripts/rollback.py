#!/usr/bin/env python3
"""Rollback Operations CLI

Rollback document processing to previous versions.

Usage:
    python3 scripts/rollback.py <document_id>
    python3 scripts/rollback.py <document_id> --to-version <version_number>
    python3 scripts/rollback.py <document_id> --list-versions

Examples:
    # Show version history
    python3 scripts/rollback.py doc_001 --list-versions

    # Rollback to previous version
    python3 scripts/rollback.py doc_001

    # Rollback to specific version
    python3 scripts/rollback.py doc_001 --to-version 2
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from output.version_manager import VersionManager
from output.publisher import Publisher, FilesystemPublisher


def list_versions(document_id: str, version_manager: VersionManager):
    """List all versions of a document

    Args:
        document_id: Document identifier
        version_manager: VersionManager instance
    """
    versions = version_manager.get_version_history(document_id)

    if not versions:
        print(f"No versions found for document: {document_id}")
        return

    print(f"Version History for: {document_id}")
    print("=" * 60)
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


def rollback_to_version(
    document_id: str,
    version_number: int,
    version_manager: VersionManager,
    output_dir: str = ".aget/output"
) -> bool:
    """Rollback document to specific version

    Args:
        document_id: Document identifier
        version_number: Version number to rollback to
        version_manager: VersionManager instance
        output_dir: Output directory for rolled-back content

    Returns:
        True if rollback succeeded, False otherwise
    """
    # Get version history
    versions = version_manager.get_version_history(document_id)

    if not versions:
        print(f"Error: No versions found for document: {document_id}")
        return False

    # Find target version
    target_version = None
    for v in versions:
        if v.number == version_number:
            target_version = v
            break

    if not target_version:
        print(f"Error: Version #{version_number} not found")
        print(f"Available versions: {[v.number for v in versions]}")
        return False

    # Get current (latest) version for comparison
    latest_version = version_manager.get_latest_version(document_id)

    if latest_version.number == version_number:
        print(f"Document is already at version #{version_number}")
        return True

    # Display rollback information
    print(f"Rolling back: {document_id}")
    print(f"  From: Version #{latest_version.number} ({latest_version.version_id})")
    print(f"  To:   Version #{target_version.number} ({target_version.version_id})")

    target_time = datetime.fromtimestamp(target_version.timestamp).strftime('%Y-%m-%d %H:%M:%S')
    print(f"  Target created: {target_time}")

    # Create new version with rolled-back content
    print(f"\nCreating rollback version...")

    new_version = version_manager.create_version(
        document_id=document_id,
        content=target_version.content,
        processing_metadata={
            **target_version.processing_metadata,
            'rollback': True,
            'rollback_from_version': latest_version.version_id,
            'rollback_to_version': target_version.version_id,
            'rollback_timestamp': datetime.now().isoformat()
        },
        parent_version_id=latest_version.version_id
    )

    print(f"✅ Created rollback version: {new_version.version_id}")
    print(f"   Version number: #{new_version.number}")

    # Publish rolled-back content
    print(f"\nPublishing rolled-back content...")

    publisher = Publisher()
    publisher.add_publisher(FilesystemPublisher(output_dir=output_dir, format='json'))

    publish_results = publisher.publish(
        document_id=document_id,
        content=new_version.content,
        metadata={
            'version_id': new_version.version_id,
            'version_number': new_version.number,
            'rollback': True,
            'rollback_from': latest_version.number,
            'rollback_to': target_version.number
        }
    )

    all_success = all(r.success for r in publish_results)

    if all_success:
        for result in publish_results:
            print(f"✅ Published to: {result.publish_path}")

        print(f"\n✅ Rollback complete")
        print(f"   Document: {document_id}")
        print(f"   New version: #{new_version.number}")
        print(f"   Content restored from: Version #{target_version.number}")
        return True
    else:
        print(f"\n❌ Publishing failed:")
        for result in publish_results:
            if not result.success:
                print(f"   {result.destination}: {result.error_message}")
        return False


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Rollback document processing to previous versions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show version history
  python3 scripts/rollback.py doc_001 --list-versions

  # Rollback to previous version
  python3 scripts/rollback.py doc_001

  # Rollback to specific version
  python3 scripts/rollback.py doc_001 --to-version 2

  # Rollback with custom output directory
  python3 scripts/rollback.py doc_001 --to-version 2 --output-dir ./rollback
        """
    )

    parser.add_argument(
        'document_id',
        help='Document identifier'
    )

    parser.add_argument(
        '--to-version',
        metavar='VERSION_NUMBER',
        type=int,
        help='Version number to rollback to (defaults to previous version)'
    )

    parser.add_argument(
        '--list-versions', '-l',
        action='store_true',
        help='List all versions of the document'
    )

    parser.add_argument(
        '--output-dir',
        metavar='DIRECTORY',
        default='.aget/output',
        help='Output directory for rolled-back content (default: .aget/output)'
    )

    args = parser.parse_args()

    # Initialize version manager
    try:
        version_manager = VersionManager()

        if args.list_versions:
            # List versions
            list_versions(args.document_id, version_manager)
            sys.exit(0)

        else:
            # Determine target version
            if args.to_version:
                target_version_number = args.to_version
            else:
                # Default: rollback to previous version
                versions = version_manager.get_version_history(args.document_id)
                if not versions:
                    print(f"Error: No versions found for document: {args.document_id}")
                    sys.exit(1)

                if len(versions) < 2:
                    print(f"Error: Document has only one version, cannot rollback")
                    sys.exit(1)

                # Second-to-last version (previous version)
                target_version_number = versions[-2].number

            # Perform rollback
            success = rollback_to_version(
                document_id=args.document_id,
                version_number=target_version_number,
                version_manager=version_manager,
                output_dir=args.output_dir
            )

            sys.exit(0 if success else 1)

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
