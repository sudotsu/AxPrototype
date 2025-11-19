"""
Logging configuration utilities.
"""

import os
import logging
import logging.config
from pathlib import Path


def configure_logging(base_dir: Path):
    """
    Configure logging from YAML config or fallback to basicConfig.

    Args:
        base_dir: Base directory for finding config files
    """
    cfg_candidates = [
        os.getenv("LOG_CFG"),
        str(base_dir / "config" / "logging.yaml"),
    ]
    cfg_candidates = [Path(p) for p in cfg_candidates if p]
    try:
        import yaml  # type: ignore
        for p in cfg_candidates:
            if p.exists():
                with open(p, "r", encoding="utf8") as f:
                    data = yaml.safe_load(f)
                logging.config.dictConfig(data)
                logging.getLogger("axprotocol").info(f"Logging configured from {p}")
                return
    except Exception as e:
        # Fall back to basic config
        logging.getLogger("axprotocol").warning(
            "Logging configuration failed (%s); using basicConfig fallback",
            e,
        )
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    logging.getLogger("axprotocol").info("Logging configured with basicConfig (fallback)")

