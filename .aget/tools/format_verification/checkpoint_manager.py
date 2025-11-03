"""
Checkpoint Manager for Multi-Stage Verification

Manages verification checkpoints across pipeline stages to detect
format loss at specific points (prevents late L245-type detection).
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import logging

from .verification_framework import FormatType, VerificationResult
from .docx_verifier import check_track_changes, check_comments

logger = logging.getLogger(__name__)


@dataclass
class Checkpoint:
    """
    Verification checkpoint capturing document state at specific stage.

    Attributes:
        name: Checkpoint identifier (e.g., "pre_modification", "post_translation")
        document_path: Path to document at this checkpoint
        timestamp: When checkpoint was created
        format_states: Dict of format type → (present, count, details)
    """
    name: str
    document_path: Path
    timestamp: datetime
    format_states: Dict[FormatType, tuple] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize checkpoint to dict."""
        return {
            "name": self.name,
            "document_path": str(self.document_path),
            "timestamp": self.timestamp.isoformat(),
            "format_states": {
                ft.value: {
                    "present": state[0],
                    "count": state[1],
                    "details": state[2],
                }
                for ft, state in self.format_states.items()
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Checkpoint':
        """Deserialize checkpoint from dict."""
        format_states = {}
        for ft_str, state_dict in data.get("format_states", {}).items():
            ft = FormatType(ft_str)
            format_states[ft] = (
                state_dict["present"],
                state_dict["count"],
                state_dict["details"],
            )

        return cls(
            name=data["name"],
            document_path=Path(data["document_path"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            format_states=format_states,
        )


def create_checkpoint(
    document_path: Path,
    checkpoint_name: str,
    format_types: List[FormatType] = None
) -> Checkpoint:
    """
    Create verification checkpoint for document at current state.

    Args:
        document_path: Path to document
        checkpoint_name: Identifier for this checkpoint (e.g., "pre_modification")
        format_types: List of format types to capture (default: Track Changes + Comments)

    Returns:
        Checkpoint with captured format states

    Example:
        # Create checkpoint before processing
        checkpoint = create_checkpoint('input.docx', 'pre_modification')

        # ... process document ...

        # Compare against checkpoint
        result = compare_checkpoints('output.docx', checkpoint)
        if not result.passed:
            logger.error(result.report())
    """
    if format_types is None:
        format_types = [FormatType.TRACK_CHANGES, FormatType.COMMENTS]

    document_path = Path(document_path)

    # Capture format states
    format_states = {}

    verifier_registry = {
        FormatType.TRACK_CHANGES: check_track_changes,
        FormatType.COMMENTS: check_comments,
    }

    for ft in format_types:
        verifier = verifier_registry.get(ft)
        if verifier:
            try:
                state = verifier(document_path)
                format_states[ft] = state
                logger.debug(f"Checkpoint '{checkpoint_name}': {ft.value} = {state[0]} ({state[1]} items)")
            except Exception as e:
                logger.exception(f"Error capturing {ft.value} state")
                format_states[ft] = (False, 0, {"error": str(e)})

    return Checkpoint(
        name=checkpoint_name,
        document_path=document_path,
        timestamp=datetime.now(),
        format_states=format_states,
    )


def compare_checkpoints(
    current_document_path: Path,
    previous_checkpoint: Checkpoint,
    format_types: List[FormatType] = None
) -> List[VerificationResult]:
    """
    Compare current document state against previous checkpoint.

    Args:
        current_document_path: Path to current document
        previous_checkpoint: Checkpoint to compare against
        format_types: List of format types to compare (default: all from checkpoint)

    Returns:
        List of VerificationResult (one per format type)

    Example:
        checkpoint = create_checkpoint('input.docx', 'pre_modification')
        # ... process document ...
        results = compare_checkpoints('output.docx', checkpoint)

        for result in results:
            if not result.passed:
                logger.error(result.report())
    """
    if format_types is None:
        format_types = list(previous_checkpoint.format_states.keys())

    current_document_path = Path(current_document_path)

    results = []

    verifier_registry = {
        FormatType.TRACK_CHANGES: check_track_changes,
        FormatType.COMMENTS: check_comments,
    }

    for ft in format_types:
        if ft not in previous_checkpoint.format_states:
            results.append(VerificationResult(
                passed=False,
                format_type=ft,
                message=f"{ft.value} not in checkpoint '{previous_checkpoint.name}'",
                details={"error": "missing_from_checkpoint"},
            ))
            continue

        previous_present, previous_count, previous_details = previous_checkpoint.format_states[ft]

        # Get current state
        verifier = verifier_registry.get(ft)
        if not verifier:
            results.append(VerificationResult(
                passed=False,
                format_type=ft,
                message=f"No verifier for {ft.value}",
                details={"error": "missing_verifier"},
            ))
            continue

        try:
            current_present, current_count, current_details = verifier(current_document_path)

            # Compare states
            if previous_present and not current_present:
                # Format lost (L245 failure mode)
                results.append(VerificationResult(
                    passed=False,
                    format_type=ft,
                    message=f"{ft.value} lost after checkpoint '{previous_checkpoint.name}' (L245 failure)",
                    details={
                        "checkpoint": previous_checkpoint.name,
                        "previous_count": previous_count,
                        "current_count": current_count,
                        "loss_rate": "100%",
                    },
                    evidence={
                        "previous": previous_details,
                        "current": current_details,
                    },
                ))

            elif previous_present and current_present:
                # Format preserved (check for partial loss)
                if current_count < previous_count:
                    loss_count = previous_count - current_count
                    loss_rate = f"{(loss_count / previous_count * 100):.1f}%"
                    results.append(VerificationResult(
                        passed=True,  # Still passing
                        format_type=ft,
                        message=f"{ft.value} partially preserved ({loss_rate} loss since '{previous_checkpoint.name}')",
                        details={
                            "checkpoint": previous_checkpoint.name,
                            "previous_count": previous_count,
                            "current_count": current_count,
                            "loss_count": loss_count,
                            "loss_rate": loss_rate,
                            "warning": "partial_loss",
                        },
                        evidence={
                            "previous": previous_details,
                            "current": current_details,
                        },
                    ))
                else:
                    # Fully preserved or increased
                    results.append(VerificationResult(
                        passed=True,
                        format_type=ft,
                        message=f"{ft.value} preserved since '{previous_checkpoint.name}' ({current_count} items)",
                        details={
                            "checkpoint": previous_checkpoint.name,
                            "previous_count": previous_count,
                            "current_count": current_count,
                        },
                    ))

            else:
                # Not present before or after (N/A)
                results.append(VerificationResult(
                    passed=True,
                    format_type=ft,
                    message=f"{ft.value} not applicable (not present at checkpoint '{previous_checkpoint.name}')",
                    details={
                        "checkpoint": previous_checkpoint.name,
                        "note": "not_applicable",
                    },
                ))

        except Exception as e:
            logger.exception(f"Error comparing {ft.value} against checkpoint")
            results.append(VerificationResult(
                passed=False,
                format_type=ft,
                message=f"Verification error: {str(e)}",
                details={"error": str(e)},
            ))

    return results


class CheckpointManager:
    """
    Manages multiple checkpoints across pipeline stages.

    Example usage:
        manager = CheckpointManager()

        # Stage 1: Input
        manager.add_checkpoint('input.docx', 'pre_modification')

        # Stage 2: After modification
        manager.add_checkpoint('modified.docx', 'post_modification')

        # Stage 3: After translation
        manager.add_checkpoint('translated.docx', 'post_translation')

        # Verify all stages
        all_results = manager.verify_all_checkpoints()

        # Or verify between specific checkpoints
        results = manager.verify_between('post_modification', 'post_translation')
    """

    def __init__(self):
        """Initialize empty checkpoint manager."""
        self.checkpoints: Dict[str, Checkpoint] = {}
        self.checkpoint_order: List[str] = []

    def add_checkpoint(
        self,
        document_path: Path,
        checkpoint_name: str,
        format_types: List[FormatType] = None
    ) -> Checkpoint:
        """
        Add checkpoint at current pipeline stage.

        Args:
            document_path: Path to document at this stage
            checkpoint_name: Identifier for checkpoint
            format_types: Format types to capture (default: Track Changes + Comments)

        Returns:
            Created Checkpoint
        """
        checkpoint = create_checkpoint(document_path, checkpoint_name, format_types)
        self.checkpoints[checkpoint_name] = checkpoint
        if checkpoint_name not in self.checkpoint_order:
            self.checkpoint_order.append(checkpoint_name)
        logger.info(f"Checkpoint '{checkpoint_name}' created for {document_path}")
        return checkpoint

    def verify_between(
        self,
        before_checkpoint_name: str,
        after_checkpoint_name: str
    ) -> List[VerificationResult]:
        """
        Verify preservation between two checkpoints.

        Args:
            before_checkpoint_name: Earlier checkpoint
            after_checkpoint_name: Later checkpoint

        Returns:
            List of VerificationResult
        """
        if before_checkpoint_name not in self.checkpoints:
            raise ValueError(f"Checkpoint '{before_checkpoint_name}' not found")
        if after_checkpoint_name not in self.checkpoints:
            raise ValueError(f"Checkpoint '{after_checkpoint_name}' not found")

        before = self.checkpoints[before_checkpoint_name]
        after = self.checkpoints[after_checkpoint_name]

        return compare_checkpoints(after.document_path, before)

    def verify_all_checkpoints(self) -> Dict[str, List[VerificationResult]]:
        """
        Verify preservation across all consecutive checkpoints.

        Returns:
            Dict mapping checkpoint transition → List[VerificationResult]
            Example: {"pre→post_modification": [...], "post_modification→post_translation": [...]}
        """
        all_results = {}

        for i in range(len(self.checkpoint_order) - 1):
            before_name = self.checkpoint_order[i]
            after_name = self.checkpoint_order[i + 1]

            transition = f"{before_name}→{after_name}"
            results = self.verify_between(before_name, after_name)
            all_results[transition] = results

            logger.info(f"Verified transition: {transition}")

        return all_results

    def save_checkpoints(self, output_path: Path):
        """Save all checkpoints to JSON file."""
        output_path = Path(output_path)
        data = {
            "checkpoint_order": self.checkpoint_order,
            "checkpoints": {
                name: checkpoint.to_dict()
                for name, checkpoint in self.checkpoints.items()
            },
        }
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved {len(self.checkpoints)} checkpoints to {output_path}")

    def load_checkpoints(self, input_path: Path):
        """Load checkpoints from JSON file."""
        input_path = Path(input_path)
        with open(input_path, 'r') as f:
            data = json.load(f)

        self.checkpoint_order = data["checkpoint_order"]
        self.checkpoints = {
            name: Checkpoint.from_dict(checkpoint_data)
            for name, checkpoint_data in data["checkpoints"].items()
        }
        logger.info(f"Loaded {len(self.checkpoints)} checkpoints from {input_path}")
