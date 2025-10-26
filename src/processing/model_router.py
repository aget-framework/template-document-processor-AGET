"""Model Routing Strategies

Routes documents to optimal LLM models based on:
- Document complexity (static routing)
- Content analysis (dynamic routing)
- Multi-model comparison (ensemble routing)

Based on L208 lines 34-90 (Model Routing Strategies)
"""

from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod


class RoutingStrategy(Enum):
    """Model routing strategies"""
    STATIC = "static"
    DYNAMIC = "dynamic"
    ENSEMBLE = "ensemble"


class ComplexityLevel(Enum):
    """Document complexity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class RoutingDecision:
    """Result of model routing decision"""
    model: str
    strategy: RoutingStrategy
    complexity: Optional[ComplexityLevel] = None
    confidence: float = 1.0
    rationale: str = ""
    estimated_cost: float = 0.0
    estimated_latency: float = 0.0


class BaseRouter(ABC):
    """Base class for routing strategies

    Design Decision: Strategy pattern for routing.
    Different strategies can be swapped based on use case.
    """

    @abstractmethod
    def route(self, document: str, metadata: Dict) -> RoutingDecision:
        """Determine which model to use

        Args:
            document: Document content or reference
            metadata: Document metadata (size, type, etc.)

        Returns:
            RoutingDecision with model and rationale
        """
        pass


class StaticRouter(BaseRouter):
    """Static routing based on document characteristics

    Maps document attributes (size, type, domain) directly to models
    without analyzing content.

    Based on L208 lines 37-41 (Static Routing)
    """

    def __init__(self, routing_rules: Optional[Dict] = None):
        """Initialize static router

        Args:
            routing_rules: Dictionary mapping conditions to models
                          Example: {
                              'complexity_low': 'gpt-4o-mini',
                              'complexity_medium': 'gemini-2.5-flash',
                              'complexity_high': 'gemini-2.5-pro'
                          }
        """
        self.routing_rules = routing_rules or self._default_rules()

    def _default_rules(self) -> Dict:
        """Default routing rules (based on L208 lines 56-76)"""
        return {
            'complexity_low': {
                'model': 'gpt-4o-mini',
                'cost_per_1k': 0.15,
                'latency_sec': 1.0
            },
            'complexity_medium': {
                'model': 'gemini-2.5-flash',
                'cost_per_1k': 0.30,
                'latency_sec': 2.0
            },
            'complexity_high': {
                'model': 'gemini-2.5-pro',
                'cost_per_1k': 15.00,
                'latency_sec': 5.0
            }
        }

    def route(self, document: str, metadata: Dict) -> RoutingDecision:
        """Route based on static rules

        Args:
            document: Document content
            metadata: Document metadata (must include 'complexity' or 'word_count')

        Returns:
            RoutingDecision
        """
        # Determine complexity
        complexity = self._assess_complexity(document, metadata)

        # Get routing rule for complexity
        rule_key = f'complexity_{complexity.value}'
        rule = self.routing_rules.get(rule_key, self.routing_rules['complexity_medium'])

        return RoutingDecision(
            model=rule['model'],
            strategy=RoutingStrategy.STATIC,
            complexity=complexity,
            confidence=1.0,
            rationale=f"Static routing: {complexity.value} complexity → {rule['model']}",
            estimated_cost=rule['cost_per_1k'],
            estimated_latency=rule['latency_sec']
        )

    def _assess_complexity(self, document: str, metadata: Dict) -> ComplexityLevel:
        """Assess document complexity

        Args:
            document: Document content
            metadata: Document metadata

        Returns:
            ComplexityLevel
        """
        # Use metadata if available
        if 'complexity' in metadata:
            complexity_str = metadata['complexity'].lower()
            if complexity_str in ['low', 'simple', 'easy']:
                return ComplexityLevel.LOW
            elif complexity_str in ['high', 'complex', 'difficult']:
                return ComplexityLevel.HIGH
            else:
                return ComplexityLevel.MEDIUM

        # Fall back to word count heuristic
        word_count = metadata.get('word_count', len(document.split()))

        if word_count < 500:
            return ComplexityLevel.LOW
        elif word_count < 2000:
            return ComplexityLevel.MEDIUM
        else:
            return ComplexityLevel.HIGH


class DynamicRouter(BaseRouter):
    """Dynamic routing based on content analysis

    Analyzes document content to determine complexity
    and routes to appropriate model.

    Based on L208 lines 43-47 (Dynamic Routing)
    """

    def __init__(self, classifier: Optional[Callable] = None):
        """Initialize dynamic router

        Args:
            classifier: Function that analyzes document and returns complexity
                       If None, uses built-in heuristic classifier
        """
        self.classifier = classifier or self._default_classifier

    def route(self, document: str, metadata: Dict) -> RoutingDecision:
        """Route based on content analysis

        Args:
            document: Document content
            metadata: Document metadata

        Returns:
            RoutingDecision
        """
        # Analyze document
        analysis = self.classifier(document, metadata)

        complexity = analysis['complexity']
        confidence = analysis['confidence']

        # Route based on complexity
        model_map = {
            ComplexityLevel.LOW: ('gpt-4o-mini', 0.15, 1.0),
            ComplexityLevel.MEDIUM: ('gemini-2.5-flash', 0.30, 2.0),
            ComplexityLevel.HIGH: ('gemini-2.5-pro', 15.00, 5.0)
        }

        model, cost, latency = model_map[complexity]

        # If confidence is low, escalate to better model
        if confidence < 0.5:
            model, cost, latency = model_map[ComplexityLevel.HIGH]
            rationale = f"Low confidence ({confidence:.2f}), escalating to {model}"
        else:
            rationale = f"Dynamic routing: {complexity.value} complexity (confidence: {confidence:.2f}) → {model}"

        return RoutingDecision(
            model=model,
            strategy=RoutingStrategy.DYNAMIC,
            complexity=complexity,
            confidence=confidence,
            rationale=rationale,
            estimated_cost=cost,
            estimated_latency=latency
        )

    def _default_classifier(self, document: str, metadata: Dict) -> Dict:
        """Default document classifier

        Uses simple heuristics. In production, replace with ML classifier.

        Args:
            document: Document content
            metadata: Document metadata

        Returns:
            Dictionary with {complexity: ComplexityLevel, confidence: float}
        """
        word_count = len(document.split())
        sentence_count = document.count('.') + document.count('!') + document.count('?')
        avg_sentence_length = word_count / max(sentence_count, 1)

        # Heuristic: longer sentences = more complex
        if avg_sentence_length > 25:
            complexity = ComplexityLevel.HIGH
            confidence = 0.7
        elif avg_sentence_length > 15:
            complexity = ComplexityLevel.MEDIUM
            confidence = 0.8
        else:
            complexity = ComplexityLevel.LOW
            confidence = 0.9

        # Adjust for document length
        if word_count > 2000:
            complexity = ComplexityLevel.HIGH
            confidence *= 0.9

        return {
            'complexity': complexity,
            'confidence': confidence,
            'avg_sentence_length': avg_sentence_length,
            'word_count': word_count
        }


class EnsembleRouter(BaseRouter):
    """Ensemble routing - runs multiple models and aggregates results

    Higher cost but improved quality for critical tasks.

    Based on L208 lines 49-54 (Ensemble Routing)
    """

    def __init__(self, models: List[str], aggregation: str = "voting"):
        """Initialize ensemble router

        Args:
            models: List of models to use in ensemble
            aggregation: Aggregation strategy ("voting", "consensus", "weighted")
        """
        self.models = models
        self.aggregation = aggregation

    def route(self, document: str, metadata: Dict) -> RoutingDecision:
        """Route to ensemble of models

        Note: This doesn't actually run multiple models (that happens in processing).
        It just signals that ensemble should be used.

        Args:
            document: Document content
            metadata: Document metadata

        Returns:
            RoutingDecision with list of models
        """
        # Estimate cost and latency for ensemble
        model_costs = {
            'gpt-4o': 2.5,
            'claude-3.5-sonnet': 3.0,
            'gemini-2.5-flash': 0.3
        }

        total_cost = sum(model_costs.get(m, 1.0) for m in self.models)
        avg_latency = 3.0  # Ensemble can run in parallel

        return RoutingDecision(
            model=f"ensemble({','.join(self.models)})",
            strategy=RoutingStrategy.ENSEMBLE,
            complexity=ComplexityLevel.HIGH,
            confidence=0.95,  # High confidence due to multiple models
            rationale=f"Ensemble routing: {len(self.models)} models with {self.aggregation} aggregation",
            estimated_cost=total_cost,
            estimated_latency=avg_latency
        )


class ModelRouter:
    """Main model router with fallback chain

    Provides unified interface for all routing strategies.

    Design Decision: Supports fallback chain for reliability.
    If primary model fails, falls back to next model in chain.
    """

    def __init__(
        self,
        primary_strategy: BaseRouter,
        fallback_chain: Optional[List[str]] = None,
        max_cost_per_doc: float = 0.50
    ):
        """Initialize model router

        Args:
            primary_strategy: Primary routing strategy
            fallback_chain: List of fallback models if primary fails
            max_cost_per_doc: Maximum allowed cost per document
        """
        self.primary_strategy = primary_strategy
        self.fallback_chain = fallback_chain or ['gpt-4o', 'claude-3.5-sonnet', 'gemini-2.5-pro']
        self.max_cost_per_doc = max_cost_per_doc

    def route(self, document: str, metadata: Optional[Dict] = None) -> RoutingDecision:
        """Route document to optimal model

        Args:
            document: Document content
            metadata: Document metadata

        Returns:
            RoutingDecision

        Raises:
            ValueError: If estimated cost exceeds max_cost_per_doc
        """
        metadata = metadata or {}

        # Get routing decision from primary strategy
        decision = self.primary_strategy.route(document, metadata)

        # Check cost constraint
        if decision.estimated_cost > self.max_cost_per_doc:
            raise ValueError(
                f"Estimated cost ${decision.estimated_cost:.2f} exceeds "
                f"maximum ${self.max_cost_per_doc:.2f}"
            )

        return decision

    def get_fallback_model(self, failed_model: str) -> Optional[str]:
        """Get next fallback model

        Args:
            failed_model: Model that failed

        Returns:
            Next fallback model, or None if no fallbacks remain
        """
        try:
            current_index = self.fallback_chain.index(failed_model)
            if current_index + 1 < len(self.fallback_chain):
                return self.fallback_chain[current_index + 1]
        except ValueError:
            # failed_model not in fallback_chain, return first fallback
            if self.fallback_chain:
                return self.fallback_chain[0]

        return None
