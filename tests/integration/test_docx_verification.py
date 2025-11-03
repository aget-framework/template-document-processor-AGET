"""
Integration Tests for DOCX Format Verification

Tests verification framework with real DOCX files (not mocks).
Improves docx_verifier.py coverage from 15% to 60%+.
"""

import pytest
from pathlib import Path
import sys

# Add format_verification to path
sys.path.insert(0, str(Path(__file__).parents[2] / '.aget' / 'tools'))

from format_verification import (
    verify_track_changes,
    check_track_changes,
    has_track_changes,
    verify_round_trip,
    extract_track_changes_text,
    FormatType,
)


# Test fixtures location
FIXTURES_DIR = Path(__file__).parent.parent / 'fixtures'
TEST_WITH_TC = FIXTURES_DIR / 'test_with_track_changes.docx'
TEST_CLEAN = FIXTURES_DIR / 'test_clean.docx'


class TestDocxVerifierIntegration:
    """Integration tests with real DOCX files."""

    def test_check_track_changes_with_real_docx(self):
        """Test check_track_changes() with real DOCX containing Track Changes."""
        present, count, details = check_track_changes(TEST_WITH_TC)

        # Verify Track Changes detected
        assert present is True, "Should detect Track Changes in test file"
        assert count == 5, f"Expected 5 Track Changes (3 ins + 2 del), got {count}"

        # Verify details structure
        assert 'insertion_count' in details
        assert 'deletion_count' in details
        assert details['insertion_count'] == 3
        assert details['deletion_count'] == 2

    def test_check_track_changes_with_clean_docx(self):
        """Test check_track_changes() with clean DOCX (no Track Changes)."""
        present, count, details = check_track_changes(TEST_CLEAN)

        # Verify no Track Changes
        assert present is False, "Should not detect Track Changes in clean file"
        assert count == 0, f"Expected 0 Track Changes, got {count}"

    def test_has_track_changes_boolean_check(self):
        """Test has_track_changes() boolean API."""
        # File with Track Changes
        assert has_track_changes(TEST_WITH_TC) is True

        # Clean file
        assert has_track_changes(TEST_CLEAN) is False

    def test_verify_track_changes_preservation(self):
        """Test verify_track_changes() with before/after files."""
        # Case 1: Track Changes preserved (both files have Track Changes)
        result = verify_track_changes(TEST_WITH_TC, TEST_WITH_TC)
        assert result.passed is True, "Should pass when Track Changes preserved"
        assert "preserved" in result.message.lower()

    def test_verify_track_changes_loss_detection(self):
        """Test verify_track_changes() detects format loss (L245 failure mode)."""
        # Before: Has Track Changes, After: Clean (100% loss)
        result = verify_track_changes(TEST_WITH_TC, TEST_CLEAN)

        # Verify L245 failure detected
        assert result.passed is False, "Should fail when Track Changes lost"
        assert "lost" in result.message.lower()
        assert result.details['loss_rate'] == '100%', "Should detect 100% loss"
        assert result.format_type == FormatType.TRACK_CHANGES

    def test_extract_track_changes_text(self):
        """Test extract_track_changes_text() retrieves actual text content."""
        changes = extract_track_changes_text(TEST_WITH_TC)

        # Verify structure
        assert 'insertions' in changes
        assert 'deletions' in changes
        assert 'insertion_count' in changes
        assert 'deletion_count' in changes

        # Verify counts match check_track_changes()
        assert changes['insertion_count'] == 3
        assert changes['deletion_count'] == 2

        # Verify text extracted (not empty)
        assert len(changes['insertions']) > 0, "Should extract insertion text"
        assert len(changes['deletions']) > 0, "Should extract deletion text"

    def test_verify_round_trip_with_real_files(self):
        """Test verify_round_trip() multi-format verification."""
        # Test with Track Changes preservation
        results = verify_round_trip(
            TEST_WITH_TC,
            TEST_WITH_TC,
            format_types=[FormatType.TRACK_CHANGES]
        )

        assert len(results) == 1
        assert results[0].passed is True
        assert results[0].format_type == FormatType.TRACK_CHANGES

    def test_verify_round_trip_detects_loss(self):
        """Test verify_round_trip() detects format loss."""
        # Before: Track Changes, After: Clean
        results = verify_round_trip(
            TEST_WITH_TC,
            TEST_CLEAN,
            format_types=[FormatType.TRACK_CHANGES]
        )

        assert len(results) == 1
        assert results[0].passed is False
        assert "lost" in results[0].message.lower()


class TestDocxVerifierEdgeCases:
    """Edge case tests with real files."""

    def test_missing_file_handling(self):
        """Test verification handles missing files gracefully."""
        result = verify_track_changes(
            Path("nonexistent_before.docx"),
            TEST_CLEAN
        )

        assert result.passed is False
        assert "not found" in result.message.lower()

    def test_check_track_changes_nonexistent_file(self):
        """Test check_track_changes() with nonexistent file."""
        present, count, details = check_track_changes(Path("nonexistent.docx"))

        # Should handle gracefully
        assert present is False
        assert count == 0
        assert 'error' in details

    def test_extract_track_changes_missing_file(self):
        """Test extract_track_changes_text() handles missing file."""
        changes = extract_track_changes_text(Path("nonexistent.docx"))

        # Should return empty structure with error
        assert changes.get('insertions', []) == []
        assert changes.get('deletions', []) == []
        assert 'error' in changes


class TestL245FailurePrevention:
    """Tests specifically for L245 catastrophic failure prevention."""

    def test_l245_detection_100_percent_loss(self):
        """Test L245 failure mode: 100% Track Changes loss."""
        result = verify_track_changes(TEST_WITH_TC, TEST_CLEAN)

        # Critical L245 indicators
        assert result.passed is False
        assert result.details.get('loss_rate') == '100%'
        assert "lost" in result.message.lower()

        # Verify evidence captured
        assert result.evidence is not None
        assert 'before' in result.evidence
        assert 'after' in result.evidence

    def test_l245_prevention_with_checkpoint(self):
        """Test checkpoint system prevents L245 failures."""
        from format_verification import create_checkpoint, compare_checkpoints

        # Create checkpoint from file with Track Changes
        checkpoint = create_checkpoint(
            TEST_WITH_TC,
            "pre_processing",
            format_types=[FormatType.TRACK_CHANGES]
        )

        # Verify checkpoint captured Track Changes
        assert FormatType.TRACK_CHANGES in checkpoint.format_states
        tc_state = checkpoint.format_states[FormatType.TRACK_CHANGES]
        assert tc_state[0] is True  # present
        assert tc_state[1] == 5  # count

        # Compare against clean file (simulates format loss)
        results = compare_checkpoints(TEST_CLEAN, checkpoint)

        # Verify L245 failure detected by checkpoint comparison
        assert len(results) == 1
        assert results[0].passed is False
        assert "lost" in results[0].message.lower()


# End-to-end test: Complete workflow
class TestEndToEnd:
    """End-to-end integration tests."""

    def test_complete_verification_workflow(self):
        """Test complete workflow: check → verify → report."""
        # Step 1: Check if input has Track Changes
        has_tc = has_track_changes(TEST_WITH_TC)
        assert has_tc is True

        # Step 2: Verify preservation after processing
        result = verify_track_changes(TEST_WITH_TC, TEST_WITH_TC)
        assert result.passed is True

        # Step 3: Generate report
        report = result.report()
        assert "PASS" in report or "✅" in report

    def test_l245_detection_and_alert_workflow(self):
        """Test L245 detection → alert generation workflow."""
        from format_verification import format_l245_failure_alert

        # Detect L245 failure
        result = verify_track_changes(TEST_WITH_TC, TEST_CLEAN)
        assert not result.passed
        assert result.details.get('loss_rate') == '100%'

        # Generate L245 alert
        alert = format_l245_failure_alert(result)
        assert "L245 CATASTROPHIC FAILURE" in alert
        assert "STOP" in alert or "IMMEDIATE ACTIONS" in alert


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
