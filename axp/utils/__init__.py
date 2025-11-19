"""
AxProtocol Utilities Module

Shared utilities for logging, LLM, helpers, etc.
"""

from .logging import configure_logging
from .llm import get_llm_client, call_llm
from .helpers import (
    shingles,
    redundancy_score,
    uniqueness_nudge,
    extract_json_block,
    violates_exclusions,
    strict_reprompt,
    load_role_shapes,
)
from .sentinel import sentinel_verify
from .errors import append_session_error, write_sys_preview
from .session_logging import log_session, extract_kpi_rows
from .config_fingerprint import compute_config_hash, get_config_files_list

__all__ = [
    'configure_logging',
    'get_llm_client',
    'call_llm',
    'shingles',
    'redundancy_score',
    'uniqueness_nudge',
    'extract_json_block',
    'violates_exclusions',
    'strict_reprompt',
    'load_role_shapes',
    'sentinel_verify',
    'append_session_error',
    'write_sys_preview',
    'log_session',
    'extract_kpi_rows',
    'compute_config_hash',
    'get_config_files_list',
]

