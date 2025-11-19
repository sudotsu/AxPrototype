# PyPI Packaging Guide for AxProtocol

## Overview

AxProtocol is packaged as `axprotocol` on PyPI with an optional FastAPI API (`sentinel-api`).

## Package Structure

```
AxProtocol/
├── axprotocol/          # Public API package (PyPI)
│   └── __init__.py      # Re-exports from axp/
├── axp/                 # Internal package (backward compatible)
│   ├── orchestration/
│   ├── detection/
│   ├── validation/
│   ├── directives/
│   ├── governance/
│   ├── sentinel/
│   └── utils/
├── pyproject.toml       # Package metadata and dependencies
├── sentinel_api.py      # FastAPI REST API
└── README.md
```

## Installation

### Basic Installation

```bash
pip install axprotocol
```

### With Optional Dependencies

```bash
# With FastAPI API support
pip install axprotocol[api]

# With Streamlit UI support
pip install axprotocol[ui]

# With vector database support
pip install axprotocol[vector]

# With all optional dependencies
pip install axprotocol[api,ui,vector]
```

## Usage

### Python Library

```python
from axprotocol import run_chain

# Execute chain
strategist, analyst, producer, courier, critic, results = run_chain(
    objective="Book 5 local jobs in 7 days for a tree service",
    domain="marketing"
)

print(f"Strategist: {strategist[:100]}...")
print(f"Results: {results}")
```

### FastAPI API

```bash
# Install with API support
pip install axprotocol[api]

# Run API server
uvicorn sentinel_api:app --host 0.0.0.0 --port 8000
```

**API Endpoints:**

- `POST /run` - Execute AxProtocol chain
  ```json
  {
    "objective": "Book 5 local jobs in 7 days",
    "domain": "marketing",
    "session_id": "optional-id"
  }
  ```

- `GET /health` - Health check
- `GET /version` - API version
- `GET /domains` - List available domains
- `GET /docs` - Interactive API documentation (Swagger UI)

**Example API Request:**

```bash
curl -X POST "http://localhost:8000/run" \
  -H "Content-Type: application/json" \
  -d '{
    "objective": "Book 5 local jobs in 7 days for a tree service",
    "domain": "marketing"
  }'
```

## Building and Publishing

### Prerequisites

```bash
pip install build twine
```

### Build Package

```bash
python -m build
```

This creates:
- `dist/axprotocol-2.4.0-py3-none-any.whl` (wheel)
- `dist/axprotocol-2.4.0.tar.gz` (source distribution)

### Test Installation Locally

```bash
pip install dist/axprotocol-2.4.0-py3-none-any.whl
```

### Publish to PyPI

**Test PyPI (for testing):**
```bash
twine upload --repository testpypi dist/*
```

**Production PyPI:**
```bash
twine upload dist/*
```

**Note:** You'll need PyPI credentials (username/token) configured.

## Configuration Files

The package includes configuration files that are installed with the package:

- `config/governance_coupling.json` - Governance coupling rules
- `config/role_shapes.json` - Role boundary definitions
- `config/taes_weights.json` - TAES weight matrices
- `protocol/*.md` - Directive markdown files
- `roles/**/*.txt` - Domain-specific role definitions

These are accessible via:

```python
from pathlib import Path
import axprotocol

# Get package directory
package_dir = Path(axprotocol.__file__).parent.parent
config_dir = package_dir / "config"
protocol_dir = package_dir / "protocol"
```

## Environment Variables

AxProtocol requires environment variables:

```bash
# Required
OPENAI_API_KEY=your-api-key

# Optional
TIER=DEV|PROD
LOG_LEVEL=INFO
```

Create a `.env` file or set environment variables before running.

## Backward Compatibility

The internal `axp/` package remains available for backward compatibility:

```python
# Old imports still work
from axp.orchestration import run_chain
from axp.validation import validate_S

# New public API (recommended)
from axprotocol import run_chain
from axprotocol import validate_S
```

## Development

### Install in Development Mode

```bash
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest verify/
```

### Run API Locally

```bash
# Install with API dependencies
pip install -e ".[api]"

# Run API
python sentinel_api.py
# or
uvicorn sentinel_api:app --reload
```

## Versioning

Version follows semantic versioning:
- `MAJOR.MINOR.PATCH`
- Current: `2.4.0`

Update version in:
- `pyproject.toml` → `[project] version`
- `axprotocol/__init__.py` → `__version__`
- `sentinel_api.py` → Import from `axprotocol.__version__`

## License

MIT License (specified in `pyproject.toml`)

## Support

- GitHub Issues: https://github.com/yourusername/axprotocol/issues
- Documentation: See `README.md` and inline docstrings

