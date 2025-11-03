"""
Unit tests for format_verification module.

Tests core verification logic preventing L245-type failures.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).parents[4] / '.aget' / 'tools'))

from format_verification import (
    VerificationResult,
    FormatType,
    verify_format_preserved,
    create_checkpoint,
    compare_checkpoints,
    format_verification_report,
)


class TestVerificationResult:
    """Test VerificationResult dataclass."""

    def test_verification_result_pass(self):
        """Test successful verification result."""
        result = VerificationResult(
            passed=True,
            format_type=FormatType.TRACK_CHANGES,
            message="Track Changes preserved",
            details={"count": 5},
        )

        assert result.passed is True
        assert result.format_type == FormatType.TRACK_CHANGES
        assert "preserved" in result.message
        assert result.details["count"] == 5

    def test_verification_result_fail(self):
        """Test failed verification result."""
        result = VerificationResult(
            passed=False,
            format_type=FormatType.TRACK_CHANGES,
            message="Track Changes lost (L245 failure)",
            details={"loss_rate": "100%"},
        )

        assert result.passed is False
        assert "lost" in result.message
        assert result.details["loss_rate"] == "100%"

    def test_verification_result_string(self):
        """Test string representation."""
        result = VerificationResult(
            passed=True,
            format_type=FormatType.COMMENTS,
            message="Comments preserved",
        )

        result_str = str(result)
        assert "PASS" in result_str or "✅" in result_str
        assert "comments" in result_str.lower()

    def test_verification_result_report(self):
        """Test detailed report generation."""
        result = VerificationResult(
            passed=False,
            format_type=FormatType.TRACK_CHANGES,
            message="Format lost",
            details={"before_count": 10, "after_count": 0},
            evidence={"before": {"insertions": 5, "deletions": 5}},
        )

        report = result.report()
        assert "FAIL" in report or "❌" in report
        assert "before_count" in report
        assert "10" in report


class TestFormatVerification:
    """Test format preservation verification."""

    @patch('format_verification.verification_framework.Path')
    def test_verify_format_preserved_missing_before_file(self, mock_path):
        """Test error when before file missing."""
        before_mock = MagicMock()
        before_mock.exists.return_value = False
        after_mock = MagicMock()
        after_mock.exists.return_value = True

        mock_path.side_effect = [before_mock, after_mock]

        def mock_verifier(path):
            return (False, 0, {})

        result = verify_format_preserved(
            "missing.docx",
            "after.docx",
            FormatType.TRACK_CHANGES,
            mock_verifier
        )

        assert result.passed is False
        assert "not found" in result.message.lower()

    @patch('format_verification.verification_framework.Path')
    def test_verify_format_preserved_missing_after_file(self, mock_path):
        """Test error when after file missing."""
        before_mock = MagicMock()
        before_mock.exists.return_value = True
        after_mock = MagicMock()
        after_mock.exists.return_value = False

        mock_path.side_effect = [before_mock, after_mock]

        def mock_verifier(path):
            return (True, 10, {"insertions": 5, "deletions": 5})

        result = verify_format_preserved(
            "before.docx",
            "missing.docx",
            FormatType.TRACK_CHANGES,
            mock_verifier
        )

        assert result.passed is False
        assert "not found" in result.message.lower()

    @patch('format_verification.verification_framework.Path')
    def test_verify_format_preserved_l245_failure(self, mock_path):
        """Test L245 failure mode (100% loss)."""
        before_mock = MagicMock()
        before_mock.exists.return_value = True
        after_mock = MagicMock()
        after_mock.exists.return_value = True

        mock_path.side_effect = [before_mock, after_mock]

        def mock_verifier(path):
            if path == before_mock:
                # Before: Has Track Changes
                return (True, 10, {"insertions": 5, "deletions": 5})
            else:
                # After: Lost Track Changes (L245 failure)
                return (False, 0, {})

        result = verify_format_preserved(
            before_mock,
            after_mock,
            FormatType.TRACK_CHANGES,
            mock_verifier
        )

        assert result.passed is False
        assert "lost" in result.message.lower()
        assert result.details["loss_rate"] == "100%"

    @patch('format_verification.verification_framework.Path')
    def test_verify_format_preserved_success(self, mock_path):
        """Test successful format preservation."""
        before_mock = MagicMock()
        before_mock.exists.return_value = True
        after_mock = MagicMock()
        after_mock.exists.return_value = True

        mock_path.side_effect = [before_mock, after_mock]

        def mock_verifier(path):
            # Both have Track Changes
            return (True, 10, {"insertions": 5, "deletions": 5})

        result = verify_format_preserved(
            before_mock,
            after_mock,
            FormatType.TRACK_CHANGES,
            mock_verifier
        )

        assert result.passed is True
        assert "preserved" in result.message.lower()

    @patch('format_verification.verification_framework.Path')
    def test_verify_format_preserved_partial_loss(self, mock_path):
        """Test partial format loss warning."""
        before_mock = MagicMock()
        before_mock.exists.return_value = True
        after_mock = MagicMock()
        after_mock.exists.return_value = True

        mock_path.side_effect = [before_mock, after_mock]

        call_count = [0]

        def mock_verifier(path):
            call_count[0] += 1
            if call_count[0] == 1:
                # Before: 10 Track Changes
                return (True, 10, {})
            else:
                # After: 5 Track Changes (50% loss)
                return (True, 5, {})

        result = verify_format_preserved(
            before_mock,
            after_mock,
            FormatType.TRACK_CHANGES,
            mock_verifier
        )

        assert result.passed is True  # Still passing
        assert "partially" in result.message.lower()
        assert result.details["warning"] == "partial_loss"


class TestCheckpointManager:
    """Test checkpoint creation and comparison."""

    @patch('format_verification.checkpoint_manager.check_track_changes')
    @patch('format_verification.checkpoint_manager.check_comments')
    @patch('format_verification.checkpoint_manager.Path')
    def test_create_checkpoint(self, mock_path, mock_check_comments, mock_check_track_changes):
        """Test checkpoint creation."""
        doc_path = MagicMock()
        doc_path.exists.return_value = True
        mock_path.return_value = doc_path

        # Mock verifier responses
        mock_check_track_changes.return_value = (True, 10, {"insertions": 5, "deletions": 5})
        mock_check_comments.return_value = (True, 3, {"authors": ["User1"]})

        checkpoint = create_checkpoint(
            doc_path,
            "pre_modification",
            format_types=[FormatType.TRACK_CHANGES, FormatType.COMMENTS]
        )

        assert checkpoint.name == "pre_modification"
        assert checkpoint.document_path == doc_path
        assert FormatType.TRACK_CHANGES in checkpoint.format_states
        assert FormatType.COMMENTS in checkpoint.format_states

        tc_state = checkpoint.format_states[FormatType.TRACK_CHANGES]
        assert tc_state[0] is True  # present
        assert tc_state[1] == 10  # count

    @patch('format_verification.checkpoint_manager.check_track_changes')
    @patch('format_verification.checkpoint_manager.Path')
    def test_compare_checkpoints_format_lost(self, mock_path, mock_check_track_changes):
        """Test checkpoint comparison detecting format loss."""
        # Create mock checkpoint
        from format_verification.checkpoint_manager import Checkpoint

        before_checkpoint = Checkpoint(
            name="pre_modification",
            document_path=Path("before.docx"),
            timestamp=datetime.now(),
            format_states={
                FormatType.TRACK_CHANGES: (True, 10, {"insertions": 5, "deletions": 5}),
            }
        )

        # Mock current state (format lost)
        mock_check_track_changes.return_value = (False, 0, {})

        current_path = MagicMock()
        current_path.exists.return_value = True
        mock_path.return_value = current_path

        results = compare_checkpoints(
            current_path,
            before_checkpoint,
            format_types=[FormatType.TRACK_CHANGES]
        )

        assert len(results) == 1
        assert results[0].passed is False
        assert "lost" in results[0].message.lower()


class TestReportFormatting:
    """Test report generation."""

    def test_format_verification_report_all_pass(self):
        """Test report formatting for all passing checks."""
        results = [
            VerificationResult(
                passed=True,
                format_type=FormatType.TRACK_CHANGES,
                message="Track Changes preserved (10 items)",
                details={"count": 10},
            ),
            VerificationResult(
                passed=True,
                format_type=FormatType.COMMENTS,
                message="Comments preserved (3 items)",
                details={"count": 3},
            ),
        ]

        report = format_verification_report(results)

        assert "2/2 checks passed" in report
        assert "All checks PASSED" in report or "✅" in report
        assert "track_changes" in report.lower()
        assert "comments" in report.lower()

    def test_format_verification_report_with_failures(self):
        """Test report formatting with failures."""
        results = [
            VerificationResult(
                passed=False,
                format_type=FormatType.TRACK_CHANGES,
                message="Track Changes lost",
                details={"loss_rate": "100%"},
            ),
            VerificationResult(
                passed=True,
                format_type=FormatType.COMMENTS,
                message="Comments preserved",
            ),
        ]

        report = format_verification_report(results)

        assert "1/2 checks passed" in report
        assert "FAILED" in report or "❌" in report
        assert "lost" in report.lower()


# Integration smoke test
class TestIntegration:
    """Integration smoke tests."""

    def test_module_import(self):
        """Test that all public APIs are importable."""
        from format_verification import (
            VerificationResult,
            FormatType,
            verify_track_changes,
            verify_comments,
            verify_round_trip,
            has_track_changes,
            has_comments,
            create_checkpoint,
            compare_checkpoints,
            CheckpointManager,
            format_verification_report,
            format_checkpoint_report,
        )

        # Verify all expected exports exist
        assert VerificationResult is not None
        assert FormatType is not None
        assert verify_track_changes is not None
        assert create_checkpoint is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


# Additional critical tests for improved coverage

class TestCriticalPaths:
    """Critical path tests for L245 prevention confidence."""

    @patch('format_verification.verification_framework.Path')
    def test_partial_format_loss_50_percent(self, mock_path):
        """Test 50% format loss detection."""
        before_mock = MagicMock()
        before_mock.exists.return_value = True
        after_mock = MagicMock()
        after_mock.exists.return_value = True

        mock_path.side_effect = [before_mock, after_mock]

        call_count = [0]

        def mock_verifier(path):
            call_count[0] += 1
            if call_count[0] == 1:
                return (True, 10, {})  # Before: 10 items
            else:
                return (True, 5, {})   # After: 5 items (50% loss)

        result = verify_format_preserved(
            before_mock, after_mock, FormatType.TRACK_CHANGES, mock_verifier
        )

        assert result.passed is True  # Still passing (not 100% loss)
        assert "partially" in result.message.lower()
        assert result.details["loss_rate"] == "50.0%"

    @patch('format_verification.verification_framework.Path')
    def test_partial_format_loss_90_percent(self, mock_path):
        """Test 90% format loss detection."""
        before_mock = MagicMock()
        before_mock.exists.return_value = True
        after_mock = MagicMock()
        after_mock.exists.return_value = True

        mock_path.side_effect = [before_mock, after_mock]

        call_count = [0]

        def mock_verifier(path):
            call_count[0] += 1
            if call_count[0] == 1:
                return (True, 10, {})  # Before: 10 items
            else:
                return (True, 1, {})   # After: 1 item (90% loss)

        result = verify_format_preserved(
            before_mock, after_mock, FormatType.TRACK_CHANGES, mock_verifier
        )

        assert result.passed is True
        assert "90.0%" in result.details["loss_rate"]

    @patch('format_verification.verification_framework.Path')
    def test_false_positive_prevention(self, mock_path):
        """Test that preserved formats don't trigger false positive."""
        before_mock = MagicMock()
        before_mock.exists.return_value = True
        after_mock = MagicMock()
        after_mock.exists.return_value = True

        mock_path.side_effect = [before_mock, after_mock]

        def mock_verifier(path):
            # Both have identical format state
            return (True, 10, {"insertions": 5, "deletions": 5})

        result = verify_format_preserved(
            before_mock, after_mock, FormatType.TRACK_CHANGES, mock_verifier
        )

        assert result.passed is True
        assert "preserved" in result.message.lower()
        assert "loss" not in result.message.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=.aget/tools/format_verification"])
