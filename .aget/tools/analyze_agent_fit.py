#!/usr/bin/env python3
"""Agent Fit Analysis Tool

Analyze whether a use case is a good fit for this document processing template.

Usage:
    python3 .aget/tools/analyze_agent_fit.py <use_case_description>
    python3 .aget/tools/analyze_agent_fit.py --interactive

Examples:
    # Analyze specific use case
    python3 .aget/tools/analyze_agent_fit.py "Process legal contracts"

    # Interactive mode
    python3 .aget/tools/analyze_agent_fit.py --interactive
"""

import sys
import argparse
from pathlib import Path


def analyze_fit(use_case: str) -> dict:
    """Analyze fit between use case and template

    Args:
        use_case: Description of intended use case

    Returns:
        Dictionary with fit analysis
    """
    use_case_lower = use_case.lower()

    # Scoring criteria (each 0-10)
    scores = {
        'document_processing': 0,
        'structured_extraction': 0,
        'batch_operations': 0,
        'version_control': 0,
        'security_requirements': 0
    }

    # Document processing keywords
    doc_keywords = ['document', 'pdf', 'text', 'file', 'parse', 'extract', 'process']
    scores['document_processing'] = min(10, sum(2 for kw in doc_keywords if kw in use_case_lower))

    # Structured extraction keywords
    extract_keywords = ['extract', 'schema', 'structured', 'fields', 'data', 'information']
    scores['structured_extraction'] = min(10, sum(2 for kw in extract_keywords if kw in use_case_lower))

    # Batch operations keywords
    batch_keywords = ['batch', 'multiple', 'queue', 'workflow', 'pipeline', 'bulk']
    scores['batch_operations'] = min(10, sum(2 for kw in batch_keywords if kw in use_case_lower))

    # Version control keywords
    version_keywords = ['version', 'history', 'rollback', 'audit', 'track']
    scores['version_control'] = min(10, sum(2 for kw in version_keywords if kw in use_case_lower))

    # Security keywords
    security_keywords = ['secure', 'sensitive', 'pii', 'compliance', 'sanitize', 'validate']
    scores['security_requirements'] = min(10, sum(2 for kw in security_keywords if kw in use_case_lower))

    # Calculate overall fit
    total_score = sum(scores.values())
    max_score = len(scores) * 10
    fit_percentage = (total_score / max_score) * 100

    # Determine fit level
    if fit_percentage >= 60:
        fit_level = 'EXCELLENT'
    elif fit_percentage >= 40:
        fit_level = 'GOOD'
    elif fit_percentage >= 20:
        fit_level = 'MODERATE'
    else:
        fit_level = 'POOR'

    return {
        'fit_level': fit_level,
        'fit_percentage': fit_percentage,
        'scores': scores,
        'recommendations': generate_recommendations(scores, fit_level)
    }


def generate_recommendations(scores: dict, fit_level: str) -> list:
    """Generate recommendations based on fit analysis

    Args:
        scores: Component scores
        fit_level: Overall fit level

    Returns:
        List of recommendations
    """
    recommendations = []

    if fit_level in ['EXCELLENT', 'GOOD']:
        recommendations.append("✅ This template is well-suited for your use case")

        # Specific strengths
        strong_areas = [k for k, v in scores.items() if v >= 6]
        if strong_areas:
            recommendations.append(f"Strong fit for: {', '.join(strong_areas)}")

    elif fit_level == 'MODERATE':
        recommendations.append("⚠️  Partial fit - some template features may not be needed")

        # Suggest which features to focus on
        relevant_areas = [k for k, v in scores.items() if v >= 4]
        if relevant_areas:
            recommendations.append(f"Focus on these features: {', '.join(relevant_areas)}")

    else:  # POOR
        recommendations.append("❌ This template may not be the best fit")
        recommendations.append("Consider: General-purpose template (template-worker-aget)")

    # Check for missing key features
    if scores['document_processing'] < 4:
        recommendations.append("Note: Limited document processing needs - consider simpler template")

    if scores['batch_operations'] < 4:
        recommendations.append("Note: Single-document use case - queue features may be overkill")

    return recommendations


def interactive_analysis():
    """Run interactive fit analysis"""
    print("Document Processing Template - Fit Analysis")
    print("=" * 60)
    print("\nAnswer the following questions to analyze fit:\n")

    responses = {}

    # Questions
    questions = [
        ("Will you be processing documents (PDF, text, etc.)?", "document_processing"),
        ("Do you need structured data extraction?", "structured_extraction"),
        ("Will you process multiple documents in batches?", "batch_operations"),
        ("Do you need version control and audit trails?", "version_control"),
        ("Are there security/compliance requirements?", "security_requirements")
    ]

    for question, key in questions:
        while True:
            response = input(f"{question} (yes/no): ").strip().lower()
            if response in ['yes', 'y', 'no', 'n']:
                responses[key] = response in ['yes', 'y']
                break
            print("Please answer yes or no")

    # Calculate scores
    scores = {k: (10 if v else 0) for k, v in responses.items()}
    total_score = sum(scores.values())
    max_score = len(scores) * 10
    fit_percentage = (total_score / max_score) * 100

    # Determine fit level
    if fit_percentage >= 60:
        fit_level = 'EXCELLENT'
    elif fit_percentage >= 40:
        fit_level = 'GOOD'
    elif fit_percentage >= 20:
        fit_level = 'MODERATE'
    else:
        fit_level = 'POOR'

    # Display results
    print("\n" + "=" * 60)
    print("FIT ANALYSIS RESULTS")
    print("=" * 60)

    print(f"\nOverall Fit: {fit_level} ({fit_percentage:.0f}%)")

    print("\nComponent Scores:")
    for key, score in scores.items():
        bar = "█" * (score // 2) + "░" * ((10 - score) // 2)
        print(f"  {key:25s}: {bar} {score}/10")

    recommendations = generate_recommendations(scores, fit_level)
    print("\nRecommendations:")
    for rec in recommendations:
        print(f"  {rec}")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Analyze whether a use case is a good fit for this template",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze specific use case
  python3 .aget/tools/analyze_agent_fit.py "Process legal contracts"

  # Interactive mode
  python3 .aget/tools/analyze_agent_fit.py --interactive
        """
    )

    parser.add_argument(
        'use_case',
        nargs='?',
        help='Description of intended use case'
    )

    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='Run interactive fit analysis'
    )

    args = parser.parse_args()

    # Execute
    try:
        if args.interactive:
            interactive_analysis()
        elif args.use_case:
            analysis = analyze_fit(args.use_case)

            print("Agent Fit Analysis")
            print("=" * 60)
            print(f"\nUse Case: {args.use_case}")
            print(f"\nOverall Fit: {analysis['fit_level']} ({analysis['fit_percentage']:.0f}%)")

            print("\nComponent Scores:")
            for key, score in analysis['scores'].items():
                bar = "█" * (score // 2) + "░" * ((10 - score) // 2)
                print(f"  {key:25s}: {bar} {score}/10")

            print("\nRecommendations:")
            for rec in analysis['recommendations']:
                print(f"  {rec}")

        else:
            parser.print_help()
            print("\nError: Must provide use_case or --interactive")
            sys.exit(1)

        sys.exit(0)

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
