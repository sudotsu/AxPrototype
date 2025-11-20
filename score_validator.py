"""
AxProtocol Score Validation v3.0

Aligned with 3-Role Critic Output (Logical, Practical, Probable).

"""

DOMAIN_THRESHOLDS = {
    "creative": {
        "minimum": 0.8,  # The 80% bar
        "weights": {
            "logical": 1.0,
            "practical": 1.2,  # Execution matters most
            "probable": 1.1    # Human resonance matters
        }
    }
    # Other domains removed for Phase 2 modularity
}

def validate_scores(scores: dict, domain: str = "creative") -> bool:
    """
    Validate if scores meet the domain threshold.
    Expects: {'logical': 0.9, 'practical': 0.8, ...}
    """
    thresholds = DOMAIN_THRESHOLDS.get(domain, DOMAIN_THRESHOLDS["creative"])
    min_score = thresholds["minimum"]

    # Simple average for now, or weighted
    avg = sum(scores.values()) / len(scores)
    return avg >= min_score
