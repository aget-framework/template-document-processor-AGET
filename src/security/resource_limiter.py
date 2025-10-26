"""Resource Limiting for Document Processing

Enforces limits on:
- Token counts (prevent excessive API costs)
- Processing time (prevent hung processes)
- API call counts (prevent runaway loops)
- Cost budgets (prevent bill shock)

Based on L208 lines 570-576 (Security Protocols - Resource Protection)
"""

from typing import Optional, Callable
from dataclasses import dataclass
from enum import Enum
import time


class LimitType(Enum):
    """Types of resource limits"""
    TOKEN_COUNT = "token_count"
    TIME = "time"
    API_CALLS = "api_calls"
    COST = "cost"


@dataclass
class ResourceLimit:
    """Definition of a resource limit"""
    limit_type: LimitType
    limit_value: float
    current_value: float = 0.0

    @property
    def remaining(self) -> float:
        """Calculate remaining resources"""
        return max(0, self.limit_value - self.current_value)

    @property
    def percent_used(self) -> float:
        """Calculate percentage of limit used"""
        if self.limit_value == 0:
            return 0.0
        return (self.current_value / self.limit_value) * 100

    @property
    def exceeded(self) -> bool:
        """Check if limit has been exceeded"""
        return self.current_value >= self.limit_value


class ResourceLimitExceeded(Exception):
    """Exception raised when resource limit is exceeded"""

    def __init__(self, limit_type: LimitType, limit_value: float, current_value: float):
        """Initialize exception

        Args:
            limit_type: Type of limit exceeded
            limit_value: Limit threshold
            current_value: Current usage value
        """
        self.limit_type = limit_type
        self.limit_value = limit_value
        self.current_value = current_value

        message = (
            f"{limit_type.value} limit exceeded: "
            f"{current_value:.2f} >= {limit_value:.2f}"
        )
        super().__init__(message)


class ResourceLimiter:
    """Enforces resource limits during document processing

    Design Decision: Fail-fast approach - stop processing immediately
    when limit is exceeded to prevent runaway costs.

    Based on L208 lines 570-576 (Work Bounding implementation)
    """

    def __init__(
        self,
        max_tokens: Optional[int] = None,
        max_time_seconds: Optional[float] = None,
        max_api_calls: Optional[int] = None,
        max_cost_usd: Optional[float] = None
    ):
        """Initialize resource limiter

        Based on L208 line 575 (Example bounds)

        Args:
            max_tokens: Maximum input tokens (default: 10,000)
            max_time_seconds: Maximum processing time in seconds (default: 300 = 5 min)
            max_api_calls: Maximum number of API calls (default: 10)
            max_cost_usd: Maximum cost in USD (default: $1.00)
        """
        self.limits = {}

        if max_tokens is not None:
            self.limits[LimitType.TOKEN_COUNT] = ResourceLimit(
                LimitType.TOKEN_COUNT,
                max_tokens
            )
        else:
            self.limits[LimitType.TOKEN_COUNT] = ResourceLimit(
                LimitType.TOKEN_COUNT,
                10000  # Default: 10k tokens
            )

        if max_time_seconds is not None:
            self.limits[LimitType.TIME] = ResourceLimit(
                LimitType.TIME,
                max_time_seconds
            )
        else:
            self.limits[LimitType.TIME] = ResourceLimit(
                LimitType.TIME,
                300.0  # Default: 5 minutes
            )

        if max_api_calls is not None:
            self.limits[LimitType.API_CALLS] = ResourceLimit(
                LimitType.API_CALLS,
                max_api_calls
            )
        else:
            self.limits[LimitType.API_CALLS] = ResourceLimit(
                LimitType.API_CALLS,
                10  # Default: 10 calls
            )

        if max_cost_usd is not None:
            self.limits[LimitType.COST] = ResourceLimit(
                LimitType.COST,
                max_cost_usd
            )
        else:
            self.limits[LimitType.COST] = ResourceLimit(
                LimitType.COST,
                1.0  # Default: $1.00
            )

        self._start_time: Optional[float] = None

    def start_processing(self) -> None:
        """Start processing timer"""
        self._start_time = time.time()

    def check_token_limit(self, token_count: int) -> None:
        """Check if token count is within limit

        Args:
            token_count: Number of tokens to process

        Raises:
            ResourceLimitExceeded: If token limit would be exceeded
        """
        limit = self.limits[LimitType.TOKEN_COUNT]

        if token_count > limit.limit_value:
            raise ResourceLimitExceeded(
                LimitType.TOKEN_COUNT,
                limit.limit_value,
                token_count
            )

        limit.current_value = token_count

    def check_time_limit(self) -> None:
        """Check if processing time is within limit

        Raises:
            ResourceLimitExceeded: If time limit exceeded
        """
        if self._start_time is None:
            return

        elapsed = time.time() - self._start_time
        limit = self.limits[LimitType.TIME]

        if elapsed >= limit.limit_value:
            raise ResourceLimitExceeded(
                LimitType.TIME,
                limit.limit_value,
                elapsed
            )

        limit.current_value = elapsed

    def record_api_call(self) -> None:
        """Record an API call

        Raises:
            ResourceLimitExceeded: If API call limit exceeded
        """
        limit = self.limits[LimitType.API_CALLS]
        limit.current_value += 1

        if limit.exceeded:
            raise ResourceLimitExceeded(
                LimitType.API_CALLS,
                limit.limit_value,
                limit.current_value
            )

    def record_cost(self, cost_usd: float) -> None:
        """Record processing cost

        Args:
            cost_usd: Cost in USD

        Raises:
            ResourceLimitExceeded: If cost limit exceeded
        """
        limit = self.limits[LimitType.COST]
        limit.current_value += cost_usd

        if limit.exceeded:
            raise ResourceLimitExceeded(
                LimitType.COST,
                limit.limit_value,
                limit.current_value
            )

    def get_status(self) -> dict:
        """Get current resource usage status

        Returns:
            Dictionary with usage for all limits
        """
        return {
            limit_type.value: {
                'limit': limit.limit_value,
                'current': limit.current_value,
                'remaining': limit.remaining,
                'percent_used': limit.percent_used,
                'exceeded': limit.exceeded
            }
            for limit_type, limit in self.limits.items()
        }

    def reset(self) -> None:
        """Reset all counters"""
        for limit in self.limits.values():
            limit.current_value = 0.0
        self._start_time = None


class TimeoutContext:
    """Context manager for enforcing time limits

    Example:
        with TimeoutContext(max_seconds=60) as timer:
            # Processing code here
            timer.check()  # Raises TimeoutError if exceeded
    """

    def __init__(self, max_seconds: float, check_interval: float = 1.0):
        """Initialize timeout context

        Args:
            max_seconds: Maximum allowed time
            check_interval: How often to check (not enforced automatically)
        """
        self.max_seconds = max_seconds
        self.check_interval = check_interval
        self.start_time = None

    def __enter__(self):
        """Enter context"""
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context"""
        return False

    def check(self) -> None:
        """Check if timeout has occurred

        Raises:
            TimeoutError: If timeout exceeded
        """
        if self.start_time is None:
            return

        elapsed = time.time() - self.start_time
        if elapsed >= self.max_seconds:
            raise TimeoutError(
                f"Operation timed out after {elapsed:.2f} seconds "
                f"(limit: {self.max_seconds})"
            )

    @property
    def elapsed(self) -> float:
        """Get elapsed time

        Returns:
            Elapsed time in seconds
        """
        if self.start_time is None:
            return 0.0
        return time.time() - self.start_time


def with_resource_limits(
    func: Callable,
    max_tokens: int = 10000,
    max_time_seconds: float = 300,
    max_api_calls: int = 10,
    max_cost_usd: float = 1.0
) -> Callable:
    """Decorator to add resource limits to a function

    Example:
        @with_resource_limits(max_time_seconds=60, max_cost_usd=0.50)
        def process_document(doc):
            # Processing code
            pass

    Args:
        func: Function to wrap
        max_tokens: Token limit
        max_time_seconds: Time limit
        max_api_calls: API call limit
        max_cost_usd: Cost limit

    Returns:
        Wrapped function with resource limits
    """
    def wrapper(*args, **kwargs):
        limiter = ResourceLimiter(
            max_tokens=max_tokens,
            max_time_seconds=max_time_seconds,
            max_api_calls=max_api_calls,
            max_cost_usd=max_cost_usd
        )

        limiter.start_processing()

        try:
            result = func(*args, **kwargs, _limiter=limiter)
            return result
        except ResourceLimitExceeded as e:
            print(f"Resource limit exceeded: {e}")
            raise

    return wrapper
