#!/usr/bin/env python3
"""
Minimal Integration Example: Track Changes Verification

Demonstrates simple API usage for L245 failure prevention.
"""

import sys
from pathlib import Path

# Add .aget/tools to path
sys.path.insert(0, str(Path(__file__).parent.parent / '.aget' / 'tools'))

from format_verification import verify_track_changes

def main():
    """Simple Track Changes verification example."""

    # Example 1: Basic verification
    print("=" * 60)
    print("Example 1: Basic Track Changes Verification")
    print("=" * 60)

    # Using test fixtures for demo (replace with your actual paths)
    input_path = "tests/fixtures/test_with_track_changes.docx"
    output_path = "tests/fixtures/test_with_track_changes.docx"  # Same file = preserved

    print(f"\nVerifying: {input_path} → {output_path}")

    result = verify_track_changes(input_path, output_path)

    if result.passed:
        print(f"✅ PASS: {result.message}")
    else:
        print(f"❌ FAIL: {result.message}")
        print("\nDetailed Report:")
        print(result.report())

        # Check for L245 catastrophic failure
        if result.details and result.details.get('loss_rate') == '100%':
            print("\n🚨 L245 CATASTROPHIC FAILURE DETECTED")
            print("STOP processing immediately and review architecture!")
            return 1

    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())
