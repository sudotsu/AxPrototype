# AxProtocol v2.7 — Config‑Driven, Sentinel‑Audited Reasoning OS

AxProtocol is a **self-auditing, directive-aware AI reasoning kernel**.
Every chain runs multi-role agents (Strategist → Analyst → Producer → Courier → Critic), is scored by TAES (Truth / Alignment / Efficiency / Signal) and is governed by hard and soft "directive" signals. All output is logged to an **append-only, cryptographically signed ledger** with config drift detection and independently verified by a detached **Sentinel** auditor.

---

## 🚀 Quick Start

### Install from PyPI

```bash
# Basic installation
pip install axprotocol

# With FastAPI API support
pip install axprotocol[api]

# With Streamlit UI support
pip install axprotocol[ui]

# With all optional dependencies
pip install axprotocol[api,ui,vector]
```

### Install from Source

```bash
git clone https://github.com/yourusername/axprotocol.git
cd AxProtocol
pip install -r requirements.txt

# Or install in development mode
pip install -e ".[dev]"
```

### Run Your First Chain

**Python Library:**
```python
from axprotocol import run_chain

strategist, analyst, producer, courier, critic, results = run_chain(
    objective="Book 5 local jobs in 7 days for a tree service",
    domain="marketing"
)

print(f"Strategist: {strategist[:100]}...")
print(f"TAES IV: {results['strategist']['taes']['integrity_vector']}")
```

**FastAPI API:**
```bash
# Install with API support
pip install axprotocol[api]

# Run API server
uvicorn sentinel_api:app --host 0.0.0.0 --port 8000

# Make request
curl -X POST "http://localhost:8000/run" \
  -H "Content-Type: application/json" \
  -d '{"objective": "Book 5 local jobs", "domain": "marketing"}'
```

**Streamlit UI:**
```bash
streamlit run app_axp.py
```

---

## 📋 Table of Contents

1. [Features](#features)
2. [Architecture](#architecture)
3. [Installation](#installation)
4. [Usage](#usage)
5. [Domains](#domains)
6. [Configuration](#configuration)
7. [Testing](#testing)
8. [Deployment](#deployment)
9. [Repository Structure](#repository-structure)
10. [Contributing](#contributing)

---

## ✨ Features

### Core Capabilities

- **Multi-Role Reasoning Chain**: Strategist → Analyst → Producer → Courier → Critic
- **TAES Evaluation**: Truth/Alignment/Efficiency/Signal scoring with domain-specific weights
- **Directive-Based Governance**: 29 directives (D0-D28) enforcing truth, logic, and compliance
- **Immutable Audit Ledger**: Cryptographically signed (Ed25519) append-only ledger
- **Config Drift Detection**: SHA256 hash of all config files stored in every ledger entry
- **Sentinel Auditor**: Independent verification of ledger integrity and tampering detection
- **Domain-Specific Roles**: 9 domains (marketing, technical, ops, creative, education, product, strategy, research, finance)
- **Fault Injection Testing**: Δ1-Δ4 test suites for adversarial resilience

### Recent Additions (v2.7)

- ✅ **PyPI Package**: Installable as `axprotocol` with optional FastAPI API
- ✅ **Config Hash**: Immutable proof that protocol config hasn't drifted
- ✅ **Finance Domain**: High-stakes financial modeling with risk-weighted TAES
- ✅ **Δ4 Tests**: Ledger tampering detection (forged/modified entries)
- ✅ **Modular Architecture**: Refactored into `axp/` subpackages for maintainability
- ✅ **Producer-Courier Handoff**: Explicit asset validation and enforcement
- ✅ **Enhanced Logging**: Comprehensive error logging with stack traces

---

## 🏗️ Architecture

### Multi-Role Chain

```
Objective
    ↓
Strategist (Positioning, Audience, Messaging)
    ↓
Analyst (Validation, KPIs, Risk Assessment)
    ↓
Producer (Assets, Content, Deliverables)
    ↓
Courier (Schedule, Deployment, Operations)
    ↓
Critic (Quality Audit, Optimization, Go/No-Go)
    ↓
Results + TAES Scores + Ledger Entries
```

### Governance Layers

1. **Directive Enforcement**: Hard gates (D3, D2, D13, D20-24) and soft signals (D0, SECRETS, FABRICATION)
2. **TAES Scoring**: Domain-specific weights applied to Logical/Practical/Probable axes
3. **Ledger Signing**: Ed25519 signatures (HMAC fallback) for cryptographic integrity
4. **Sentinel Verification**: Independent auditor checks signatures, hashes, and detects tampering
5. **Config Hash**: SHA256 fingerprint of all config files stored in every entry

### Deployment Architecture

```
┌─────────────────────────────┐
│           Traefik           │
│  HTTPS (ACME TLS), rate-lim │
└────────────┬────────────────┘
   8443 (AxP)│      │443 (Sentinel)
             │      │
┌────────────▼──┐  ┌▼─────────────┐
│   AxProtocol  │  │   Sentinel   │
│ (Streamlit/   │  │ (FastAPI:    │
│  kernel)      │  │  /health,    │
│               │  │  /verify,    │
│ - writes logs │  │  /reports)   │
│ - writes      │  │ - reads      │
│   signed      │  │   read-only  │
│   ledger      │  │   ledger     │
│ - config_hash │  │ - detects    │
│   in entries  │  │   tampering  │
└──────┬────────┘  └──────┬───────┘
       │                   │
       │ mounts            │ mounts (read-only)
┌──────▼────────┐    ┌─────▼─────────┐
│ logs/ledger   │    │ logs/reports  │
│ (jsonl +      │    │ (sentinel     │
│  public key)  │    │  outputs)     │
└───────────────┘    └───────────────┘
```

---

## 📦 Installation

### Requirements

- Python 3.10+
- OpenAI API key (set `OPENAI_API_KEY` environment variable)

### PyPI Installation (Recommended)

```bash
pip install axprotocol
```

**Optional Extras:**
- `[api]` - FastAPI REST API (`fastapi`, `uvicorn`, `pydantic`)
- `[ui]` - Streamlit UI (`streamlit`, `matplotlib`, `plotly`)
- `[vector]` - Vector database support (`pymilvus`, `grpcio`, `ujson`)
- `[dev]` - Development tools (`pytest`, `black`, `ruff`)

### Source Installation

```bash
git clone https://github.com/yourusername/axprotocol.git
cd AxProtocol
pip install -r requirements.txt

# Development mode
pip install -e ".[dev]"
```

### Environment Setup

Create `.env` file:
```bash
OPENAI_API_KEY=your-api-key-here
TIER=DEV  # or PREP, CLIENT
LOG_LEVEL=INFO
```

---

## 💻 Usage

### Python Library

```python
from axprotocol import run_chain

# Execute chain with auto-detected domain
strategist, analyst, producer, courier, critic, results = run_chain(
    objective="Book 5 local jobs in 7 days for a tree service"
)

# Execute with specific domain
results = run_chain(
    objective="Model $50k seed round ROI with NPV and IRR",
    domain="finance"
)

# Access results
print(f"Domain: {results['domain']}")
print(f"Strategist TAES IV: {results['strategist']['taes']['integrity_vector']}")
print(f"Config Hash: {results.get('config_hash', 'N/A')}")
```

### FastAPI REST API

**Start Server:**
```bash
pip install axprotocol[api]
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

**Example Request:**
```bash
curl -X POST "http://localhost:8000/run" \
  -H "Content-Type: application/json" \
  -d '{
    "objective": "Model $50k seed round ROI",
    "domain": "finance"
  }'
```

### Streamlit UI

```bash
streamlit run app_axp.py
```

Features:
- Objective input with domain override
- Real-time chain execution
- TAES score visualization
- Ledger entry browser
- Session history
- Export capabilities

### CLI

```bash
# Run with default objective
python run_axp.py

# Run with custom objective
python run_axp.py "Book 5 local jobs in 7 days"

# Run with domain override
python run_axp.py "Model ROI" finance

# Smoke governance test (no LLM, no ledger writes)
python run_axp.py --smoke-governance
```

---

## 🌍 Domains

AxProtocol supports 9 domains with domain-specific roles and TAES weights:

| Domain | TAES Weights | Use Cases |
|--------|--------------|-----------|
| **Marketing** | L:0.3, P:0.2, Pr:0.5 | Campaigns, lead gen, content |
| **Technical** | L:0.6, P:0.35, Pr:0.05 | Code, architecture, systems |
| **Ops** | L:0.4, P:0.45, Pr:0.15 | Workflows, processes, efficiency |
| **Creative** | L:0.35, P:0.25, Pr:0.4 | Content creation, storytelling |
| **Education** | L:0.45, P:0.35, Pr:0.2 | Curriculum, training, learning |
| **Product** | L:0.4, P:0.4, Pr:0.2 | Product dev, features, roadmap |
| **Strategy** | L:0.45, P:0.35, Pr:0.2 | Business strategy, planning |
| **Research** | L:0.55, P:0.3, Pr:0.15 | Data analysis, research design |
| **Finance** | L:0.5, P:0.35, Pr:0.15 | Financial modeling, risk analysis |

**Domain Auto-Detection:**
```python
from domain_detector import DomainDetector

detector = DomainDetector()
domain = detector.detect("Model $50k seed round ROI")
# Returns: "finance" (with confidence score)
```

---

## ⚙️ Configuration

### Core Config Files

- **`config/governance_coupling.json`** - Hard/soft signal definitions
- **`config/role_shapes.json`** - Role boundary enforcement (banned phrases)
- **`config/taes_weights.json`** - Domain-specific TAES weight matrices
- **`config/logging.yaml`** - Python logging configuration
- **`config/auth_settings.yaml`** - Authentication settings
- **`DomainConfig.json`** - Domain detection keywords and weights

### Config Hash

Every ledger entry includes a `config_hash` (SHA256) of all protocol config files:
- Governance coupling
- Role shapes
- TAES weights
- All directive markdown files

**Usage:**
```python
from axprotocol import compute_config_hash
from pathlib import Path

hash_val = compute_config_hash(Path("."))
# Returns: "sha256:29de65ae94973957a7fc324..."
```

**Drift Detection:**
```python
# Compare config hashes between sessions
entry_a = get_last_n_entries(1)[0]
hash_a = entry_a["config_hash"]

hash_b = compute_config_hash(Path("."))

if hash_a != hash_b:
    print("⚠️ Config drift detected!")
```

---

## 🧪 Testing

### Run Tests

```bash
# All tests
pytest verify/ -v

# Specific test suites
pytest verify/test_directive_enforcement_core.py -v
pytest verify/test_taes_adherence.py -v
pytest verify/test_config_hash.py -v
pytest verify/test_fault_injection_pytest.py -v

# Fault injection tests
python fault_injection.py --run Δ1,Δ2,Δ3,Δ4
```

### Test Suites

- **Δ1**: Malformed Objectives (empty, nonsensical, contradictory)
- **Δ2**: Score Manipulation (invalid scores, missing dimensions)
- **Δ3**: Protocol Bypass Attempts (directive violations, unauthorized changes)
- **Δ4**: Ledger Tampering (forged entries, signature validation)

### Test Coverage

- Directive enforcement (D1-D14)
- TAES integrity and scoring
- Ledger signature verification
- Config hash computation
- Domain detection
- Fault injection resilience

---

## 🚢 Deployment

### Docker Compose

```bash
docker compose build
docker compose up -d
```

**Services:**
- **AxProtocol** (Streamlit) - Port 8443
- **Sentinel** (FastAPI) - Port 443
- **Traefik** - Reverse proxy with TLS

### Production Checklist

- [ ] Set `OPENAI_API_KEY` in `.env`
- [ ] Configure `TIER` (DEV/PREP/CLIENT)
- [ ] Set up ACME domains in Traefik
- [ ] Configure rate limiting
- [ ] Set up logging rotation
- [ ] Configure Sentinel public key path
- [ ] Run smoke tests: `./scripts/smoke.sh`

### GitHub Actions

Automated build and deployment:
- Builds Docker images
- Pushes to GHCR
- Deploys via SSH to VPS
- Runs smoke tests

---

## 📁 Repository Structure

```
AxProtocol/
├── axprotocol/              # Public API package (PyPI)
│   └── __init__.py
├── axp/                     # Internal package (modular)
│   ├── orchestration/       # Chain execution
│   │   ├── chain.py         # Main run_chain()
│   │   ├── role_executor.py
│   │   ├── role_loader.py
│   │   └── ...
│   ├── detection/           # Governance signal detection
│   │   └── signals.py
│   ├── validation/          # Schema validators
│   │   └── validators.py
│   ├── directives/          # Directive loading/composition
│   │   ├── loader.py
│   │   └── composer.py
│   ├── governance/          # Ledger signing, coupling
│   │   ├── ledger.py
│   │   └── coupling.py
│   ├── sentinel/            # Sentinel auditor
│   │   ├── sentinel.py
│   │   ├── verify_ledger.py
│   │   └── sentinel_app.py
│   └── utils/               # Shared utilities
│       ├── logging.py
│       ├── llm.py
│       ├── config_fingerprint.py
│       └── ...
├── config/                  # Configuration files
│   ├── governance_coupling.json
│   ├── role_shapes.json
│   ├── taes_weights.json
│   └── ...
├── protocol/                # Directive markdown files
│   ├── AxProtocol_v2.4_CORE_DIRECTIVES.md
│   ├── AxProtocol_v2.4_TAES_EVALUATION.md
│   └── ...
├── roles/                   # Domain-specific role definitions
│   ├── marketing/
│   ├── technical/
│   ├── finance/
│   └── ...
├── verify/                  # Test suites
│   ├── test_directive_enforcement_core.py
│   ├── test_taes_adherence.py
│   ├── test_config_hash.py
│   ├── test_fault_injection_delta4.py
│   └── ...
├── app_axp.py              # Streamlit operator console
├── run_axp.py             # CLI entry point
├── sentinel_api.py        # FastAPI REST API
├── taes_evaluation.py    # TAES scoring engine
├── domain_detector.py    # Domain auto-detection
├── ledger.py             # SQLite audit ledger
├── pyproject.toml        # PyPI package metadata
├── requirements.txt      # Python dependencies
├── docker-compose.yml    # Docker orchestration
└── README.md
```

---

## 🔐 Security & Auditing

### Ledger Integrity

- **Cryptographic Signing**: Ed25519 signatures (HMAC fallback)
- **Hash Chain**: Each entry links to previous via hash
- **Config Hash**: SHA256 fingerprint of all config files
- **Tampering Detection**: Sentinel verifies signatures and detects modifications

### Sentinel Auditor

Independent verification:
- `/verify` - Recomputes hashes & signatures
- Detects forged entries
- Detects modified entries
- Detects malformed JSON
- Writes timestamped reports

### Fault Injection Tests

- **Δ1**: Malformed inputs
- **Δ2**: Score manipulation
- **Δ3**: Protocol bypass attempts
- **Δ4**: Ledger tampering

---

## 📚 Documentation

- **Protocol Directives**: `protocol/AxProtocol_v2.4_*.md`
- **PyPI Packaging**: `PYPI_PACKAGING.md`
- **Config Hash**: `CONFIG_HASH_IMPLEMENTATION.md`
- **Finance Domain**: `FINANCE_DOMAIN_IMPLEMENTATION.md`
- **Δ4 Tests**: `DELTA4_IMPLEMENTATION.md`
- **Refactoring**: `REFACTORING_SUMMARY.md`

---

## 🤝 Contributing

### Development Setup

```bash
git clone https://github.com/yourusername/axprotocol.git
cd AxProtocol
pip install -e ".[dev]"
pytest verify/ -v
```

### Code Style

- Follow PEP 8
- Use type hints
- Add docstrings
- Run `black` and `ruff` before committing

### Testing

- Add tests for new features
- Run fault injection tests: `python fault_injection.py --run Δ1,Δ2,Δ3,Δ4`
- Ensure all security tests pass

---

## 📄 License

Evaluation license - see `AxProtocol_Evaluation_License_v0.1.txt`.
Commercial use requires written authorization.

---

## 🎯 Key Principles

**Truth > Obedience**
**Signed. Sentineled. Config-driven.**

---

## 📞 Support

- **GitHub Issues**: https://github.com/yourusername/axprotocol/issues
- **Documentation**: See `docs/` directory
- **API Docs**: http://localhost:8000/docs (when API running)

---

**Version**: 2.7
**Last Updated**: November 2025
**Status**: Production Ready ✅
