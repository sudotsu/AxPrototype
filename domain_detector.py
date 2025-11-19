"""
AxProtocol Multi-Domain Detector
Automatically detects the appropriate domain based on objective text
"""

import json
import re
from pathlib import Path
from typing import Dict, Tuple, List, Optional

class DomainDetector:
    """
    Intelligent domain detection using keyword matching and pattern recognition.
    Determines which domain (marketing, ops, technical, etc.) best fits an objective.
    """

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize detector with domain configuration.

        Args:
            config_path: Path to DomainConfig.json (defaults to same directory)
        """
        if config_path is None:
            config_path = Path(__file__).parent / "DomainConfig.json"

        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        self.domains = self.config['domains']
        self.detection_rules = self.config['detection_rules']
        self.confidence_threshold = self.detection_rules['confidence_threshold']
        self.fallback_domain = self.detection_rules['fallback_domain']

    def detect(self, objective: str, verbose: bool = False) -> str:
        """
        Detect the most appropriate domain for the given objective.

        Args:
            objective: The campaign/project objective text
            verbose: If True, print detection details

        Returns:
            Domain name (e.g., 'marketing', 'technical', 'ops')
        """
        scores = self._score_all_domains(objective)
        domain, confidence = self._select_best_domain(scores)

        if verbose:
            print(f"\n[Domain Detection]")
            print(f"   Objective: {objective[:100]}...")
            print(f"   Scores: {scores}")
            print(f"   Selected: {domain} (confidence: {confidence:.2f})")

            if confidence < self.confidence_threshold:
                print(f"   ⚠️  Low confidence - using fallback domain")

        return domain

    def _score_all_domains(self, objective: str) -> Dict[str, float]:
        """
        Score the objective against all domains.

        Args:
            objective: The objective text

        Returns:
            Dictionary of domain names to confidence scores (0.0-1.0)
        """
        objective_lower = objective.lower()
        scores = {}

        for domain_name, domain_config in self.domains.items():
            score = self._score_domain(objective_lower, domain_config)
            scores[domain_name] = score

        return scores
    def score_all_domains(self, objective: str) -> Dict[str, float]:
        """Public wrapper for domain scoring (UI/runner use)."""
        return self._score_all_domains(objective)

    def _score_domain(self, objective_lower: str, domain_config: Dict) -> float:
        """
        Score how well the objective matches a specific domain.

        Uses keyword matching with weighted scoring.

        Args:
            objective_lower: Lowercase objective text
            domain_config: Domain configuration from DomainConfig.json

        Returns:
            Confidence score (0.0-1.0)
        """
        keywords = domain_config['keywords']
        matches = 0
        matched_keywords = 0

        for keyword in keywords:
            # Check if keyword appears in objective
            keyword_lower = keyword.lower()

            # Exact word match (higher weight)
            pattern_exact = r'\b' + re.escape(keyword_lower) + r'\b'
            exact_matches = len(re.findall(pattern_exact, objective_lower))

            if exact_matches > 0:
                # Weight: 1.0 for first occurrence, 0.2 for each additional
                weight = 1.0 + (min(exact_matches - 1, 3) * 0.2)
                matches += weight
                matched_keywords += 1

        # If no keywords matched, return 0
        if matched_keywords == 0:
            return 0.0

        # Use a more reasonable scoring: base score + bonus for multiple matches
        # Base score is 0.3 for any match, plus 0.1 for each additional keyword
        base_score = 0.3
        bonus_per_keyword = 0.1
        max_bonus = 0.7  # Cap bonus at 0.7 to keep max score at 1.0

        bonus = min((matched_keywords - 1) * bonus_per_keyword, max_bonus)
        raw_score = base_score + bonus

        # Apply diminishing returns for very high keyword counts
        normalized_score = min(raw_score, 1.0)

        return normalized_score

    def _select_best_domain(self, scores: Dict[str, float]) -> Tuple[str, float]:
        """
        Select the best domain from scores.

        Args:
            scores: Dictionary of domain names to scores

        Returns:
            Tuple of (domain_name, confidence_score)
        """
        if not scores:
            return self.fallback_domain, 0.0

        # Find domain with highest score
        best_domain = max(scores, key=scores.get)
        best_score = scores[best_domain]

        # If score is below threshold, use fallback
        if best_score < self.confidence_threshold:
            return self.fallback_domain, best_score

        return best_domain, best_score

    def get_domain_info(self, domain: str) -> Dict:
        """
        Get full configuration for a domain.

        Args:
            domain: Domain name

        Returns:
            Domain configuration dictionary
        """
        if domain not in self.domains:
            raise ValueError(f"Unknown domain: {domain}")

        return self.domains[domain]

    def list_domains(self) -> List[str]:
        """Get list of all available domain names."""
        return list(self.domains.keys())

    def get_taes_weights(self, domain: str) -> Dict[str, float]:
        """
        Get TAES weights for a specific domain.

        Args:
            domain: Domain name

        Returns:
            Dictionary with 'logical', 'practical', 'probable' weights
        """
        domain_info = self.get_domain_info(domain)
        return domain_info['taes_weights']


# Convenience function for quick detection
def detect_domain(objective: str, verbose: bool = False) -> str:
    """
    Quick domain detection function.

    Args:
        objective: The campaign/project objective
        verbose: Whether to print detection details

    Returns:
        Detected domain name

    Example:
        >>> domain = detect_domain("Build a REST API for user authentication")
        >>> print(domain)
        'technical'
    """
    detector = DomainDetector()
    return detector.detect(objective, verbose=verbose)


# Testing function
def test_detector():
    """Test the domain detector with various objectives."""
    detector = DomainDetector()

    test_cases = [
        "Launch a social media campaign for new product",
        "Build a user authentication system with OAuth",
        "Create an employee onboarding workflow",
        "Design a brand identity and visual style guide",
        "Develop an online course about Python programming",
        "Plan product roadmap for Q1 2026",
        "Analyze customer churn data and identify patterns",
        "Create strategic plan for market expansion"
    ]

    print("\n" + "="*70)
    print("AxProtocol Domain Detector - Test Results")
    print("="*70)

    for objective in test_cases:
        domain = detector.detect(objective, verbose=False)
        scores = detector._score_all_domains(objective)

        print(f"\n📋 Objective: {objective}")
        print(f"✅ Detected: {domain.upper()}")
        print(f"   Confidence: {scores[domain]:.2f}")

        # Show top 3 scores
        top_3 = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]
        print(f"   Top matches: {', '.join([f'{d}({s:.2f})' for d, s in top_3])}")

    print("\n" + "="*70)


if __name__ == "__main__":
    # Run tests if executed directly
    test_detector()