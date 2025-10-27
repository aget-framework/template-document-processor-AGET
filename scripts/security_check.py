#!/usr/bin/env python3
"""Security Validation CLI

Run security checks on documents and system configuration.

Usage:
    python3 scripts/security_check.py <document_path>
    python3 scripts/security_check.py --check-config

Examples:
    # Check document for security issues
    python3 scripts/security_check.py /path/to/document.txt

    # Check system security configuration
    python3 scripts/security_check.py --check-config
"""

import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from security.input_sanitizer import InputSanitizer
from security.content_filter import ContentFilterPipeline


def check_document_security(document_path: str, verbose: bool = False) -> bool:
    """Check document for security issues

    Args:
        document_path: Path to document
        verbose: Show detailed results

    Returns:
        True if document passes all security checks
    """
    print(f"Security Check: {document_path}")
    print("=" * 60)

    # Read document
    try:
        with open(document_path, 'r') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Failed to read document: {e}")
        return False

    # Check 1: Input sanitization
    print("\n[1/2] Input Sanitization...")
    try:
        sanitizer = InputSanitizer(max_length=50000)
        sanitized_content = sanitizer.sanitize(content)

        print(f"✅ Input sanitization passed")
        if verbose:
            print(f"   Original length: {len(content)} chars")
            print(f"   Sanitized length: {len(sanitized_content)} chars")

    except Exception as e:
        print(f"❌ Input sanitization failed: {e}")
        return False

    # Check 2: Content filtering
    print("\n[2/2] Content Filtering...")
    try:
        content_filter = ContentFilterPipeline()
        passed, matches = content_filter.scan(content)

        if passed:
            print(f"✅ Content filtering passed (no sensitive content detected)")
        else:
            print(f"⚠️  Content filtering found {len(matches)} potential issues:")
            for match in matches:
                print(f"   - {match.filter_name}: {match.matched_text[:50]}... (severity: {match.severity})")

    except Exception as e:
        print(f"❌ Content filtering failed: {e}")
        return False

    # Summary
    print("\n" + "=" * 60)
    if passed:
        print("✅ Security check passed")
        return True
    else:
        print("⚠️  Security check completed with warnings")
        return False


def check_system_security(verbose: bool = False) -> bool:
    """Check system security configuration

    Args:
        verbose: Show detailed results

    Returns:
        True if system security is properly configured
    """
    print("System Security Configuration Check")
    print("=" * 60)

    checks_passed = 0
    checks_total = 0

    # Check 1: Security policy file exists
    print("\n[1/4] Security Policy Configuration...")
    checks_total += 1

    security_policy_file = Path('configs/security_policy.yaml')
    if security_policy_file.exists():
        print(f"✅ Security policy file exists: {security_policy_file}")
        checks_passed += 1
        if verbose:
            size = security_policy_file.stat().st_size
            print(f"   Size: {size} bytes")
    else:
        print(f"❌ Security policy file not found: {security_policy_file}")

    # Check 2: Input sanitizer available
    print("\n[2/4] Input Sanitizer Availability...")
    checks_total += 1

    try:
        sanitizer = InputSanitizer()
        print(f"✅ Input sanitizer initialized")
        checks_passed += 1
        if verbose:
            print(f"   Max length: {sanitizer.max_length} chars")
    except Exception as e:
        print(f"❌ Input sanitizer initialization failed: {e}")

    # Check 3: Content filter available
    print("\n[3/4] Content Filter Availability...")
    checks_total += 1

    try:
        content_filter = ContentFilterPipeline()
        print(f"✅ Content filter initialized")
        checks_passed += 1
        if verbose:
            print(f"   Filters loaded: {len(content_filter.filters) if hasattr(content_filter, 'filters') else 'N/A'}")
    except Exception as e:
        print(f"❌ Content filter initialization failed: {e}")

    # Check 4: Security directories exist
    print("\n[4/4] Security Storage...")
    checks_total += 1

    security_dirs = ['.aget', '.aget/cache', '.aget/versions']
    all_dirs_exist = all(Path(d).exists() for d in security_dirs)

    if all_dirs_exist:
        print(f"✅ Security directories exist")
        checks_passed += 1
        if verbose:
            for d in security_dirs:
                print(f"   - {d}")
    else:
        print(f"❌ Some security directories missing")
        if verbose:
            for d in security_dirs:
                status = "✅" if Path(d).exists() else "❌"
                print(f"   {status} {d}")

    # Summary
    print("\n" + "=" * 60)
    print(f"Security Checks: {checks_passed}/{checks_total} passed")

    if checks_passed == checks_total:
        print("✅ System security configuration validated")
        return True
    else:
        print("⚠️  Some security checks failed")
        return False


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Run security checks on documents and system configuration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check document for security issues
  python3 scripts/security_check.py /path/to/document.txt

  # Check system security configuration
  python3 scripts/security_check.py --check-config

  # Verbose security check
  python3 scripts/security_check.py document.txt --verbose
        """
    )

    parser.add_argument(
        'document',
        nargs='?',
        help='Path to document to check'
    )

    parser.add_argument(
        '--check-config',
        action='store_true',
        help='Check system security configuration'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed security check results'
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.document and not args.check_config:
        parser.print_help()
        print("\nError: Must provide either document path or --check-config option")
        sys.exit(1)

    # Execute
    try:
        if args.check_config:
            # System security check
            success = check_system_security(verbose=args.verbose)
        else:
            # Document security check
            success = check_document_security(args.document, verbose=args.verbose)

        sys.exit(0 if success else 1)

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
