"""
AxProtocol Orchestration Module

Main chain execution and role coordination.
"""

from .chain import run_chain
from .role_executor import run_role_json
from .role_loader import load_domain_roles
from .registry import init_registry
from .qa import run_micro_qa
from .composer import compose_final_report

__all__ = [
    'run_chain',
    'run_role_json',
    'load_domain_roles',
    'init_registry',
    'run_micro_qa',
    'compose_final_report',
]


