"""
Sentinel verification utilities.
"""

from typing import Dict, Any


def sentinel_verify(objective: str, results: dict) -> dict:
    """
    Perform Sentinel verification (mock implementation).

    Checks for:
    - Overconfidence without evidence
    - Low reference coverage
    - Upstream emptiness

    Args:
        objective: Original objective
        results: Execution results dictionary

    Returns:
        Verification report with score, flags, and details
    """
    registry = results.get('registry') or {}
    s = registry.get('S') or []
    a = registry.get('A') or []
    p = registry.get('P') or []
    c = registry.get('C') or []
    x = registry.get('X') or []

    text_pool = []
    try:
        text_pool.append(results.get('composer') or '')
        text_pool.append(results.get('producer_draft', {}).get('output', ''))
        text_pool.append(results.get('courier_draft', {}).get('output', ''))
        text_pool.append(results.get('critic', {}).get('output', ''))
    except Exception:
        pass
    text = "\n\n".join([t for t in text_pool if t])

    strong = ["100%", "certain", "always", "definitely", "zero risk", "guarantee", "impossible to fail"]
    evid = ["evidence", "source", "cite", "reference", "data", "study", "trial", "dataset", "link"]
    t = (text or '').lower()
    strong_hits = sum(t.count(w.lower()) for w in strong)
    evid_hits = sum(t.count(w.lower()) for w in evid)

    # Cross-ref coverage from Critic refs -> registry ids
    def _idset(key):
        return {item.get(f"{key.lower()}_id") for item in (registry.get(key) or [])}
    s_ids, a_ids, p_ids, c_ids = _idset('S'), _idset('A'), _idset('P'), set()
    try:
        c_ids = {row.get('p_id') for row in (registry.get('C') or [])}
    except Exception:
        c_ids = set()

    total_refs = 0
    matched = 0
    drift = []
    for item in x or []:
        refs = item.get('refs') or {}
        for sid in refs.get('s', []) or []:
            total_refs += 1
            matched += 1 if sid in s_ids else 0
        for aid in refs.get('a', []) or []:
            total_refs += 1
            matched += 1 if aid in a_ids else 0
        for pid in refs.get('p', []) or []:
            total_refs += 1
            matched += 1 if pid in p_ids else 0
        for cid in refs.get('c', []) or []:
            total_refs += 1
            matched += 1 if cid in c_ids else 0
    coverage = (matched/total_refs) if total_refs else (1.0 if not x else 0.0)

    # Upstream emptiness penalty
    upstream_empty = int(len(s) == 0 or len(a) == 0)
    if upstream_empty:
        drift.append({"type": "UPSTREAM_EMPTY", "detail": "S or A slice empty while downstream present"})

    # Compose score (100 baseline minus penalties)
    score = 100.0
    # strong without evidence => penalty
    if strong_hits > evid_hits:
        score -= min(40.0, (strong_hits - evid_hits) * 5.0)
    # low coverage penalty
    score -= max(0.0, (1.0 - coverage) * 30.0)
    # upstream empty penalty
    if upstream_empty:
        score -= 20.0

    score = max(0.0, min(100.0, score))

    flags = []
    if strong_hits > evid_hits:
        flags.append('OVERCONF_NO_EVIDENCE')
    if coverage < 0.7:
        flags.append('LOW_REF_COVERAGE')
    if upstream_empty:
        flags.append('UPSTREAM_EMPTY')

    return {
        'score': round(score, 1),
        'flags': flags,
        'details': {
            'strong_hits': int(strong_hits),
            'evidence_hits': int(evid_hits),
            'ref_coverage': round(coverage, 3),
        },
        'drift': drift,
    }

