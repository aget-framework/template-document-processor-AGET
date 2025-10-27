#!/usr/bin/env python3
"""Document Validation CLI

Validates documents against configured validation rules before processing.

Usage:
    python3 scripts/validate.py <document_path>
    python3 scripts/validate.py <document_path> --verbose
    python3 scripts/validate.py --batch <file_list.txt>

Examples:
    # Validate single document
    python3 scripts/validate.py /path/to/document.pdf

    # Validate with detailed output
    python3 scripts/validate.py /path/to/document.pdf --verbose

    # Validate batch of documents
    python3 scripts/validate.py --batch documents.txt
"""

import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from ingestion.validator import DocumentValidator, FileSizeValidator, FileFormatValidator, FileExistsValidator


def validate_document(document_path: str, verbose: bool = False) -> bool:
    """Validate a single document

    Args:
        document_path: Path to document
        verbose: Show detailed validation results

    Returns:
        True if valid, False otherwise
    """
    # Create validator with default rules
    validator = DocumentValidator()

    # Validate
    result = validator.validate(document_path)

    # Display results
    if result.valid:
        print(f"✅ VALID: {document_path}")

        if verbose and result.warnings:
            print(f"\n⚠️  Warnings ({len(result.warnings)}):")
            for warning in result.warnings:
                print(f"   - {warning}")

        if verbose and result.metadata:
            print(f"\n📊 Metadata:")
            for key, value in result.metadata.items():
                print(f"   {key}: {value}")
    else:
        print(f"❌ INVALID: {document_path}")
        print(f"\n❌ Errors ({len(result.errors)}):")
        for error in result.errors:
            print(f"   - {error}")

        if result.warnings:
            print(f"\n⚠️  Warnings ({len(result.warnings)}):")
            for warning in result.warnings:
                print(f"   - {warning}")

    return result.valid


def validate_batch(file_list_path: str, verbose: bool = False) -> dict:
    """Validate batch of documents from file list

    Args:
        file_list_path: Path to file containing document paths (one per line)
        verbose: Show detailed results

    Returns:
        Dictionary with validation statistics
    """
    # Read document paths
    with open(file_list_path) as f:
        document_paths = [line.strip() for line in f if line.strip()]

    print(f"Validating {len(document_paths)} documents...\n")

    # Validate each
    valid_count = 0
    invalid_count = 0

    for doc_path in document_paths:
        is_valid = validate_document(doc_path, verbose=verbose)
        if is_valid:
            valid_count += 1
        else:
            invalid_count += 1

        if not verbose:
            print()  # Blank line between documents

    # Summary
    print("=" * 60)
    print(f"Validation Summary:")
    print(f"  Total: {len(document_paths)}")
    print(f"  Valid: {valid_count} ({valid_count/len(document_paths)*100:.1f}%)")
    print(f"  Invalid: {invalid_count} ({invalid_count/len(document_paths)*100:.1f}%)")

    return {
        'total': len(document_paths),
        'valid': valid_count,
        'invalid': invalid_count,
        'success_rate': valid_count / len(document_paths) if document_paths else 0
    }


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Validate documents against configured validation rules",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate single document
  python3 scripts/validate.py /path/to/document.pdf

  # Validate with verbose output
  python3 scripts/validate.py /path/to/document.pdf --verbose

  # Validate batch of documents
  python3 scripts/validate.py --batch documents.txt
        """
    )

    parser.add_argument(
        'document',
        nargs='?',
        help='Path to document to validate'
    )

    parser.add_argument(
        '--batch',
        metavar='FILE_LIST',
        help='Path to file containing document paths (one per line)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed validation results'
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.document and not args.batch:
        parser.print_help()
        print("\nError: Must provide either document path or --batch option")
        sys.exit(1)

    if args.document and args.batch:
        print("Error: Cannot use both document path and --batch option")
        sys.exit(1)

    # Execute
    try:
        if args.batch:
            # Batch validation
            stats = validate_batch(args.batch, verbose=args.verbose)
            sys.exit(0 if stats['invalid'] == 0 else 1)
        else:
            # Single document validation
            is_valid = validate_document(args.document, verbose=args.verbose)
            sys.exit(0 if is_valid else 1)

    except FileNotFoundError as e:
        print(f"Error: File not found: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
