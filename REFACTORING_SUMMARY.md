# Refactoring Summary: Breaking Up `run_axp.py`

## Overview

`run_axp.py` (1518 lines) has been refactored into a modular structure organized by responsibility, not by origin. This improves maintainability, testability, and code clarity.

## New Module Structure

### `axp/orchestration/` - Chain Execution
- **`chain.py`** - Main `run_chain()` orchestrator
- **`role_executor.py`** - Role execution and JSON parsing
- **`role_loader.py`** - Domain-specific role loading
- **`registry.py`** - Registry (blackboard) management
- **`qa.py`** - Micro Q&A helpers
- **`composer.py`** - Final report composition

### `axp/detection/` - Governance Signal Detection
- **`signals.py`** - Sycophancy, contradiction, ambiguity detection

### `axp/validation/` - Schema Validators
- **`validators.py`** - Validators for S, A, P, C, X outputs

### `axp/directives/` - Directive Management
- **`loader.py`** - Load directives from markdown files
- **`composer.py`** - Compose system prompts from directives

### `axp/utils/` - Shared Utilities
- **`logging.py`** - Logging configuration
- **`llm.py`** - LLM client wrapper
- **`helpers.py`** - Shingles, redundancy, JSON extraction, etc.
- **`sentinel.py`** - Sentinel verification
- **`errors.py`** - Error logging helpers

## Naming Convention Decision

**We did NOT use prefixes/suffixes** (e.g., `run_axp_chain.py`, `run_axp_validators.py`).

### Why Not Prefixes?

1. **Doesn't Scale**: Files often influence multiple areas. A validator might be used by chain execution, testing, and UI. Which prefix?
2. **IDE Tools**: Modern IDEs show imports/usage. You can see `from axp.validation import validate_S` and immediately know it's a validator.
3. **Python Namespacing**: Modules already provide namespacing (`axp.orchestration.chain` vs `run_axp_chain`).
4. **Readability**: `chain.py` is clearer than `run_axp_chain.py`. The directory structure (`axp/orchestration/`) already indicates purpose.
5. **Maintenance**: If you rename `run_axp.py` to `main.py`, do you rename all prefixed files? No.

### What We Did Instead

- **Clear, descriptive names**: `chain.py`, `validators.py`, `signals.py`
- **Logical directory structure**: Grouped by responsibility
- **Clean imports**: `from axp.orchestration import run_chain`
- **Documentation**: Each module has docstrings explaining purpose

## Migration Path

The original `run_axp.py` can be updated to import from the new modules:

```python
from axp.orchestration import run_chain
from axp.directives import load_directives
# ... etc
```

This maintains backward compatibility while allowing gradual migration.

## Benefits

1. **Maintainability**: Each module has a single, clear responsibility
2. **Testability**: Modules can be tested independently
3. **Reusability**: Utilities can be imported by other parts of the codebase
4. **Clarity**: File names indicate purpose without needing prefixes
5. **Scalability**: Easy to add new modules without naming conflicts

## Next Steps

1. Update `run_axp.py` to import from new modules
2. Update `app_axp.py` to use new imports
3. Test the refactored code
4. Remove duplicate code from `run_axp.py` once migration is complete

