"""
Format Verification Module for Document Processing

Prevents L245-type catastrophic failures (100% Track Changes loss, 10h waste).

Usage:
    from format_verification import verify_track_changes, create_checkpoint

    # Verify Track Changes present
    result = verify_track_changes('before.docx', 'after.docx')
    if not result.passed:
        print(result.report())

    # Or use checkpoint system
    checkpoint = create_checkpoint('input.docx', 'pre_modification')
    # ... process document ...
    result = verify_checkpoint('output.docx', checkpoint)

Version: 1.0.0 (template v3.0.0)
"""

from .verification_framework import (
    VerificationResult,
    verify_format_preserved,
    FormatType,
)

from .docx_verifier import (
    verify_track_changes,
    verify_comments,
    verify_round_trip,
    has_track_changes,
    has_comments,
    check_track_changes,
    check_comments,
    extract_track_changes_text,
)

from .checkpoint_manager import (
    create_checkpoint,
    compare_checkpoints,
    CheckpointManager,
)

from .verification_report import (
    format_verification_report,
    format_checkpoint_report,
    format_l245_failure_alert,
)

__version__ = "1.0.0"
__all__ = [
    # Core framework
    "VerificationResult",
    "verify_format_preserved",
    "FormatType",
    # DOCX verifiers
    "verify_track_changes",
    "verify_comments",
    "verify_round_trip",
    "has_track_changes",
    "has_comments",
    "check_track_changes",
    "check_comments",
    "extract_track_changes_text",
    # Checkpoint system
    "create_checkpoint",
    "compare_checkpoints",
    "CheckpointManager",
    # Reporting
    "format_verification_report",
    "format_checkpoint_report",
    "format_l245_failure_alert",
]
