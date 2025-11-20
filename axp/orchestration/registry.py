"""
Registry (blackboard) management for role outputs.

"""


def init_registry() -> dict:
    """
    Initialize empty registry for 3-Role architecture.
    """
    return {
        "Caller": [],
        "Builder": [],
        "Critic": []
    }

