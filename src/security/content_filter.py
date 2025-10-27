"""Content Filtering for Input and Output

Filters content for safety, detecting:
- Personally Identifiable Information (PII)
- Profanity and hate speech
- Sensitive data (credentials, API keys)
- Malicious content

Based on L208 lines 549-568 (Security Protocols - Content Filtering)
"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import re


class FilterSeverity(Enum):
    """Severity of content filter matches"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class FilterMatch:
    """Represents a content filter match"""
    filter_name: str
    severity: FilterSeverity
    matched_text: str
    position: int
    reason: str


class BaseContentFilter:
    """Base class for content filters"""

    def __init__(self, severity: FilterSeverity = FilterSeverity.WARNING):
        """Initialize content filter

        Args:
            severity: Severity level for matches
        """
        self.severity = severity

    def scan(self, text: str) -> List[FilterMatch]:
        """Scan text for filter matches

        Args:
            text: Text to scan

        Returns:
            List of filter matches

        Raises:
            NotImplementedError: Subclasses must implement
        """
        raise NotImplementedError("Subclasses must implement scan()")


class PIIFilter(BaseContentFilter):
    """Detects Personally Identifiable Information

    Detects:
    - Email addresses
    - Phone numbers
    - Social Security Numbers
    - Credit card numbers

    Based on L208 line 560 (Detect private data leaks)
    """

    def scan(self, text: str) -> List[FilterMatch]:
        """Scan for PII

        Args:
            text: Text to scan

        Returns:
            List of PII matches
        """
        matches = []

        # Email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        for match in re.finditer(email_pattern, text):
            matches.append(FilterMatch(
                filter_name="email",
                severity=FilterSeverity.WARNING,
                matched_text=match.group(),
                position=match.start(),
                reason="Email address detected"
            ))

        # Phone numbers (US format)
        phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        for match in re.finditer(phone_pattern, text):
            matches.append(FilterMatch(
                filter_name="phone",
                severity=FilterSeverity.WARNING,
                matched_text=match.group(),
                position=match.start(),
                reason="Phone number detected"
            ))

        # SSN (US Social Security Number)
        ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b'
        for match in re.finditer(ssn_pattern, text):
            matches.append(FilterMatch(
                filter_name="ssn",
                severity=FilterSeverity.CRITICAL,
                matched_text=match.group(),
                position=match.start(),
                reason="Social Security Number detected"
            ))

        # Credit card numbers (simple detection)
        cc_pattern = r'\b(?:\d{4}[-\s]?){3}\d{4}\b'
        for match in re.finditer(cc_pattern, text):
            matches.append(FilterMatch(
                filter_name="credit_card",
                severity=FilterSeverity.CRITICAL,
                matched_text=match.group(),
                position=match.start(),
                reason="Potential credit card number detected"
            ))

        return matches


class CredentialFilter(BaseContentFilter):
    """Detects credentials and API keys

    Detects:
    - API keys
    - Passwords
    - Authentication tokens

    Based on L208 line 560 (Detect credentials)
    """

    def scan(self, text: str) -> List[FilterMatch]:
        """Scan for credentials

        Args:
            text: Text to scan

        Returns:
            List of credential matches
        """
        matches = []

        # API keys (common patterns)
        api_key_patterns = [
            r'api[_-]?key["\s:=]+([A-Za-z0-9_-]{20,})',
            r'token["\s:=]+([A-Za-z0-9_-]{20,})',
            r'sk-[A-Za-z0-9]{32,}',  # OpenAI style
            r'AIza[A-Za-z0-9_-]{35}',  # Google API key style
        ]

        for pattern in api_key_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                matches.append(FilterMatch(
                    filter_name="api_key",
                    severity=FilterSeverity.CRITICAL,
                    matched_text=match.group(1) if match.groups() else match.group(),
                    position=match.start(),
                    reason="API key or token detected"
                ))

        # Password patterns
        password_pattern = r'password["\s:=]+([^\s"\']{6,})'
        for match in re.finditer(password_pattern, text, re.IGNORECASE):
            matches.append(FilterMatch(
                filter_name="password",
                severity=FilterSeverity.CRITICAL,
                matched_text="[REDACTED]",  # Don't store actual password
                position=match.start(),
                reason="Password detected"
            ))

        return matches


class ProfanityFilter(BaseContentFilter):
    """Detects profanity and hate speech

    Design Decision: Simple word list for template.
    Production should use comprehensive hate speech detection API.

    Based on L208 line 551 (Screen for disallowed content)
    """

    def __init__(self, severity: FilterSeverity = FilterSeverity.WARNING):
        """Initialize profanity filter

        Args:
            severity: Severity level for matches
        """
        super().__init__(severity)
        # Minimal list for template - expand for production
        self.profanity_list = [
            "damn", "hell", "crap"  # Very mild examples for template
        ]

    def scan(self, text: str) -> List[FilterMatch]:
        """Scan for profanity

        Args:
            text: Text to scan

        Returns:
            List of profanity matches
        """
        matches = []
        text_lower = text.lower()

        for word in self.profanity_list:
            pattern = r'\b' + re.escape(word) + r'\b'
            for match in re.finditer(pattern, text_lower):
                matches.append(FilterMatch(
                    filter_name="profanity",
                    severity=self.severity,
                    matched_text=word,
                    position=match.start(),
                    reason="Profanity detected"
                ))

        return matches


class MaliciousContentFilter(BaseContentFilter):
    """Detects potentially malicious content

    Detects:
    - HTML/JavaScript injection attempts
    - SQL injection patterns
    - Command injection attempts

    Based on L208 lines 553, 561 (Detect code injection)
    """

    def scan(self, text: str) -> List[FilterMatch]:
        """Scan for malicious content

        Args:
            text: Text to scan

        Returns:
            List of malicious content matches
        """
        matches = []

        # HTML/Script tags
        html_pattern = r'<\s*(?:script|iframe|object|embed|img|svg|link|style)[^>]*>'
        for match in re.finditer(html_pattern, text, re.IGNORECASE):
            matches.append(FilterMatch(
                filter_name="html_injection",
                severity=FilterSeverity.CRITICAL,
                matched_text=match.group(),
                position=match.start(),
                reason="HTML/JavaScript tag detected"
            ))

        # SQL injection patterns
        sql_patterns = [
            r'\bDROP\s+TABLE\b',
            r'\bUNION\s+SELECT\b',
            r'\bDELETE\s+FROM\b',
            r"'\s*OR\s+'1'\s*=\s*'1",
        ]

        for pattern in sql_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                matches.append(FilterMatch(
                    filter_name="sql_injection",
                    severity=FilterSeverity.CRITICAL,
                    matched_text=match.group(),
                    position=match.start(),
                    reason="SQL injection pattern detected"
                ))

        # Command injection (shell commands)
        command_patterns = [
            r';\s*(?:rm|del|rmdir)\s',
            r'\|\s*(?:bash|sh|cmd)',
            r'`.*`',  # Backtick command substitution
        ]

        for pattern in command_patterns:
            for match in re.finditer(pattern, text):
                matches.append(FilterMatch(
                    filter_name="command_injection",
                    severity=FilterSeverity.CRITICAL,
                    matched_text=match.group(),
                    position=match.start(),
                    reason="Command injection pattern detected"
                ))

        return matches


class ContentFilterPipeline:
    """Runs multiple content filters in sequence

    Design Decision: Pipeline pattern for composable filtering.
    Agent-specific filters can be added to the pipeline.

    Based on L208 lines 549-568 (Content Filtering implementation)
    """

    def __init__(self, filters: Optional[List[BaseContentFilter]] = None):
        """Initialize content filter pipeline

        Args:
            filters: List of filters to apply (uses defaults if None)
        """
        self.filters = filters or self._default_filters()

    def _default_filters(self) -> List[BaseContentFilter]:
        """Get default filter set

        Returns:
            List of default content filters
        """
        return [
            PIIFilter(severity=FilterSeverity.WARNING),
            CredentialFilter(severity=FilterSeverity.CRITICAL),
            ProfanityFilter(severity=FilterSeverity.WARNING),
            MaliciousContentFilter(severity=FilterSeverity.CRITICAL)
        ]

    def scan(self, text: str) -> Tuple[bool, List[FilterMatch]]:
        """Scan text through all filters

        Args:
            text: Text to scan

        Returns:
            Tuple of (passed: bool, matches: List[FilterMatch])
            passed=True if no critical issues found
        """
        all_matches = []

        for filter_obj in self.filters:
            matches = filter_obj.scan(text)
            all_matches.extend(matches)

        # Check if any critical matches
        has_critical = any(m.severity == FilterSeverity.CRITICAL for m in all_matches)
        passed = not has_critical

        return passed, all_matches

    def scan_and_redact(self, text: str) -> Tuple[str, List[FilterMatch]]:
        """Scan text and redact sensitive content

        Args:
            text: Text to scan and redact

        Returns:
            Tuple of (redacted_text: str, matches: List[FilterMatch])
        """
        passed, matches = self.scan(text)

        redacted_text = text
        # Sort matches by position (descending) so replacements don't affect indices
        sorted_matches = sorted(matches, key=lambda m: m.position, reverse=True)

        for match in sorted_matches:
            if match.severity == FilterSeverity.CRITICAL:
                # Redact critical content
                start = match.position
                end = start + len(match.matched_text)
                redacted_text = redacted_text[:start] + f"[REDACTED:{match.filter_name}]" + redacted_text[end:]

        return redacted_text, matches

    def add_filter(self, filter_obj: BaseContentFilter) -> None:
        """Add a filter to the pipeline

        Args:
            filter_obj: Filter to add
        """
        self.filters.append(filter_obj)

    def get_summary(self, matches: List[FilterMatch]) -> Dict[str, int]:
        """Get summary of filter matches

        Args:
            matches: List of filter matches

        Returns:
            Dictionary with match counts by filter name
        """
        from collections import Counter

        filter_counts = Counter(m.filter_name for m in matches)
        severity_counts = Counter(m.severity.value for m in matches)

        return {
            'total_matches': len(matches),
            'by_filter': dict(filter_counts),
            'by_severity': dict(severity_counts),
            'has_critical': any(m.severity == FilterSeverity.CRITICAL for m in matches)
        }
