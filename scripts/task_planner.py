#!/usr/bin/env python3
"""Task Decomposition Planner CLI

Plan task decomposition for complex documents.

Usage:
    python3 scripts/task_planner.py <document_path>
    python3 scripts/task_planner.py <document_path> --schema <schema_file>

Examples:
    # Plan task decomposition for document
    python3 scripts/task_planner.py /path/to/large_document.pdf

    # Plan with custom schema
    python3 scripts/task_planner.py document.pdf --schema schema.json
"""

import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


def estimate_document_complexity(document_path: str) -> dict:
    """Estimate document processing complexity

    Args:
        document_path: Path to document

    Returns:
        Dictionary with complexity metrics
    """
    doc_path = Path(document_path)

    if not doc_path.exists():
        raise FileNotFoundError(f"Document not found: {document_path}")

    # Get file size
    file_size = doc_path.stat().st_size

    # Estimate content size (simplified)
    try:
        with open(document_path, 'r') as f:
            content = f.read()
        char_count = len(content)
        word_count = len(content.split())
        line_count = len(content.splitlines())
    except:
        # Binary or unreadable file
        char_count = file_size  # Rough estimate
        word_count = file_size // 5  # Rough estimate
        line_count = file_size // 100  # Rough estimate

    return {
        'file_size_bytes': file_size,
        'file_size_mb': file_size / (1024 * 1024),
        'char_count': char_count,
        'word_count': word_count,
        'line_count': line_count,
        'estimated_tokens': word_count * 1.3  # Rough estimate
    }


def recommend_decomposition(complexity: dict) -> dict:
    """Recommend task decomposition strategy

    Args:
        complexity: Complexity metrics

    Returns:
        Decomposition recommendation
    """
    file_size_mb = complexity['file_size_mb']
    estimated_tokens = complexity['estimated_tokens']

    # Determine if decomposition is needed
    if file_size_mb < 0.1 and estimated_tokens < 10000:
        # Small document - no decomposition needed
        return {
            'strategy': 'single_task',
            'reason': 'Document is small enough for single-task processing',
            'chunk_count': 1,
            'estimated_duration': '1-2 minutes'
        }

    elif file_size_mb < 1.0 and estimated_tokens < 50000:
        # Medium document - optional decomposition
        return {
            'strategy': 'optional',
            'reason': 'Document size moderate - decomposition optional for performance',
            'chunk_count': 2,
            'estimated_duration': '2-5 minutes'
        }

    else:
        # Large document - decomposition recommended
        chunk_size = 50000  # tokens per chunk
        chunk_count = max(2, int(estimated_tokens // chunk_size))

        return {
            'strategy': 'chunking',
            'reason': 'Document is large - decomposition recommended',
            'chunk_count': chunk_count,
            'chunk_size_tokens': chunk_size,
            'overlap_tokens': 500,
            'estimated_duration': f'{chunk_count * 2}-{chunk_count * 3} minutes'
        }


def plan_decomposition(document_path: str, schema_file: str = None):
    """Plan task decomposition for document

    Args:
        document_path: Path to document
        schema_file: Optional schema file
    """
    print("Task Decomposition Plan")
    print("=" * 60)

    print(f"\nDocument: {document_path}")

    # Analyze complexity
    print(f"\n[1/3] Analyzing document complexity...")

    complexity = estimate_document_complexity(document_path)

    print(f"\nComplexity Metrics:")
    print(f"  File size: {complexity['file_size_mb']:.2f} MB ({complexity['file_size_bytes']:,} bytes)")
    print(f"  Characters: {complexity['char_count']:,}")
    print(f"  Words: {complexity['word_count']:,}")
    print(f"  Lines: {complexity['line_count']:,}")
    print(f"  Estimated tokens: {complexity['estimated_tokens']:.0f}")

    # Get decomposition recommendation
    print(f"\n[2/3] Determining decomposition strategy...")

    recommendation = recommend_decomposition(complexity)

    print(f"\nRecommended Strategy: {recommendation['strategy'].upper()}")
    print(f"Reason: {recommendation['reason']}")

    if recommendation['strategy'] == 'single_task':
        print(f"\nProcessing Plan:")
        print(f"  Tasks: 1 (no decomposition)")
        print(f"  Estimated duration: {recommendation['estimated_duration']}")

    elif recommendation['strategy'] == 'optional':
        print(f"\nProcessing Plan (if decomposed):")
        print(f"  Tasks: {recommendation['chunk_count']}")
        print(f"  Estimated duration: {recommendation['estimated_duration']}")
        print(f"\nNote: Decomposition optional - single task also viable")

    elif recommendation['strategy'] == 'chunking':
        print(f"\nProcessing Plan:")
        print(f"  Tasks: {recommendation['chunk_count']} chunks")
        print(f"  Chunk size: {recommendation['chunk_size_tokens']:.0f} tokens")
        print(f"  Overlap: {recommendation['overlap_tokens']} tokens")
        print(f"  Estimated duration: {recommendation['estimated_duration']}")

    # Schema considerations
    print(f"\n[3/3] Schema considerations...")

    if schema_file:
        print(f"  Custom schema: {schema_file}")
        print(f"  Note: Schema complexity may increase processing time")
    else:
        print(f"  No schema specified - using default extraction")

    print(f"\n" + "=" * 60)
    print(f"✅ Task decomposition plan complete")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Plan task decomposition for complex documents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Plan task decomposition for document
  python3 scripts/task_planner.py /path/to/large_document.pdf

  # Plan with custom schema
  python3 scripts/task_planner.py document.pdf --schema schema.json
        """
    )

    parser.add_argument(
        'document',
        help='Path to document to analyze'
    )

    parser.add_argument(
        '--schema',
        metavar='SCHEMA_FILE',
        help='Path to schema file (optional)'
    )

    args = parser.parse_args()

    # Execute
    try:
        plan_decomposition(args.document, schema_file=args.schema)
        sys.exit(0)

    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
