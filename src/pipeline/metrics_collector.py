"""Metrics Collection for Document Processing

Tracks and reports:
- Accuracy metrics (extraction quality, validation pass rate)
- Latency metrics (processing time, LLM API latency)
- Cost metrics (token usage, API spending)

Based on L208 lines 253-528 (Observability & Metrics)
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict
import time


@dataclass
class AccuracyMetrics:
    """Accuracy tracking for document processing

    Based on L208 lines 263-302 (Accuracy Metrics)
    """
    total_processed: int = 0
    successful_extractions: int = 0
    validation_passes: int = 0
    human_reviews_required: int = 0
    errors: int = 0

    @property
    def extraction_accuracy(self) -> float:
        """Calculate extraction accuracy percentage

        Returns:
            Accuracy as percentage (0-100)
        """
        if self.total_processed == 0:
            return 0.0
        return (self.successful_extractions / self.total_processed) * 100

    @property
    def validation_pass_rate(self) -> float:
        """Calculate validation pass rate percentage

        Returns:
            Pass rate as percentage (0-100)
        """
        if self.total_processed == 0:
            return 0.0
        return (self.validation_passes / self.total_processed) * 100

    @property
    def human_review_rate(self) -> float:
        """Calculate human review rate percentage

        Returns:
            Review rate as percentage (0-100)
        """
        if self.total_processed == 0:
            return 0.0
        return (self.human_reviews_required / self.total_processed) * 100

    @property
    def error_rate(self) -> float:
        """Calculate error rate percentage

        Returns:
            Error rate as percentage (0-100)
        """
        if self.total_processed == 0:
            return 0.0
        return (self.errors / self.total_processed) * 100


@dataclass
class LatencyMetrics:
    """Latency tracking for document processing

    Based on L208 lines 304-361 (Latency Metrics)
    """
    timings: Dict[str, List[float]] = field(default_factory=lambda: defaultdict(list))

    def record(self, stage: str, duration_seconds: float) -> None:
        """Record a timing measurement

        Args:
            stage: Processing stage name
            duration_seconds: Duration in seconds
        """
        self.timings[stage].append(duration_seconds)

    def get_stats(self, stage: str) -> Dict[str, float]:
        """Get statistics for a stage

        Args:
            stage: Stage name

        Returns:
            Dictionary with mean, min, max, p50, p95, p99
        """
        times = self.timings.get(stage, [])

        if not times:
            return {}

        sorted_times = sorted(times)
        count = len(sorted_times)

        return {
            'mean': sum(times) / count,
            'min': sorted_times[0],
            'max': sorted_times[-1],
            'p50': sorted_times[int(count * 0.50)],
            'p95': sorted_times[int(count * 0.95)] if count > 1 else sorted_times[0],
            'p99': sorted_times[int(count * 0.99)] if count > 1 else sorted_times[0],
            'count': count
        }


@dataclass
class CostMetrics:
    """Cost tracking for document processing

    Based on L208 lines 363-414 (Cost Metrics)
    """
    monthly_budget: float
    total_spent: float = 0.0
    documents_processed: int = 0
    token_usage: Dict[str, int] = field(default_factory=lambda: {'input': 0, 'output': 0})

    def record_llm_call(
        self,
        input_tokens: int,
        output_tokens: int,
        cost: float
    ) -> None:
        """Record an LLM API call

        Args:
            input_tokens: Input tokens used
            output_tokens: Output tokens used
            cost: Cost in USD
        """
        self.token_usage['input'] += input_tokens
        self.token_usage['output'] += output_tokens
        self.total_spent += cost
        self.documents_processed += 1

    @property
    def cost_per_document(self) -> float:
        """Calculate average cost per document

        Returns:
            Average cost in USD
        """
        if self.documents_processed == 0:
            return 0.0
        return self.total_spent / self.documents_processed

    @property
    def budget_utilization(self) -> float:
        """Calculate budget utilization percentage

        Returns:
            Utilization as percentage (0-100)
        """
        return (self.total_spent / self.monthly_budget) * 100 if self.monthly_budget > 0 else 0.0

    def project_monthly_cost(self, days_elapsed: int) -> float:
        """Project monthly cost based on current usage

        Args:
            days_elapsed: Days elapsed in current month

        Returns:
            Projected monthly cost in USD
        """
        if days_elapsed == 0:
            return 0.0

        daily_rate = self.total_spent / days_elapsed
        return daily_rate * 30  # Project to full month


class MetricsCollector:
    """Collects and aggregates metrics for document processing

    Provides unified interface for tracking:
    - Accuracy (extraction, validation)
    - Latency (processing time, API calls)
    - Cost (tokens, spending)

    Based on L208 lines 253-528 (Observability & Metrics)
    """

    def __init__(self, monthly_budget: float = 300.0):
        """Initialize metrics collector

        Args:
            monthly_budget: Monthly budget in USD
        """
        self.accuracy = AccuracyMetrics()
        self.latency = LatencyMetrics()
        self.cost = CostMetrics(monthly_budget=monthly_budget)
        self._timers: Dict[str, float] = {}

    def record_extraction(self, success: bool) -> None:
        """Record extraction attempt

        Args:
            success: Whether extraction succeeded
        """
        self.accuracy.total_processed += 1
        if success:
            self.accuracy.successful_extractions += 1
        else:
            self.accuracy.errors += 1

    def record_validation(self, passed: bool) -> None:
        """Record validation result

        Args:
            passed: Whether validation passed
        """
        if passed:
            self.accuracy.validation_passes += 1

    def record_human_review(self) -> None:
        """Record that human review was required"""
        self.accuracy.human_reviews_required += 1

    def start_timer(self, stage: str) -> None:
        """Start timing a stage

        Args:
            stage: Stage name
        """
        self._timers[stage] = time.time()

    def stop_timer(self, stage: str) -> float:
        """Stop timing a stage and record duration

        Args:
            stage: Stage name

        Returns:
            Duration in seconds
        """
        if stage not in self._timers:
            return 0.0

        duration = time.time() - self._timers[stage]
        self.latency.record(stage, duration)
        del self._timers[stage]

        return duration

    def record_llm_call(
        self,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
        latency_ms: float
    ) -> None:
        """Record LLM API call metrics

        Args:
            input_tokens: Input tokens
            output_tokens: Output tokens
            cost_usd: Cost in USD
            latency_ms: Latency in milliseconds
        """
        self.cost.record_llm_call(input_tokens, output_tokens, cost_usd)
        self.latency.record('llm_calls', latency_ms / 1000)  # Convert to seconds

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics

        Based on L208 lines 1311-1328 (Metrics view output)

        Returns:
            Dictionary with all metric categories
        """
        return {
            'accuracy': {
                'extraction_accuracy': self.accuracy.extraction_accuracy,
                'validation_pass_rate': self.accuracy.validation_pass_rate,
                'human_review_rate': self.accuracy.human_review_rate,
                'error_rate': self.accuracy.error_rate,
                'total_processed': self.accuracy.total_processed
            },
            'latency': {
                stage: self.latency.get_stats(stage)
                for stage in self.latency.timings.keys()
            },
            'cost': {
                'total_spent': self.cost.total_spent,
                'cost_per_document': self.cost.cost_per_document,
                'budget_utilization': self.cost.budget_utilization,
                'documents_processed': self.cost.documents_processed,
                'token_usage': dict(self.cost.token_usage)
            }
        }

    def check_budget_alert(self, threshold: float = 80.0) -> Optional[str]:
        """Check if budget threshold is exceeded

        Args:
            threshold: Alert threshold percentage (default: 80%)

        Returns:
            Alert message if threshold exceeded, None otherwise
        """
        utilization = self.cost.budget_utilization

        if utilization >= threshold:
            return (
                f"⚠️ Budget alert: {utilization:.1f}% of monthly budget used. "
                f"Spent: ${self.cost.total_spent:.2f} / ${self.cost.monthly_budget:.2f}"
            )

        return None

    def get_performance_summary(self) -> str:
        """Get human-readable performance summary

        Returns:
            Formatted summary string
        """
        acc = self.accuracy
        cost = self.cost
        llm_stats = self.latency.get_stats('llm_calls')

        summary_lines = [
            "=== Performance Summary ===",
            f"Documents Processed: {acc.total_processed}",
            f"Extraction Accuracy: {acc.extraction_accuracy:.1f}%",
            f"Validation Pass Rate: {acc.validation_pass_rate:.1f}%",
            f"",
            f"Average Cost per Document: ${cost.cost_per_document:.3f}",
            f"Total Spent: ${cost.total_spent:.2f}",
            f"Budget Utilization: {cost.budget_utilization:.1f}%",
        ]

        if llm_stats:
            summary_lines.extend([
                f"",
                f"LLM Call Latency:",
                f"  P50: {llm_stats['p50']:.2f}s",
                f"  P95: {llm_stats['p95']:.2f}s",
                f"  P99: {llm_stats['p99']:.2f}s",
            ])

        return "\n".join(summary_lines)
