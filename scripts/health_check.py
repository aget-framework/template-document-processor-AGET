#!/usr/bin/env python3
"""System Health Check CLI

Verify system health and component availability.

Usage:
    python3 scripts/health_check.py
    python3 scripts/health_check.py --verbose

Examples:
    # Quick health check
    python3 scripts/health_check.py

    # Verbose health check with details
    python3 scripts/health_check.py --verbose
"""

import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


def check_directories(verbose: bool = False) -> bool:
    """Check required directories exist

    Args:
        verbose: Show detailed checks

    Returns:
        True if all checks pass
    """
    required_dirs = [
        '.aget',
        '.aget/cache',
        '.aget/versions',
        '.aget/output',
        'src',
        'configs'
    ]

    if verbose:
        print("\nDirectory Checks:")

    all_ok = True
    for dir_path in required_dirs:
        exists = Path(dir_path).exists()
        if verbose:
            status = "✅" if exists else "❌"
            print(f"  {status} {dir_path}")
        if not exists:
            all_ok = False

    return all_ok


def check_modules(verbose: bool = False) -> bool:
    """Check core modules can be imported

    Args:
        verbose: Show detailed checks

    Returns:
        True if all imports succeed
    """
    modules = [
        ('ingestion.validator', 'DocumentValidator'),
        ('ingestion.queue_manager', 'QueueManager'),
        ('processing.cache_manager', 'CacheManager'),
        ('processing.schema_validator', 'Schema'),
        ('output.version_manager', 'VersionManager'),
        ('output.publisher', 'Publisher'),
        ('pipeline.pipeline_runner', 'PipelineRunner'),
        ('pipeline.metrics_collector', 'MetricsCollector'),
        ('security.input_sanitizer', 'InputSanitizer')
    ]

    if verbose:
        print("\nModule Import Checks:")

    all_ok = True
    for module_name, class_name in modules:
        try:
            module = __import__(module_name, fromlist=[class_name])
            getattr(module, class_name)
            if verbose:
                print(f"  ✅ {module_name}.{class_name}")
        except ImportError as e:
            if verbose:
                print(f"  ❌ {module_name}.{class_name} - {e}")
            all_ok = False
        except AttributeError as e:
            if verbose:
                print(f"  ❌ {module_name}.{class_name} - {e}")
            all_ok = False

    return all_ok


def check_configs(verbose: bool = False) -> bool:
    """Check configuration files exist

    Args:
        verbose: Show detailed checks

    Returns:
        True if all configs exist
    """
    config_files = [
        'configs/llm_providers.yaml',
        'configs/validation_rules.yaml',
        'configs/orchestration.yaml',
        'configs/processing_limits.yaml',
        'configs/caching.yaml',
        'configs/security_policy.yaml',
        'configs/models.yaml',
        'configs/metrics.yaml'
    ]

    if verbose:
        print("\nConfiguration File Checks:")

    all_ok = True
    for config_file in config_files:
        exists = Path(config_file).exists()
        if verbose:
            status = "✅" if exists else "❌"
            print(f"  {status} {config_file}")
        if not exists:
            all_ok = False

    return all_ok


def check_queue_health(verbose: bool = False) -> bool:
    """Check queue manager health

    Args:
        verbose: Show detailed checks

    Returns:
        True if queue is healthy
    """
    try:
        from ingestion.queue_manager import QueueManager

        queue = QueueManager()
        status = queue.get_status()

        if verbose:
            print("\nQueue Health:")
            print(f"  Total items: {status['total']}")
            print(f"  Candidates: {status['candidates']}")
            print(f"  Pending: {status['pending']}")
            print(f"  Processed: {status['processed']}")
            print(f"  Failed: {status['failed']}")

        return True

    except Exception as e:
        if verbose:
            print(f"\n❌ Queue health check failed: {e}")
        return False


def check_cache_health(verbose: bool = False) -> bool:
    """Check cache manager health

    Args:
        verbose: Show detailed checks

    Returns:
        True if cache is healthy
    """
    try:
        from processing.cache_manager import CacheManager

        cache = CacheManager()
        stats = cache.get_stats()

        if verbose:
            print("\nCache Health:")
            print(f"  Total entries: {stats['total_entries']}")
            print(f"  Cache size: {stats['cache_size_mb']:.2f} MB")
            print(f"  Enabled: {stats['enabled']}")

        return True

    except Exception as e:
        if verbose:
            print(f"\n❌ Cache health check failed: {e}")
        return False


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Verify system health and component availability",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Quick health check
  python3 scripts/health_check.py

  # Verbose health check with details
  python3 scripts/health_check.py --verbose
        """
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed health check results'
    )

    args = parser.parse_args()

    print("System Health Check")
    print("=" * 60)

    # Run checks
    checks = {
        'Directories': check_directories(args.verbose),
        'Modules': check_modules(args.verbose),
        'Configs': check_configs(args.verbose),
        'Queue': check_queue_health(args.verbose),
        'Cache': check_cache_health(args.verbose)
    }

    # Summary
    print("\nHealth Check Summary:")
    print("-" * 60)

    all_passed = True
    for check_name, passed in checks.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {check_name}: {status}")
        if not passed:
            all_passed = False

    print("-" * 60)

    if all_passed:
        print("\n✅ All health checks passed")
        sys.exit(0)
    else:
        print("\n❌ Some health checks failed")
        sys.exit(1)


if __name__ == '__main__':
    main()
