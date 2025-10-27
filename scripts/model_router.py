#!/usr/bin/env python3
"""Model Routing CLI

Route processing tasks to appropriate LLM models based on complexity.

Usage:
    python3 scripts/model_router.py <task_description>
    python3 scripts/model_router.py <task_description> --complexity high

Examples:
    # Get model recommendation for task
    python3 scripts/model_router.py "Extract invoice data"

    # Specify task complexity
    python3 scripts/model_router.py "Summarize document" --complexity low

    # List all available models
    python3 scripts/model_router.py --list-models
"""

import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


def get_model_recommendations() -> dict:
    """Get model routing recommendations

    Returns:
        Dictionary mapping complexity levels to models
    """
    return {
        'low': {
            'model': 'gpt-4o-mini',
            'provider': 'openai',
            'use_cases': ['Simple extraction', 'Basic summarization', 'Format conversion'],
            'cost_per_1k_tokens': 0.00015
        },
        'medium': {
            'model': 'gpt-4o',
            'provider': 'openai',
            'use_cases': ['Complex extraction', 'Multi-field schemas', 'Structured output'],
            'cost_per_1k_tokens': 0.0050
        },
        'high': {
            'model': 'gpt-4o',
            'provider': 'openai',
            'use_cases': ['Legal document analysis', 'Complex reasoning', 'Multi-step processing'],
            'cost_per_1k_tokens': 0.0050
        }
    }


def estimate_complexity(task_description: str) -> str:
    """Estimate task complexity based on description

    Args:
        task_description: Description of the task

    Returns:
        Complexity level: low, medium, or high
    """
    task_lower = task_description.lower()

    # High complexity indicators
    high_keywords = ['legal', 'complex', 'reasoning', 'analysis', 'multi-step', 'chain']
    if any(keyword in task_lower for keyword in high_keywords):
        return 'high'

    # Low complexity indicators
    low_keywords = ['simple', 'basic', 'format', 'convert', 'summarize']
    if any(keyword in task_lower for keyword in low_keywords):
        return 'low'

    # Default to medium
    return 'medium'


def recommend_model(task_description: str, complexity: str = None) -> dict:
    """Recommend model for task

    Args:
        task_description: Description of the task
        complexity: Optional complexity override

    Returns:
        Model recommendation dictionary
    """
    # Estimate complexity if not provided
    if not complexity:
        complexity = estimate_complexity(task_description)

    recommendations = get_model_recommendations()
    return recommendations.get(complexity, recommendations['medium'])


def list_models():
    """List all available models"""
    print("Available Models")
    print("=" * 60)

    recommendations = get_model_recommendations()

    for complexity, details in recommendations.items():
        print(f"\n{complexity.upper()} Complexity:")
        print(f"  Model: {details['model']}")
        print(f"  Provider: {details['provider']}")
        print(f"  Cost: ${details['cost_per_1k_tokens']}/1k tokens")
        print(f"  Use cases:")
        for use_case in details['use_cases']:
            print(f"    - {use_case}")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Route processing tasks to appropriate LLM models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Get model recommendation for task
  python3 scripts/model_router.py "Extract invoice data"

  # Specify task complexity
  python3 scripts/model_router.py "Summarize document" --complexity low

  # List all available models
  python3 scripts/model_router.py --list-models
        """
    )

    parser.add_argument(
        'task',
        nargs='?',
        help='Task description'
    )

    parser.add_argument(
        '--complexity',
        choices=['low', 'medium', 'high'],
        help='Task complexity level'
    )

    parser.add_argument(
        '--list-models',
        action='store_true',
        help='List all available models'
    )

    args = parser.parse_args()

    # Execute
    try:
        if args.list_models:
            list_models()
            sys.exit(0)

        if not args.task:
            parser.print_help()
            print("\nError: Must provide task description or --list-models")
            sys.exit(1)

        # Get recommendation
        recommendation = recommend_model(args.task, complexity=args.complexity)

        estimated_complexity = estimate_complexity(args.task) if not args.complexity else args.complexity

        print("Model Routing Recommendation")
        print("=" * 60)
        print(f"\nTask: {args.task}")
        print(f"Estimated Complexity: {estimated_complexity}")
        print(f"\nRecommended Model:")
        print(f"  Model: {recommendation['model']}")
        print(f"  Provider: {recommendation['provider']}")
        print(f"  Cost: ${recommendation['cost_per_1k_tokens']}/1k tokens")
        print(f"\nTypical Use Cases:")
        for use_case in recommendation['use_cases']:
            print(f"  - {use_case}")

        sys.exit(0)

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
