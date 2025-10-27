#!/usr/bin/env python3
"""Metrics Collection CLI

Collect and display pipeline metrics (processing, LLM usage, cost, resource).

Usage:
    python3 scripts/metrics.py
    python3 scripts/metrics.py --detailed
    python3 scripts/metrics.py --export metrics.txt

Examples:
    # Show metrics summary
    python3 scripts/metrics.py

    # Show detailed metrics
    python3 scripts/metrics.py --detailed

    # Export metrics to file
    python3 scripts/metrics.py --export metrics.txt
"""

import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from pipeline.metrics_collector import MetricsCollector


def show_metrics_summary(collector: MetricsCollector):
    """Display metrics summary

    Args:
        collector: MetricsCollector instance
    """
    summary = collector.get_summary()

    print("Pipeline Metrics Summary")
    print("=" * 60)

    # Display summary
    for key, value in summary.items():
        if isinstance(value, float):
            if 'rate' in key or 'percent' in key:
                print(f"  {key}: {value:.2%}")
            elif 'cost' in key or 'usd' in key:
                print(f"  {key}: ${value:.4f}")
            else:
                print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")

    # Check budget alert
    alert = collector.check_budget_alert(threshold=80.0)
    if alert:
        print(f"\n⚠️  {alert}")


def show_metrics_detailed(collector: MetricsCollector):
    """Display detailed metrics

    Args:
        collector: MetricsCollector instance
    """
    print("Pipeline Metrics (Detailed)")
    print("=" * 60)

    # Get performance summary
    perf_summary = collector.get_performance_summary()
    print(f"\n{perf_summary}")


def export_metrics(collector: MetricsCollector, output_file: str):
    """Export metrics to file

    Args:
        collector: MetricsCollector instance
        output_file: Output file path
    """
    print(f"Exporting metrics to: {output_file}")

    # Export summary as JSON
    import json
    summary = collector.get_summary()

    with open(output_file, 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"✅ Metrics exported ({len(summary)} metrics)")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Collect and display pipeline metrics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show metrics summary
  python3 scripts/metrics.py

  # Show detailed metrics
  python3 scripts/metrics.py --detailed

  # Export metrics to file
  python3 scripts/metrics.py --export metrics.txt
        """
    )

    parser.add_argument(
        '--detailed', '-d',
        action='store_true',
        help='Show detailed metrics'
    )

    parser.add_argument(
        '--export',
        metavar='OUTPUT_FILE',
        help='Export metrics to file'
    )

    args = parser.parse_args()

    # Initialize metrics collector
    try:
        collector = MetricsCollector(monthly_budget=300.0)

        # Execute requested operation
        if args.export:
            export_metrics(collector, args.export)
        elif args.detailed:
            show_metrics_detailed(collector)
        else:
            show_metrics_summary(collector)

        sys.exit(0)

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
