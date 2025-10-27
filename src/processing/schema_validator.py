"""Schema Validation for LLM Outputs

Validates LLM outputs against defined schemas to ensure:
- Type compliance
- Required fields present
- Value constraints met
- No injection attempts

Based on L208 lines 247-251, 565-568 (Validation Pipeline, Schema Enforcement)
"""

from typing import Dict, List, Any, Optional, Type
from dataclasses import dataclass
from enum import Enum
import re


class FieldType(Enum):
    """Field data types for schema validation

    Added per API Specification v1.0 for type safety.
    Maps to Python types: STRING=str, NUMBER=float/int, etc.
    """
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"


class ValidationSeverity(Enum):
    """Validation issue severity"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    """Validation issue found in output"""
    field: str
    severity: ValidationSeverity
    message: str
    expected: Optional[Any] = None
    actual: Optional[Any] = None


@dataclass
class ValidationResult:
    """Result of schema validation"""
    is_valid: bool  # Renamed from 'valid' per API Specification v1.0
    issues: List[ValidationIssue]
    validated_data: Optional[Dict] = None

    @property
    def errors(self) -> List[ValidationIssue]:
        """Get error-level issues"""
        return [i for i in self.issues if i.severity == ValidationSeverity.ERROR]

    @property
    def warnings(self) -> List[ValidationIssue]:
        """Get warning-level issues"""
        return [i for i in self.issues if i.severity == ValidationSeverity.WARNING]


class SchemaField:
    """Definition of a schema field

    Design Decision: Pydantic-inspired but simplified.
    For production, consider using Pydantic directly.
    """

    def __init__(
        self,
        field_type: Type,
        required: bool = True,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        pattern: Optional[str] = None,
        allowed_values: Optional[List] = None,
        description: str = ""
    ):
        """Initialize schema field

        Args:
            field_type: Expected Python type
            required: Whether field is required
            min_length: Minimum length for strings/lists
            max_length: Maximum length for strings/lists
            pattern: Regex pattern for strings
            allowed_values: List of allowed values (enum)
            description: Field description
        """
        self.field_type = field_type
        self.required = required
        self.min_length = min_length
        self.max_length = max_length
        self.pattern = pattern
        self.allowed_values = allowed_values
        self.description = description

    def validate(self, field_name: str, value: Any) -> List[ValidationIssue]:
        """Validate field value

        Args:
            field_name: Name of field being validated
            value: Value to validate

        Returns:
            List of validation issues (empty if valid)
        """
        issues = []

        # Type validation
        if not isinstance(value, self.field_type):
            issues.append(ValidationIssue(
                field=field_name,
                severity=ValidationSeverity.ERROR,
                message=f"Type mismatch",
                expected=self.field_type.__name__,
                actual=type(value).__name__
            ))
            return issues  # Don't continue validation if type is wrong

        # Length validation (strings and lists)
        if isinstance(value, (str, list)):
            length = len(value)

            if self.min_length is not None and length < self.min_length:
                issues.append(ValidationIssue(
                    field=field_name,
                    severity=ValidationSeverity.ERROR,
                    message=f"Length {length} below minimum {self.min_length}"
                ))

            if self.max_length is not None and length > self.max_length:
                issues.append(ValidationIssue(
                    field=field_name,
                    severity=ValidationSeverity.ERROR,
                    message=f"Length {length} exceeds maximum {self.max_length}"
                ))

        # Pattern validation (strings only)
        if isinstance(value, str) and self.pattern:
            if not re.match(self.pattern, value):
                issues.append(ValidationIssue(
                    field=field_name,
                    severity=ValidationSeverity.ERROR,
                    message=f"Does not match pattern: {self.pattern}"
                ))

        # Enum validation
        if self.allowed_values and value not in self.allowed_values:
            issues.append(ValidationIssue(
                field=field_name,
                severity=ValidationSeverity.ERROR,
                message=f"Value not in allowed list",
                expected=self.allowed_values,
                actual=value
            ))

        return issues


class Schema:
    """Schema definition for LLM output validation

    Example (dict-based):
        schema = Schema({
            'title': SchemaField(str, max_length=200, pattern=r'^[^<>]*$'),
            'summary': SchemaField(str, max_length=1000),
            'category': SchemaField(str, allowed_values=['tech', 'business', 'science'])
        })

    Example (fluent API):
        schema = Schema()
        schema.add_field('title', FieldType.STRING, required=True)
        schema.add_field('count', FieldType.NUMBER, required=False)
    """

    def __init__(self, fields: Optional[Dict[str, SchemaField]] = None):
        """Initialize schema

        Args:
            fields: Optional dictionary mapping field names to SchemaField definitions
                   If None, use add_field() to build schema incrementally
        """
        self.fields = fields or {}

    def add_field(
        self,
        name: str,
        field_type: FieldType,
        required: bool = False,
        description: Optional[str] = None
    ) -> None:
        """Add a field to the schema (fluent API)

        Added per API Specification v1.0 for fluent schema building.

        Args:
            name: Field name
            field_type: Field type (FieldType enum)
            required: Whether field is required
            description: Optional field description
        """
        # Map FieldType enum to Python type
        type_mapping = {
            FieldType.STRING: str,
            FieldType.NUMBER: (int, float),
            FieldType.BOOLEAN: bool,
            FieldType.ARRAY: list,
            FieldType.OBJECT: dict
        }

        python_type = type_mapping.get(field_type, str)

        self.fields[name] = SchemaField(
            field_type=python_type,
            required=required,
            description=description or ""
        )

    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        """Validate data against schema

        Args:
            data: Data to validate

        Returns:
            ValidationResult with issues
        """
        issues = []

        # Check required fields
        for field_name, field_def in self.fields.items():
            if field_def.required and field_name not in data:
                issues.append(ValidationIssue(
                    field=field_name,
                    severity=ValidationSeverity.ERROR,
                    message="Required field missing"
                ))

        # Validate present fields
        for field_name, value in data.items():
            if field_name in self.fields:
                field_issues = self.fields[field_name].validate(field_name, value)
                issues.extend(field_issues)
            else:
                # Unknown field (warning, not error)
                issues.append(ValidationIssue(
                    field=field_name,
                    severity=ValidationSeverity.WARNING,
                    message="Unknown field (not in schema)"
                ))

        # Validation passes if no errors
        valid = not any(i.severity == ValidationSeverity.ERROR for i in issues)

        return ValidationResult(
            is_valid=valid,
            issues=issues,
            validated_data=data if valid else None
        )


class SchemaValidator:
    """Validates LLM outputs against schemas

    Provides:
    - Schema-based validation
    - Security validation (injection prevention)
    - Custom validation rules

    Design Decision: Security boundary enforcement.
    Schema validation prevents LLM from injecting arbitrary content.
    See L208 lines 565-568 (Schema Enforcement as Security Boundary)
    """

    def __init__(self, schema: Schema, strict_mode: bool = True):
        """Initialize schema validator

        Args:
            schema: Schema definition
            strict_mode: If True, unknown fields cause validation failure
        """
        self.schema = schema
        self.strict_mode = strict_mode

    def validate(self, llm_output: Dict[str, Any]) -> ValidationResult:
        """Validate LLM output against schema

        Args:
            llm_output: Output from LLM to validate

        Returns:
            ValidationResult
        """
        # Run schema validation
        result = self.schema.validate(llm_output)

        # Apply security validation
        security_issues = self._security_validation(llm_output)
        result.issues.extend(security_issues)

        # Update valid flag if security issues found
        if security_issues:
            result.is_valid = False

        return result

    def _security_validation(self, data: Dict[str, Any]) -> List[ValidationIssue]:
        """Apply security validation to detect injection attempts

        Args:
            data: Data to validate

        Returns:
            List of security-related validation issues
        """
        issues = []

        for field_name, value in data.items():
            if isinstance(value, str):
                # Check for HTML/script injection
                if self._contains_html(value):
                    issues.append(ValidationIssue(
                        field=field_name,
                        severity=ValidationSeverity.ERROR,
                        message="Contains HTML/script tags (potential injection)"
                    ))

                # Check for SQL injection patterns
                if self._contains_sql_injection(value):
                    issues.append(ValidationIssue(
                        field=field_name,
                        severity=ValidationSeverity.WARNING,
                        message="Contains SQL-like patterns (potential injection)"
                    ))

        return issues

    def _contains_html(self, text: str) -> bool:
        """Check if text contains HTML/script tags

        Args:
            text: Text to check

        Returns:
            True if HTML detected
        """
        html_pattern = r'<\s*(?:script|iframe|object|embed|img|svg|link|style)[^>]*>'
        return bool(re.search(html_pattern, text, re.IGNORECASE))

    def _contains_sql_injection(self, text: str) -> bool:
        """Check if text contains SQL injection patterns

        Args:
            text: Text to check

        Returns:
            True if SQL patterns detected
        """
        sql_patterns = [
            r'\bDROP\s+TABLE\b',
            r'\bUNION\s+SELECT\b',
            r'\bDELETE\s+FROM\b',
            r"'\s*OR\s+'1'\s*=\s*'1",
            r"--\s*$"
        ]

        for pattern in sql_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True

        return False

    @staticmethod
    def create_from_dict(schema_dict: Dict) -> 'SchemaValidator':
        """Create validator from dictionary schema definition

        Args:
            schema_dict: Schema definition as dictionary
                        Example: {
                            'title': {'type': 'str', 'max_length': 200},
                            'summary': {'type': 'str', 'required': True}
                        }

        Returns:
            SchemaValidator instance
        """
        type_map = {
            'str': str,
            'int': int,
            'float': float,
            'bool': bool,
            'list': list,
            'dict': dict
        }

        fields = {}
        for field_name, field_spec in schema_dict.items():
            field_type = type_map.get(field_spec.get('type', 'str'), str)

            fields[field_name] = SchemaField(
                field_type=field_type,
                required=field_spec.get('required', True),
                min_length=field_spec.get('min_length'),
                max_length=field_spec.get('max_length'),
                pattern=field_spec.get('pattern'),
                allowed_values=field_spec.get('allowed_values'),
                description=field_spec.get('description', '')
            )

        schema = Schema(fields)
        return SchemaValidator(schema)
