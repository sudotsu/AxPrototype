"""
AxProtocol governance coupling utilities.
Config-driven enforcement of TAES caps/floors and soft-signal logging.
"""

from __future__ import annotations
import json
import re
from pathlib import Path
from typing import Optional, Tuple
import logging

logger = logging.getLogger("axprotocol.governance.coupling")

BASE_DIR = Path(__file__).resolve().parents[2]


def load_governance_coupling() -> Tuple[dict, dict]:
    """Load governance coupling config and minimal settings.

    Search order:
      1) env GOV_COUPLING_PATH
      2) ./config/governance_coupling.json
      3) ./governance_coupling.json
      4) ./verify/governance_coupling.json
    """
    import os
    candidates = []
    env_path = os.getenv("GOV_COUPLING_PATH")
    if env_path:
        candidates.append(Path(env_path))
    candidates.append(BASE_DIR / "config" / "governance_coupling.json")
    candidates.append(BASE_DIR / "governance_coupling.json")
    candidates.append(BASE_DIR / "verify" / "governance_coupling.json")

    data = None
    for p in candidates:
        try:
            if p.exists():
                data = json.loads(p.read_text(encoding="utf8"))
                logger.info(f"Loaded governance coupling from {p}")
                break
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON in {p}: {e}; trying next candidate")
            continue
        except IOError as e:
            logger.warning(f"Failed to read {p}: {e}; trying next candidate")
            continue
        except Exception as e:
            logger.warning(f"Unexpected error reading {p}: {e}; trying next candidate")
            continue

    if data is None:
        logger.warning("No governance coupling config found; using empty defaults")
        return {}, {}

    settings = {"write_governance_to_ledger": bool(data.get("write_governance_to_ledger", False))} if isinstance(data, dict) else {}
    signals = data.get("signals", data) if isinstance(data, dict) else {}
    norm: dict = {}

    def _valid_range(x):
        try:
            return 0.0 <= float(x) <= 1.0
        except Exception:
            return False

    for key, spec in (signals.items() if isinstance(signals, dict) else []):
        if not isinstance(spec, dict):
            logging.getLogger("axprotocol").warning(f"Invalid governance spec for {key}: not an object; skipping")
            continue
        mode = spec.get("mode", "hard")
        if mode not in ("hard", "soft"):
            logging.getLogger("axprotocol").warning(f"Invalid mode for {key}: {mode}; defaulting to 'hard'")
            mode = "hard"
        iv_max = spec.get("iv_max")
        ird_min = spec.get("ird_min")
        if iv_max is not None and not _valid_range(iv_max):
            logging.getLogger("axprotocol").warning(f"Invalid iv_max for {key}: {iv_max}; ignoring cap")
            iv_max = None
        if ird_min is not None and not _valid_range(ird_min):
            logging.getLogger("axprotocol").warning(f"Invalid ird_min for {key}: {ird_min}; ignoring floor")
            ird_min = None
        norm[key] = {"mode": mode, "iv_max": iv_max, "ird_min": ird_min}

    return norm, settings


def apply_governance_coupling(
    text: str,
    taes: dict,
    hard_signals: set,
    objective: Optional[str] = None,
    soft_signals: Optional[set] = None,
    cfg: Optional[dict] = None,
) -> dict:
    """Apply config-driven coupling to TAES and collect signals.
    If a signal is in mode=hard, cap iv/floor ird and set requires_rrp=True.
    If mode=soft, add to soft_signals (if provided) and do not change TAES.
    """
    triggered_hard = []
    GOV_COUPLING = cfg or {}
    if GOV_COUPLING:
        def _push(sig):
            spec = GOV_COUPLING.get(sig)
            if not spec:
                return
            if spec.get("mode", "hard") == "hard":
                triggered_hard.append(sig)
            elif soft_signals is not None:
                soft_signals.add(sig)

        if _detect_contradiction(text):
            _push("D3")
        if _detect_sycophancy(text):
            _push("D13")
        if objective and _unresolved_ambiguity(objective, text):
            _push("D2")
        if objective and _precedence_inversion(objective, text):
            _push("D7"); _push("D11")
        if _overconfidence_no_evidence(text):
            _push("D20-24")

    if not triggered_hard:
        return taes

    base_iv = float(taes.get("integrity_vector", taes.get("iv", 0.0)))
    base_ird = float(taes.get("ird", 0.0))
    iv_caps = [float(GOV_COUPLING[s]["iv_max"]) for s in triggered_hard if GOV_COUPLING.get(s, {}).get("iv_max") is not None]
    ird_floors = [float(GOV_COUPLING[s]["ird_min"]) for s in triggered_hard if GOV_COUPLING.get(s, {}).get("ird_min") is not None]
    adjusted_iv = min([base_iv] + iv_caps) if iv_caps else base_iv
    adjusted_ird = max([base_ird] + ird_floors) if ird_floors else base_ird

    new = dict(taes)
    if "integrity_vector" in new:
        new["integrity_vector"] = round(float(adjusted_iv), 3)
    if "iv" in new:
        new["iv"] = round(float(adjusted_iv), 3)
    new["ird"] = round(float(adjusted_ird), 3)
    new["requires_rrp"] = True

    hard_signals.update(triggered_hard)
    return new


def compute_soft_signals(all_text: str, detected_domain: str, domain_override: Optional[str], confidence: Optional[float], cfg: Optional[dict] = None) -> set:
    gov_soft = set()
    GOV_COUPLING = cfg or {}
    def _in_cfg(sig: str) -> bool:
        return sig in GOV_COUPLING
    if _in_cfg('SECRETS'):
        t = (all_text or "").lower()
        cc_regex = r"\b(?:\d[ -]*?){13,16}\b"
        if ("ssn" in t or "social security" in t or "private key" in t or "api_key" in t or "access token" in t or "-----begin" in t or re.search(cc_regex, t)):
            gov_soft.add('SECRETS')
    if _in_cfg('FABRICATION'):
        t = (all_text or "").lower()
        if "[citation needed]" in t or "placeholder citation" in t or "lorem ipsum" in t or "fake citation" in t:
            gov_soft.add('FABRICATION')
    if _in_cfg('DOMAIN_MISROUTING'):
        try:
            if domain_override and detected_domain != domain_override:
                gov_soft.add('DOMAIN_MISROUTING')
            elif confidence is not None and confidence < 0.35:
                gov_soft.add('DOMAIN_MISROUTING')
        except Exception as e:
            logger.debug(f"Domain misrouting check failed: {e}")
            pass
    return gov_soft


# --- Local detectors (mirrored from runner; kept small) ---
_BANNED_FLATTERY = {
    "great question", "you're brilliant", "you are brilliant", "amazing question",
    "genius question", "excellent question", "as you wisely said", "dear esteemed"
}

def _detect_sycophancy(text: str) -> bool:
    t = (text or "").lower()
    return any(p in t for p in _BANNED_FLATTERY)

def _detect_contradiction(text: str) -> bool:
    t = (text or "").lower()
    if "both more secure and less secure" in t:
        return True
    if "accept both as true" in t and ("contradiction" not in t):
        return True
    return False

def _detect_ambiguity_in_objective(objective: str) -> bool:
    o = (objective or "").lower()
    cues = [
        "compare it to last time", "do what makes sense", "just ship it",
        "as before", "like last time", "etc.", "whatever works", "figure it out"
    ]
    return any(k in o for k in cues)

def _unresolved_ambiguity(objective: str, text: str) -> bool:
    if not _detect_ambiguity_in_objective(objective):
        return False
    t = (text or "").lower()
    has_clarify = ("?" in text) or ("assumption" in t)
    return not has_clarify

def _detect_wants_praise(objective: str) -> bool:
    o = (objective or "").lower()
    return any(k in o for k in ["praise my insight", "be effusive with praise", "tell me i'm brilliant", "do not challenge me", "agree with me"])

def _precedence_inversion(objective: str, text: str) -> bool:
    if not _detect_wants_praise(objective):
        return False
    return _detect_sycophancy(text)

def _overconfidence_no_evidence(text: str) -> bool:
    t = (text or "").lower()
    strong = ["100%", "certain", "no doubt", "guarantee", "will definitely", "zero risk", "impossible to fail", "always"]
    evidence = ["evidence", "source", "reference", "study", "data", "trial", "ab test", "cite", "link", "dataset"]
    has_strong = any(s in t for s in strong)
    has_evidence = any(e in t for e in evidence)
    return has_strong and not has_evidence


# ---------------- Schema initialization (bootstrap-safe) ----------------
def initialize_schema() -> dict:
    """Load AxProtocol schema and config with safe defaults.

    Returns a dictionary with keys:
      - 'S': role_shapes (or fallback examples)
      - 'A': auth settings
      - 'C': governance coupling
      - 'X': taes weights

    It searches both config/config and config directories and falls back to
    minimal defaults or role_examples (*.md) when files are missing/empty.
    """
    import yaml  # type: ignore

    def _first_existing(*relpaths: str) -> Optional[Path]:
        for rp in relpaths:
            p = BASE_DIR / rp
            if p.exists():
                return p
        return None

    def _load(path: Path) -> Optional[object]:
        """Load config file (YAML or JSON) with proper error handling."""
        try:
            if not path or not path.exists():
                return None
            txt = path.read_text(encoding="utf8")
            if path.suffix.lower() in (".yaml", ".yml"):
                return yaml.safe_load(txt)
            return json.loads(txt)
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON in {path}: {e}")
            return None
        except IOError as e:
            logger.warning(f"Failed to read {path}: {e}")
            return None
        except Exception as e:
            logger.warning(f"Unexpected error loading {path}: {e}")
            return None

    def _read_examples() -> dict:
        out: dict = {}
        d = _first_existing("config/config/role_examples", "config/role_examples")
        if not d:
            return out
        for md in d.glob("*.md"):
            try:
                lines = [ln.strip() for ln in md.read_text(encoding="utf8").splitlines() if ln.strip()]
                out[md.stem] = lines[:100]
            except IOError as e:
                logger.debug(f"Failed to read example {md}: {e}")
                continue
            except Exception as e:
                logger.debug(f"Unexpected error reading {md}: {e}")
                continue
        return out

    # locate files (prefer config/config then config)
    p_S = _first_existing("config/config/role_shapes.json", "config/role_shapes.json")
    p_A = _first_existing("config/config/auth_settings.yaml", "config/auth_settings.yaml")
    p_C = _first_existing("config/config/governance_coupling.json", "config/governance_coupling.json")
    p_X = _first_existing("config/config/taes_weights.json", "config/taes_weights.json")

    s_data = _load(p_S) or {}
    a_data = _load(p_A) or {}
    c_data = _load(p_C) or {}
    x_data = _load(p_X) or {}

    # Bootstrap defaults if empty or invalid
    examples = _read_examples()
    if not isinstance(s_data, dict) or not s_data:
        if examples:
            s_data = {"examples": examples}
        else:
            s_data = {"examples": {"strategist": ["Define positioning"], "analyst": ["List KPIs"]}}

    if not isinstance(a_data, dict) or not a_data:
        a_data = {"ttl_minutes": 30, "rate_limits": {"burst": 10, "window_s": 60}}

    if not isinstance(c_data, dict) or not c_data:
        c_data = {"signals": {"D3": {"mode": "hard", "iv_max": 0.68, "ird_min": 0.55}}}

    if not isinstance(x_data, dict) or not x_data:
        x_data = {"default": {"logical": 0.4, "practical": 0.4, "probable": 0.2}}

    return {"S": s_data, "A": a_data, "C": c_data, "X": x_data}
