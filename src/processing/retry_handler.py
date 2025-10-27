"""Retry Logic with Exponential Backoff

Handles transient failures in LLM API calls with:
- Exponential backoff
- Configurable retry limits
- Error classification (retryable vs non-retryable)
- Jitter to prevent thundering herd

Based on L208 lines 27-32 (LLM-Powered Processing Pipeline - Retry logic)
"""

from typing import Callable, Optional, List, Any
from dataclasses import dataclass
from enum import Enum
import time
import random


class ErrorType(Enum):
    """Classification of errors"""
    RATE_LIMIT = "rate_limit"          # 429 Too Many Requests
    TIMEOUT = "timeout"                # Request timeout
    SERVER_ERROR = "server_error"      # 5xx errors
    NETWORK_ERROR = "network_error"    # Connection failures
    CLIENT_ERROR = "client_error"      # 4xx errors (not retryable)
    UNKNOWN = "unknown"


@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    max_attempts: int = 3              # Renamed from 'max_retries' for API consistency
    base_delay: float = 1.0            # Renamed from 'initial_delay' for API consistency
    max_delay: float = 60.0            # Maximum delay in seconds
    exponential_base: float = 2.0      # Multiplier for exponential backoff
    jitter: bool = True                # Add randomness to prevent thundering herd
    retryable_errors: List[ErrorType] = None

    def __post_init__(self):
        """Set default retryable errors"""
        if self.retryable_errors is None:
            self.retryable_errors = [
                ErrorType.RATE_LIMIT,
                ErrorType.TIMEOUT,
                ErrorType.SERVER_ERROR,
                ErrorType.NETWORK_ERROR,
                ErrorType.UNKNOWN  # Default to retryable for safety
            ]


@dataclass
class RetryResult:
    """Result of retry operation"""
    success: bool
    result: Any = None
    error: Optional[Exception] = None
    attempts: int = 0
    total_delay: float = 0.0


class RetryHandler:
    """Handles retry logic with exponential backoff

    Design Decision: Exponential backoff with jitter.
    - Exponential: Delay doubles with each retry (1s → 2s → 4s → 8s)
    - Jitter: Random variation prevents synchronized retries across clients
    - Classification: Only retry transient errors, not client errors

    Example:
        handler = RetryHandler()
        result = handler.retry(lambda: api_call())
    """

    def __init__(self, config: Optional[RetryConfig] = None):
        """Initialize retry handler

        Args:
            config: Retry configuration (uses defaults if None)
        """
        self.config = config or RetryConfig()

    def retry(
        self,
        func: Callable,
        error_classifier: Optional[Callable[[Exception], ErrorType]] = None
    ) -> RetryResult:
        """Execute function with retry logic

        Args:
            func: Function to execute (should take no arguments)
            error_classifier: Function to classify exceptions into ErrorType
                            If None, uses default classifier

        Returns:
            RetryResult with outcome
        """
        classifier = error_classifier or self._default_error_classifier

        attempts = 0
        total_delay = 0.0
        last_error = None

        while attempts <= self.config.max_attempts:
            try:
                # Attempt execution
                result = func()
                return RetryResult(
                    success=True,
                    result=result,
                    attempts=attempts + 1,
                    total_delay=total_delay
                )

            except Exception as e:
                last_error = e
                attempts += 1

                # Classify error
                error_type = classifier(e)

                # Check if error is retryable
                if error_type not in self.config.retryable_errors:
                    # Non-retryable error, fail immediately
                    return RetryResult(
                        success=False,
                        error=e,
                        attempts=attempts,
                        total_delay=total_delay
                    )

                # Check if max retries exceeded
                if attempts > self.config.max_attempts:
                    break

                # Calculate delay
                delay = self._calculate_delay(attempts)
                total_delay += delay

                # Wait before retry
                time.sleep(delay)

        # All retries exhausted
        return RetryResult(
            success=False,
            error=last_error,
            attempts=attempts,
            total_delay=total_delay
        )

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for current attempt

        Uses exponential backoff with optional jitter.

        Args:
            attempt: Current attempt number (1-indexed)

        Returns:
            Delay in seconds
        """
        # Exponential backoff: delay = base * (exponential_base ^ (attempt - 1))
        delay = self.config.base_delay * (self.config.exponential_base ** (attempt - 1))

        # Cap at max delay
        delay = min(delay, self.config.max_delay)

        # Add jitter if enabled
        if self.config.jitter:
            # Random value between 0 and delay
            delay = random.uniform(0, delay)

        return delay

    def _default_error_classifier(self, error: Exception) -> ErrorType:
        """Default error classification

        Args:
            error: Exception to classify

        Returns:
            ErrorType classification
        """
        error_msg = str(error).lower()

        # Rate limit errors
        if '429' in error_msg or 'rate limit' in error_msg or 'too many requests' in error_msg:
            return ErrorType.RATE_LIMIT

        # Timeout errors
        if 'timeout' in error_msg or 'timed out' in error_msg:
            return ErrorType.TIMEOUT

        # Server errors (5xx)
        if any(code in error_msg for code in ['500', '502', '503', '504']):
            return ErrorType.SERVER_ERROR

        # Network errors
        if any(term in error_msg for term in ['connection', 'network', 'dns']):
            return ErrorType.NETWORK_ERROR

        # Client errors (4xx, excluding 429)
        if any(code in error_msg for code in ['400', '401', '403', '404']):
            return ErrorType.CLIENT_ERROR

        # Unknown error type (default to retryable for safety)
        return ErrorType.UNKNOWN


class RetryDecorator:
    """Decorator for adding retry logic to functions

    Example:
        @RetryDecorator(max_retries=3)
        def call_api():
            return api.request()
    """

    def __init__(self, max_attempts: int = 3, base_delay: float = 1.0):
        """Initialize retry decorator

        Args:
            max_attempts: Maximum number of retry attempts
            base_delay: Base delay in seconds for exponential backoff
        """
        self.config = RetryConfig(max_attempts=max_attempts, base_delay=base_delay)
        self.handler = RetryHandler(self.config)

    def __call__(self, func: Callable) -> Callable:
        """Wrap function with retry logic

        Args:
            func: Function to wrap

        Returns:
            Wrapped function
        """
        def wrapper(*args, **kwargs):
            # Create a closure that captures args/kwargs
            def execute():
                return func(*args, **kwargs)

            result = self.handler.retry(execute)

            if result.success:
                return result.result
            else:
                raise result.error

        return wrapper


def with_retry(
    func: Callable,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    error_classifier: Optional[Callable[[Exception], ErrorType]] = None
) -> Any:
    """Helper function to retry a function call

    Args:
        func: Function to execute
        max_attempts: Maximum number of retry attempts
        base_delay: Base delay in seconds for exponential backoff
        error_classifier: Function to classify exceptions

    Returns:
        Function result

    Raises:
        Exception: If all retries fail

    Example:
        result = with_retry(lambda: api_call(), max_attempts=5)
    """
    config = RetryConfig(max_attempts=max_attempts, base_delay=base_delay)
    handler = RetryHandler(config)
    result = handler.retry(func, error_classifier)

    if result.success:
        return result.result
    else:
        raise result.error
