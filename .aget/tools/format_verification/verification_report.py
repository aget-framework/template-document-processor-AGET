"""
Verification Report Formatting

Human-readable reports for verification results.
Helps debug L245-type failures with clear evidence presentation.
"""

from typing import List, Dict, Any
from .verification_framework import VerificationResult
from .checkpoint_manager import Checkpoint


def format_verification_report(results: List[VerificationResult]) -> str:
    """
    Format multiple verification results into human-readable report.

    Args:
        results: List of VerificationResult

    Returns:
        Formatted report string

    Example:
        results = verify_round_trip('input.docx', 'output.docx')
        print(format_verification_report(results))
    """
    lines = [
        "=" * 70,
        "FORMAT VERIFICATION REPORT",
        "=" * 70,
    ]

    # Summary
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    failed = total - passed

    lines.append(f"\nSummary: {passed}/{total} checks passed")
    if failed > 0:
        lines.append(f"⚠️  {failed} check(s) FAILED")
    else:
        lines.append("✅ All checks PASSED")

    # Individual results
    lines.append("\n" + "-" * 70)
    lines.append("Individual Results:")
    lines.append("-" * 70)

    for i, result in enumerate(results, 1):
        status_icon = "✅" if result.passed else "❌"
        lines.append(f"\n{i}. {status_icon} {result.format_type.value.upper()}")
        lines.append(f"   Status: {'PASS' if result.passed else 'FAIL'}")
        lines.append(f"   Message: {result.message}")

        if result.details:
            lines.append("   Details:")
            for key, value in result.details.items():
                if key == "warning" and value:
                    lines.append(f"     ⚠️  {key}: {value}")
                else:
                    lines.append(f"     {key}: {value}")

        if result.evidence and not result.passed:
            # Show evidence for failures
            lines.append("   Evidence:")
            for key, value in result.evidence.items():
                if isinstance(value, dict):
                    lines.append(f"     {key}:")
                    for k, v in value.items():
                        if isinstance(v, list) and len(v) > 3:
                            lines.append(f"       {k}: {len(v)} items")
                        else:
                            lines.append(f"       {k}: {v}")
                else:
                    lines.append(f"     {key}: {value}")

    lines.append("\n" + "=" * 70)

    return "\n".join(lines)


def format_checkpoint_report(
    checkpoint: Checkpoint,
    include_details: bool = True
) -> str:
    """
    Format checkpoint information into human-readable report.

    Args:
        checkpoint: Checkpoint to format
        include_details: Whether to include detailed format states

    Returns:
        Formatted checkpoint report

    Example:
        checkpoint = create_checkpoint('input.docx', 'pre_modification')
        print(format_checkpoint_report(checkpoint))
    """
    lines = [
        "=" * 70,
        f"CHECKPOINT: {checkpoint.name}",
        "=" * 70,
        f"Document: {checkpoint.document_path}",
        f"Timestamp: {checkpoint.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
        f"Formats Captured: {len(checkpoint.format_states)}",
    ]

    if include_details:
        lines.append("\n" + "-" * 70)
        lines.append("Format States:")
        lines.append("-" * 70)

        for format_type, (present, count, details) in checkpoint.format_states.items():
            status_icon = "✅" if present else "❌"
            lines.append(f"\n{status_icon} {format_type.value}:")
            lines.append(f"  Present: {present}")
            lines.append(f"  Count: {count}")

            if details:
                lines.append("  Details:")
                for key, value in details.items():
                    if isinstance(value, list) and len(value) > 3:
                        lines.append(f"    {key}: {len(value)} items")
                        for item in value[:3]:
                            lines.append(f"      - {item}")
                    else:
                        lines.append(f"    {key}: {value}")

    lines.append("\n" + "=" * 70)

    return "\n".join(lines)


def format_checkpoint_comparison_report(
    before_checkpoint: Checkpoint,
    after_checkpoint: Checkpoint,
    results: List[VerificationResult]
) -> str:
    """
    Format checkpoint comparison with verification results.

    Args:
        before_checkpoint: Earlier checkpoint
        after_checkpoint: Later checkpoint
        results: Verification results from comparison

    Returns:
        Formatted comparison report

    Example:
        cp1 = create_checkpoint('input.docx', 'pre_modification')
        # ... process ...
        cp2 = create_checkpoint('output.docx', 'post_modification')
        results = compare_checkpoints(cp2.document_path, cp1)
        print(format_checkpoint_comparison_report(cp1, cp2, results))
    """
    lines = [
        "=" * 70,
        "CHECKPOINT COMPARISON REPORT",
        "=" * 70,
        f"\nBefore: {before_checkpoint.name}",
        f"  Document: {before_checkpoint.document_path}",
        f"  Timestamp: {before_checkpoint.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
        f"\nAfter: {after_checkpoint.name}",
        f"  Document: {after_checkpoint.document_path}",
        f"  Timestamp: {after_checkpoint.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
    ]

    # Summary
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    failed = total - passed

    lines.append(f"\nVerification Results: {passed}/{total} checks passed")
    if failed > 0:
        lines.append(f"⚠️  {failed} check(s) FAILED - Format loss detected")
    else:
        lines.append("✅ All formats preserved")

    # Format changes
    lines.append("\n" + "-" * 70)
    lines.append("Format Changes:")
    lines.append("-" * 70)

    for result in results:
        status_icon = "✅" if result.passed else "❌"
        lines.append(f"\n{status_icon} {result.format_type.value}:")

        if result.details:
            before_count = result.details.get('previous_count', result.details.get('before_count', 'N/A'))
            current_count = result.details.get('current_count', result.details.get('after_count', 'N/A'))
            lines.append(f"  Before: {before_count}")
            lines.append(f"  After: {current_count}")

            if 'loss_count' in result.details:
                lines.append(f"  Loss: {result.details['loss_count']} ({result.details.get('loss_rate', 'N/A')})")

            if 'warning' in result.details:
                lines.append(f"  ⚠️  Warning: {result.details['warning']}")

        lines.append(f"  Message: {result.message}")

    lines.append("\n" + "=" * 70)

    return "\n".join(lines)


def format_pipeline_verification_report(
    checkpoint_results: Dict[str, List[VerificationResult]]
) -> str:
    """
    Format multi-stage pipeline verification results.

    Args:
        checkpoint_results: Dict mapping stage transition → verification results
                          (e.g., from CheckpointManager.verify_all_checkpoints())

    Returns:
        Formatted pipeline report

    Example:
        manager = CheckpointManager()
        manager.add_checkpoint('input.docx', 'pre_modification')
        # ... process ...
        manager.add_checkpoint('output.docx', 'post_modification')
        all_results = manager.verify_all_checkpoints()
        print(format_pipeline_verification_report(all_results))
    """
    lines = [
        "=" * 70,
        "PIPELINE VERIFICATION REPORT",
        "=" * 70,
        f"\nTotal Stages: {len(checkpoint_results)}",
    ]

    # Overall summary
    total_checks = sum(len(results) for results in checkpoint_results.values())
    total_passed = sum(
        sum(1 for r in results if r.passed)
        for results in checkpoint_results.values()
    )
    total_failed = total_checks - total_passed

    lines.append(f"Total Checks: {total_checks}")
    lines.append(f"Passed: {total_passed}/{total_checks}")

    if total_failed > 0:
        lines.append(f"⚠️  FAILED: {total_failed}/{total_checks} - Format loss detected in pipeline")
    else:
        lines.append("✅ All format checks PASSED")

    # Stage-by-stage results
    lines.append("\n" + "=" * 70)
    lines.append("Stage-by-Stage Results:")
    lines.append("=" * 70)

    for transition, results in checkpoint_results.items():
        stage_passed = sum(1 for r in results if r.passed)
        stage_total = len(results)
        stage_failed = stage_total - stage_passed

        status_icon = "✅" if stage_failed == 0 else "❌"
        lines.append(f"\n{status_icon} {transition}")
        lines.append(f"   Checks: {stage_passed}/{stage_total} passed")

        if stage_failed > 0:
            lines.append(f"   ⚠️  {stage_failed} format(s) lost in this stage:")
            for result in results:
                if not result.passed:
                    lines.append(f"      - {result.format_type.value}: {result.message}")
        else:
            lines.append("   ✅ All formats preserved")

    # Failed checks detail
    if total_failed > 0:
        lines.append("\n" + "=" * 70)
        lines.append("FAILED CHECKS DETAIL:")
        lines.append("=" * 70)

        for transition, results in checkpoint_results.items():
            failed_results = [r for r in results if not r.passed]
            if failed_results:
                lines.append(f"\n{transition}:")
                for result in failed_results:
                    lines.append(f"  ❌ {result.format_type.value}")
                    lines.append(f"     {result.message}")
                    if result.details:
                        for key, value in result.details.items():
                            if key in ['previous_count', 'current_count', 'loss_count', 'loss_rate']:
                                lines.append(f"     {key}: {value}")

    lines.append("\n" + "=" * 70)

    return "\n".join(lines)


def format_l245_failure_alert(result: VerificationResult) -> str:
    """
    Format L245-specific failure alert (100% format loss).

    Args:
        result: VerificationResult with failure

    Returns:
        L245 failure alert message

    Example:
        result = verify_track_changes('input.docx', 'output.docx')
        if not result.passed and result.details.get('loss_rate') == '100%':
            print(format_l245_failure_alert(result))
    """
    lines = [
        "⚠️" * 35,
        "🚨 L245 CATASTROPHIC FAILURE DETECTED 🚨",
        "⚠️" * 35,
        "",
        f"Format Type: {result.format_type.value.upper()}",
        f"Loss Rate: {result.details.get('loss_rate', 'UNKNOWN')}",
        "",
        "This is a catastrophic L245-type failure:",
        "- docx-AGET experienced 100% Track Changes loss (8/8 files)",
        "- 10 hours of work invalidated",
        "- User discovered failure, not worker/supervisor",
        "",
        "IMMEDIATE ACTIONS REQUIRED:",
        "1. STOP all processing immediately",
        "2. Review architecture decision (text-only vs format-preserving)",
        "3. Check if `.text` extraction used instead of OOXML manipulation",
        "4. Verify all intermediate files (not just final output)",
        "5. Consult FORMAT_PRESERVING_DECISION_PROTOCOL.md",
        "",
        f"Details: {result.message}",
        "",
        "⚠️" * 35,
    ]

    return "\n".join(lines)
