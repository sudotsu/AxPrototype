"""
Registry (blackboard) management for role outputs.
"""


def init_registry() -> dict:
    """
    Initialize empty registry for role outputs.

    Returns:
        Registry dictionary with keys: S, A, P, C, X, Q
    """
    return {"S": [], "A": [], "P": [], "C": [], "X": [], "Q": []}

