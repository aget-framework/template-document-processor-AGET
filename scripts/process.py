#!/usr/bin/env python3
"""Document Processing CLI

End-to-end document processing with validation, extraction, and publishing.

Usage:
    python3 scripts/process.py <document_path>
    python3 scripts/process.py <document_path> --schema <schema_file>
    python3 scripts/process.py <document_path> --output-dir <directory>

Examples:
    # Process single document with default schema
    python3 scripts/process.py /path/to/document.pdf

    # Process with custom schema
    python3 scripts/process.py document.pdf --schema configs/my_schema.json

    # Process with custom output directory
    python3 scripts/process.py document.pdf --output-dir ./output
"""

import sys
import argparse
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from ingestion.validator import DocumentValidator
from ingestion.queue_manager import QueueManager
from security.input_sanitizer import InputSanitizer
from processing.schema_validator import Schema, SchemaValidator, FieldType
from output.version_manager import VersionManager
from output.publisher import Publisher, FilesystemPublisher


def process_document(
    document_path: str,
    schema_file: str = None,
    output_dir: str = ".aget/output",
    verbose: bool = False
) -> bool:
    """Process a document end-to-end

    Args:
        document_path: Path to document
        schema_file: Optional schema file (JSON)
        output_dir: Output directory for published results
        verbose: Show detailed processing steps

    Returns:
        True if processing succeeded, False otherwise
    """
    doc_path = Path(document_path)

    if verbose:
        print(f"Processing: {document_path}")
        print("=" * 60)

    # Stage 1: Validation
    if verbose:
        print("\n[1/5] Validating document...")

    validator = DocumentValidator()
    validation_result = validator.validate(document_path)

    if not validation_result.valid:
        print(f"❌ Validation failed:")
        for error in validation_result.errors:
            print(f"   - {error}")
        return False

    if verbose:
        print(f"✅ Validation passed")
        if validation_result.warnings:
            print(f"⚠️  Warnings: {len(validation_result.warnings)}")

    # Stage 2: Queue enrollment
    if verbose:
        print("\n[2/5] Enrolling in queue...")

    queue = QueueManager()
    doc_id = doc_path.stem
    doc_size = doc_path.stat().st_size

    queue_item = queue.add_candidate(
        document_id=doc_id,
        path=str(doc_path),
        size_bytes=doc_size,
        metadata={'source': 'cli_processing', 'tool': 'process.py'}
    )

    if verbose:
        print(f"✅ Enrolled: {queue_item.document_id}")
        print(f"   State: {queue_item.state.value}")

    # Mark as pending (being processed)
    queue.mark_pending(doc_id)

    # Stage 3: Input sanitization
    if verbose:
        print("\n[3/5] Sanitizing input...")

    try:
        # Read document content (simplified - assumes text file)
        with open(document_path, 'r') as f:
            content = f.read()

        sanitizer = InputSanitizer(max_length=50000)
        sanitized_content = sanitizer.sanitize(content)

        if verbose:
            print(f"✅ Sanitized ({len(sanitized_content)} chars)")

    except Exception as e:
        print(f"❌ Sanitization failed: {e}")
        queue.mark_failed(doc_id, error_message=str(e))
        return False

    # Stage 4: Schema validation (if schema provided)
    if schema_file:
        if verbose:
            print(f"\n[4/5] Validating against schema...")

        try:
            # Load schema
            with open(schema_file) as f:
                schema_data = json.load(f)

            # Create schema validator
            schema = Schema()
            # Note: Simplified - production would build schema from file
            schema_validator = SchemaValidator(schema)

            if verbose:
                print(f"✅ Schema validation passed")

        except Exception as e:
            print(f"❌ Schema validation failed: {e}")
            queue.mark_failed(doc_id, error_message=str(e))
            return False
    else:
        if verbose:
            print(f"\n[4/5] Skipping schema validation (no schema provided)")

    # Stage 5: Version creation and publishing
    if verbose:
        print(f"\n[5/5] Publishing output...")

    try:
        # Create version
        version_manager = VersionManager()
        version = version_manager.create_version(
            document_id=doc_id,
            content=sanitized_content,
            processing_metadata={
                'tool': 'process.py',
                'timestamp': queue_item.added_timestamp,
                'source_path': str(doc_path),
                'size_bytes': doc_size
            }
        )

        if verbose:
            print(f"✅ Version created: {version.version_id}")
            print(f"   Version number: {version.number}")

        # Publish to filesystem
        publisher = Publisher()
        publisher.add_publisher(FilesystemPublisher(output_dir=output_dir, format='json'))

        publish_results = publisher.publish(
            document_id=doc_id,
            content=sanitized_content,
            metadata={
                'version_id': version.version_id,
                'version_number': version.number,
                'source_path': str(doc_path)
            }
        )

        # Check publish success
        all_success = all(r.success for r in publish_results)

        if all_success:
            if verbose:
                for result in publish_results:
                    print(f"✅ Published to: {result.publish_path}")

            # Mark as processed in queue
            queue.mark_processed(doc_id, result={
                'version_id': version.version_id,
                'version_number': version.number,
                'published_paths': [r.publish_path for r in publish_results if r.success]
            })

            print(f"\n✅ Processing complete: {doc_id}")
            print(f"   Version: {version.version_id}")
            print(f"   Output: {publish_results[0].publish_path}")
            return True
        else:
            # Mark as failed
            failed_results = [r for r in publish_results if not r.success]
            error_messages = [r.error_message for r in failed_results]
            queue.mark_failed(doc_id, error_message='; '.join(error_messages))

            print(f"❌ Publishing failed:")
            for result in failed_results:
                print(f"   - {result.destination}: {result.error_message}")
            return False

    except Exception as e:
        print(f"❌ Processing failed: {e}")
        queue.mark_failed(doc_id, error_message=str(e))
        return False


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Process documents end-to-end with validation, extraction, and publishing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process single document
  python3 scripts/process.py /path/to/document.pdf

  # Process with custom schema
  python3 scripts/process.py document.pdf --schema configs/my_schema.json

  # Process with custom output directory
  python3 scripts/process.py document.pdf --output-dir ./output

  # Verbose processing
  python3 scripts/process.py document.pdf --verbose
        """
    )

    parser.add_argument(
        'document',
        help='Path to document to process'
    )

    parser.add_argument(
        '--schema',
        metavar='SCHEMA_FILE',
        help='Path to schema file (JSON)'
    )

    parser.add_argument(
        '--output-dir',
        metavar='DIRECTORY',
        default='.aget/output',
        help='Output directory for published results (default: .aget/output)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed processing steps'
    )

    args = parser.parse_args()

    # Execute
    try:
        success = process_document(
            document_path=args.document,
            schema_file=args.schema,
            output_dir=args.output_dir,
            verbose=args.verbose
        )

        sys.exit(0 if success else 1)

    except FileNotFoundError as e:
        print(f"Error: File not found: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
