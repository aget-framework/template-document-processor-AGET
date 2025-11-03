"""
Core Verification Framework

Provides base classes and utilities for format verification.
Prevents L245-type failures (silent format loss).
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class FormatType(Enum):
    """Types of formats that can be verified."""
    TRACK_CHANGES = "track_changes"
    COMMENTS = "comments"
    TABLES = "tables"
    HEADINGS = "headings"
    HYPERLINKS = "hyperlinks"
    IMAGES = "images"
    STYLES = "styles"


@dataclass
class VerificationResult:
    """
    Result of format verification check.

    Attributes:
        passed: Whether verification passed
        format_type: Type of format verified
        message: Human-readable description
        details: Additional verification details
        evidence: Evidence of pass/fail (counts, examples, etc.)
    """
    passed: bool
    format_type: FormatType
    message: str
    details: Optional[Dict[str, Any]] = None
    evidence: Optional[Dict[str, Any]] = None

    def __str__(self) -> str:
        """Human-readable summary."""
        status = "✅ PASS" if self.passed else "❌ FAIL"
        return f"{status}: {self.format_type.value} - {self.message}"

    def report(self) -> str:
        """Detailed verification report."""
        lines = [
            f"{'='*60}",
            f"Format Verification: {self.format_type.value}",
            f"{'='*60}",
            f"Status: {'PASS ✅' if self.passed else 'FAIL ❌'}",
            f"Message: {self.message}",
        ]

        if self.details:
            lines.append("\nDetails:")
            for key, value in self.details.items():
                lines.append(f"  {key}: {value}")

        if self.evidence:
            lines.append("\nEvidence:")
            for key, value in self.evidence.items():
                if isinstance(value, list) and len(value) > 5:
                    lines.append(f"  {key}: {len(value)} items (showing first 5)")
                    for item in value[:5]:
                        lines.append(f"    - {item}")
                else:
                    lines.append(f"  {key}: {value}")

        lines.append(f"{'='*60}")
        return "\n".join(lines)


def verify_format_preserved(
    before_path: Path,
    after_path: Path,
    format_type: FormatType,
    verifier_func: callable
) -> VerificationResult:
    """
    Generic format preservation verification.

    Args:
        before_path: Path to document before processing
        after_path: Path to document after processing
        format_type: Type of format to verify
        verifier_func: Function that checks format presence
                      Should return (present: bool, count: int, details: dict)

    Returns:
        VerificationResult with pass/fail status and evidence

    Example:
        result = verify_format_preserved(
            'input.docx',
            'output.docx',
            FormatType.TRACK_CHANGES,
            check_track_changes_present
        )
        if not result.passed:
            logger.error(result.report())
    """
    before_path = Path(before_path)
    after_path = Path(after_path)

    # Validate paths exist
    if not before_path.exists():
        return VerificationResult(
            passed=False,
            format_type=format_type,
            message=f"Before file not found: {before_path}",
            details={"error": "missing_before_file"},
        )

    if not after_path.exists():
        return VerificationResult(
            passed=False,
            format_type=format_type,
            message=f"After file not found: {after_path}",
            details={"error": "missing_after_file"},
        )

    try:
        # Check before state
        before_present, before_count, before_details = verifier_func(before_path)

        # Check after state
        after_present, after_count, after_details = verifier_func(after_path)

        # Verify preservation
        if before_present and not after_present:
            # Format was present, now lost (L245 failure mode)
            return VerificationResult(
                passed=False,
                format_type=format_type,
                message=f"{format_type.value} lost during processing (L245 failure mode)",
                details={
                    "before_count": before_count,
                    "after_count": after_count,
                    "loss_rate": "100%",
                },
                evidence={
                    "before": before_details,
                    "after": after_details,
                },
            )

        elif before_present and after_present:
            # Format preserved
            if after_count < before_count:
                # Partial loss warning
                loss_count = before_count - after_count
                loss_rate = f"{(loss_count / before_count * 100):.1f}%"
                return VerificationResult(
                    passed=True,  # Still passing, but with warning
                    format_type=format_type,
                    message=f"{format_type.value} partially preserved ({loss_rate} loss)",
                    details={
                        "before_count": before_count,
                        "after_count": after_count,
                        "loss_count": loss_count,
                        "loss_rate": loss_rate,
                        "warning": "partial_loss",
                    },
                    evidence={
                        "before": before_details,
                        "after": after_details,
                    },
                )
            else:
                # Full preservation
                return VerificationResult(
                    passed=True,
                    format_type=format_type,
                    message=f"{format_type.value} preserved ({after_count} items)",
                    details={
                        "before_count": before_count,
                        "after_count": after_count,
                    },
                    evidence={
                        "before": before_details,
                        "after": after_details,
                    },
                )

        elif not before_present and not after_present:
            # No format in either (not applicable)
            return VerificationResult(
                passed=True,
                format_type=format_type,
                message=f"{format_type.value} not present (verification not applicable)",
                details={
                    "before_count": 0,
                    "after_count": 0,
                    "note": "no_format_to_preserve",
                },
            )

        else:  # not before_present and after_present
            # Format added (acceptable)
            return VerificationResult(
                passed=True,
                format_type=format_type,
                message=f"{format_type.value} added during processing ({after_count} items)",
                details={
                    "before_count": 0,
                    "after_count": after_count,
                    "note": "format_added",
                },
                evidence={
                    "after": after_details,
                },
            )

    except Exception as e:
        logger.exception(f"Verification error for {format_type.value}")
        return VerificationResult(
            passed=False,
            format_type=format_type,
            message=f"Verification error: {str(e)}",
            details={
                "error": type(e).__name__,
                "error_message": str(e),
            },
        )


def verify_multiple_formats(
    before_path: Path,
    after_path: Path,
    format_types: List[FormatType],
    verifier_registry: Dict[FormatType, callable]
) -> List[VerificationResult]:
    """
    Verify multiple format types in one pass.

    Args:
        before_path: Path to document before processing
        after_path: Path to document after processing
        format_types: List of format types to verify
        verifier_registry: Map of format type → verifier function

    Returns:
        List of VerificationResult (one per format type)

    Example:
        from format_verification.docx_verifier import (
            check_track_changes, check_comments
        )

        results = verify_multiple_formats(
            'input.docx',
            'output.docx',
            [FormatType.TRACK_CHANGES, FormatType.COMMENTS],
            {
                FormatType.TRACK_CHANGES: check_track_changes,
                FormatType.COMMENTS: check_comments,
            }
        )

        for result in results:
            if not result.passed:
                logger.error(result.report())
    """
    results = []

    for format_type in format_types:
        verifier_func = verifier_registry.get(format_type)
        if not verifier_func:
            results.append(VerificationResult(
                passed=False,
                format_type=format_type,
                message=f"No verifier registered for {format_type.value}",
                details={"error": "missing_verifier"},
            ))
            continue

        result = verify_format_preserved(
            before_path,
            after_path,
            format_type,
            verifier_func
        )
        results.append(result)

    return results


def aggregate_verification_results(results: List[VerificationResult]) -> Dict[str, Any]:
    """
    Aggregate multiple verification results into summary.

    Args:
        results: List of VerificationResult

    Returns:
        Summary dict with pass/fail counts, overall status

    Example:
        results = verify_multiple_formats(...)
        summary = aggregate_verification_results(results)
        print(f"Overall: {summary['overall_status']}")
        print(f"Passed: {summary['passed_count']}/{summary['total_count']}")
    """
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    failed = total - passed

    failed_formats = [r.format_type.value for r in results if not r.passed]

    return {
        "total_count": total,
        "passed_count": passed,
        "failed_count": failed,
        "pass_rate": f"{(passed / total * 100):.1f}%" if total > 0 else "N/A",
        "overall_status": "PASS" if failed == 0 else "FAIL",
        "failed_formats": failed_formats,
        "results": results,
    }
