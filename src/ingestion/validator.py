"""Input Validation for Document Processing

Pre-processing validation to ensure documents meet requirements before LLM processing.

Based on L208 lines 247-251 (Validation Pipeline Architecture)
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import mimetypes


@dataclass
class ValidationResult:
    """Result of document validation"""
    valid: bool
    document_path: str
    errors: List[str]
    warnings: List[str]
    metadata: Dict

    @property
    def has_errors(self) -> bool:
        """Check if validation found errors"""
        return len(self.errors) > 0

    @property
    def has_warnings(self) -> bool:
        """Check if validation found warnings"""
        return len(self.warnings) > 0


class ValidationRule:
    """Base class for validation rules"""

    def validate(self, document_path: Path, metadata: Dict) -> Tuple[List[str], List[str]]:
        """Validate document

        Args:
            document_path: Path to document
            metadata: Document metadata

        Returns:
            Tuple of (errors, warnings)
        """
        raise NotImplementedError("Subclasses must implement validate()")


class FileSizeValidator(ValidationRule):
    """Validates document file size"""

    def __init__(self, max_bytes: int, warn_bytes: Optional[int] = None):
        """Initialize file size validator

        Args:
            max_bytes: Maximum allowed file size (hard limit)
            warn_bytes: Warning threshold (optional)
        """
        self.max_bytes = max_bytes
        self.warn_bytes = warn_bytes or int(max_bytes * 0.8)

    def validate(self, document_path: Path, metadata: Dict) -> Tuple[List[str], List[str]]:
        errors = []
        warnings = []

        if not document_path.exists():
            errors.append(f"File not found: {document_path}")
            return errors, warnings

        size = document_path.stat().st_size
        metadata['size_bytes'] = size

        if size > self.max_bytes:
            errors.append(
                f"File size {size:,} bytes exceeds maximum {self.max_bytes:,} bytes"
            )
        elif size > self.warn_bytes:
            warnings.append(
                f"File size {size:,} bytes is large (threshold: {self.warn_bytes:,} bytes)"
            )

        return errors, warnings


class FileFormatValidator(ValidationRule):
    """Validates document file format"""

    def __init__(self, allowed_extensions: List[str], allowed_mimetypes: Optional[List[str]] = None):
        """Initialize file format validator

        Args:
            allowed_extensions: List of allowed file extensions (e.g., ['.pdf', '.docx'])
            allowed_mimetypes: Optional list of allowed MIME types
        """
        self.allowed_extensions = [ext.lower() for ext in allowed_extensions]
        self.allowed_mimetypes = allowed_mimetypes

    def validate(self, document_path: Path, metadata: Dict) -> Tuple[List[str], List[str]]:
        errors = []
        warnings = []

        # Check extension
        extension = document_path.suffix.lower()
        metadata['extension'] = extension

        if extension not in self.allowed_extensions:
            errors.append(
                f"File extension '{extension}' not allowed. "
                f"Allowed: {', '.join(self.allowed_extensions)}"
            )
            return errors, warnings

        # Check MIME type if specified
        if self.allowed_mimetypes:
            mime_type, _ = mimetypes.guess_type(str(document_path))
            metadata['mime_type'] = mime_type

            if mime_type and mime_type not in self.allowed_mimetypes:
                errors.append(
                    f"MIME type '{mime_type}' not allowed. "
                    f"Allowed: {', '.join(self.allowed_mimetypes)}"
                )

        return errors, warnings


class FileExistsValidator(ValidationRule):
    """Validates document file exists and is readable"""

    def validate(self, document_path: Path, metadata: Dict) -> Tuple[List[str], List[str]]:
        errors = []
        warnings = []

        if not document_path.exists():
            errors.append(f"File not found: {document_path}")
            return errors, warnings

        if not document_path.is_file():
            errors.append(f"Path is not a file: {document_path}")
            return errors, warnings

        # Try to read first few bytes
        try:
            with open(document_path, 'rb') as f:
                f.read(1024)
        except PermissionError:
            errors.append(f"File not readable (permission denied): {document_path}")
        except Exception as e:
            errors.append(f"File not readable: {e}")

        return errors, warnings


class DocumentValidator:
    """Validates documents before processing

    Runs a series of validation rules and aggregates results.

    Design Decision: Validator is configurable via rules list.
    Agent-specific validators should extend ValidationRule base class.
    """

    def __init__(self, rules: Optional[List[ValidationRule]] = None):
        """Initialize document validator

        Args:
            rules: List of validation rules to apply (default: basic validation)
        """
        # Explicit None check to allow empty list (rules=[])
        self.rules = rules if rules is not None else self._default_rules()

    def _default_rules(self) -> List[ValidationRule]:
        """Default validation rules

        Returns:
            List of default validators
        """
        return [
            FileExistsValidator(),
            FileSizeValidator(max_bytes=10_485_760),  # 10MB default
            FileFormatValidator(allowed_extensions=['.txt', '.md', '.pdf', '.docx'])
        ]

    def validate(self, document_path: str) -> ValidationResult:
        """Validate a document

        Args:
            document_path: Path to document to validate

        Returns:
            ValidationResult with errors, warnings, and metadata
        """
        path = Path(document_path)
        all_errors = []
        all_warnings = []
        metadata = {}

        # Run all validation rules
        for rule in self.rules:
            try:
                errors, warnings = rule.validate(path, metadata)
                all_errors.extend(errors)
                all_warnings.extend(warnings)
            except Exception as e:
                all_errors.append(f"Validation rule failed: {type(rule).__name__}: {e}")

        return ValidationResult(
            valid=len(all_errors) == 0,
            document_path=str(path),
            errors=all_errors,
            warnings=all_warnings,
            metadata=metadata
        )

    def validate_batch(self, document_paths: List[str]) -> List[ValidationResult]:
        """Validate multiple documents

        Args:
            document_paths: List of document paths to validate

        Returns:
            List of validation results
        """
        return [self.validate(path) for path in document_paths]

    def add_rule(self, rule: ValidationRule) -> None:
        """Add a validation rule

        Args:
            rule: Validation rule to add
        """
        self.rules.append(rule)

    def remove_rule(self, rule_type: type) -> None:
        """Remove validation rules of a specific type

        Args:
            rule_type: Type of rule to remove
        """
        self.rules = [r for r in self.rules if not isinstance(r, rule_type)]
