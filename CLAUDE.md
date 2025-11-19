# AxProtocol - Codebase Analysis for Claude Code

## Project Overview

**AxProtocol** is a self-auditing, directive-aware AI reasoning kernel that orchestrates multi-role reasoning chains with cryptographic ledger signing and independent Sentinel auditing. It's built as an **end-to-end governance system** where every reasoning operation is scored, logged, and verified.

**Current Version:** v2.6  
**Status:** Production-ready with active development  
**License:** Evaluation (commercial use requires authorization)

---

## 1. Project Type & Tech Stack

### Framework & Architecture
- **Core Framework:** Python 3.11-based reasoning engine
- **UI/Dashboard:** Streamlit (Operator Console)
- **API Server:** FastAPI (Sentinel auditor)
- **Reverse Proxy:** Traefik v2.11 (HTTPS, TLS, rate limiting)
- **Container Orchestration:** Docker Compose v3.9

### Primary Languages & Technologies
- **Python 3.11** - Main development language
- **OpenAI API** - GPT-4o, GPT-4o-turbo, GPT-4o-mini for reasoning chains
- **Cryptography:** PyNaCl (Ed25519 signatures), HMAC fallback
- **Vector Database:** Milvus (via pymilvus for future Bridge sync)
- **Data Processing:** Pandas, NumPy, Plotly, Matplotlib

### Key Dependencies (from requirements.txt)
```
streamlit>=1.28.0          # Web console
openai>=1.3.0              # LLM API
python-dotenv>=1.0.0       # Environment configuration
pandas>=2.0.0              # Data manipulation
numpy>=1.24.0              # Numerical computing
matplotlib>=3.7.0          # Data visualization
plotly>=5.17.0             # Interactive charts
PyJWT>=2.8.0               # JWT token handling
rich>=13.0.0               # Terminal formatting
requests>=2.31.0           # HTTP client
pymilvus>=2.6.0            # Vector DB
grpcio>=1.66.0             # gRPC support
ujson>=2.0.0               # JSON serialization
```

### Additional Production Dependencies (Dockerfile)
- `fastapi` - Sentinel API
- `uvicorn` - ASGI server
- `pynacl` - Cryptographic signing

---

## 2. Key Configuration Files

### Core Configuration
- **`.env`** - Environment variables for OpenAI API, model tiers, domain settings, auth, logging, deployment domains
- **`DomainConfig.json`** - Multi-domain governance configuration (source of truth for domain names)
- **`.gitignore`** - Standard Python + secrets exclusions

### Application Configuration
- **`config/governance_coupling.json`** - Hard/soft signal definitions for TAES enforcement
  - Hard signals: D3, D2, D13, D7, D11, D20-24 (enforce strict limits)
  - Soft signals: D0, SECRETS, FABRICATION, DOMAIN_MISROUTING, OBSERVABILITY_GAP (logged for audit)
- **`config/taes_weights.json`** - Domain-specific TAES (Truth/Alignment/Efficiency/Signal) weight matrices
- **`config/role_shapes.json`** - Banned phrase patterns per role (Strategist, Analyst, Producer, Courier, Critic)
- **`config/auth_settings.yaml`** - Authentication configuration
- **`config/logging.yaml`** - Python logging configuration
- **`config/ui_presentation.json`** - Streamlit UI presentation settings

### Docker & Deployment
- **`docker-compose.yml`** - Multi-container orchestration (Traefik + AxP + Sentinel)
- **`Dockerfile.axp`** - AxProtocol Streamlit application container
- **`Dockerfile.sentinel`** - Sentinel auditor FastAPI container
- **`.env.example`** - Documented template for all required environment variables
- **`.github/workflows/deploy.yml`** - GitHub Actions CI/CD (build & push to GHCR, SSH deploy)

---

## 3. Project Structure & Main Directories

```
AxProtocol/
├── Core Application Files
│   ├── run_axp.py                    # Multi-agent orchestrator (1482 lines)
│   ├── app_axp.py                    # Streamlit console (1190 lines)
│   ├── taes_evaluation.py            # TAES scoring engine (281 lines)
│   ├── score_validator.py            # Score validation & formatting (884 lines)
│   ├── domain_detector.py            # Auto-detect domain from text (244 lines)
│   ├── load_roles.py                 # Role prompt loader (529 lines)
│   ├── auth.py                       # CAM auth/token handling (1245 lines)
│   ├── ledger.py                     # Legacy ledger module (174 lines)
│   └── dashboard.py                  # Dashboard utilities (1056 lines)
│
├── axp/ (Core Modules)
│   ├── governance/
│   │   ├── ledger.py                 # Ed25519 signing layer + HMAC fallback
│   │   └── coupling.py               # Config-driven governance enforcement
│   └── sentinel/
│       ├── sentinel.py               # CLI audit tool
│       ├── sentinel_app.py           # FastAPI audit server (/health, /verify, /reports)
│       └── verify_ledger.py          # Signature + hash verification logic
│
├── config/
│   ├── governance_coupling.json
│   ├── taes_weights.json
│   ├── role_shapes.json
│   ├── auth_settings.yaml
│   ├── logging.yaml
│   ├── ui_presentation.json
│   └── role_examples/                # Reference prompts for each role
│       ├── strategist.md
│       ├── analyst.md
│       ├── producer.md
│       ├── courier.md
│       └── critic.md
│
├── roles/ (Domain-Specific Prompts)
│   ├── creative/
│   ├── education/
│   ├── marketing/
│   ├── ops/
│   ├── product/
│   ├── research/
│   ├── strategy/
│   └── technical/
│   (Each domain contains: strategist_stable.txt, analyst_stable.txt, 
│    producer_stable.txt, courier_stable.txt, critic_stable.txt)
│
├── verify/ (Test Suite)
│   ├── conftest.py                   # Pytest fixtures & test utilities
│   ├── test_directive_enforcement_core.py   # Governance enforcement tests
│   └── test_taes_adherence.py        # TAES scoring validation tests
│
├── logs/ (Runtime Output)
│   ├── ledger/                       # Append-only signed ledger (jsonl + public.key)
│   ├── sessions/                     # Session logs
│   ├── reports/                      # Sentinel audit reports
│   └── exports/                      # User exports (CSV, JSON, Markdown)
│
├── scripts/ (Automation)
│   ├── smoke.sh                      # Post-deploy health check
│   ├── smoke_governance.sh           # Test governance enforcement
│   ├── validate_all.sh               # Full validation suite
│   ├── validate_governance_config.py # Config validation
│   ├── validate_taes_weights.py      # TAES weight validation
│   └── sync_bridge.py                # Future Bridge sync automation
│
├── docs/ (Documentation)
│   ├── app_axp_docs/                 # UI documentation
│   │   ├── APP_AXP_V2.5_SUMMARY.md
│   │   └── DOMAIN_DETECTOR_UPDATE.md
│   └── auth_dashboard_docs/          # Auth & dashboard docs
│       ├── AUTH_V2.5_DOCUMENTATION.md
│       ├── DASHBOARD_DELIVERY.md
│       └── QUICK_START.md
│
├── traefik/
│   └── acme.json                     # Let's Encrypt ACME certificate storage
│
├── AxP_Public/                       # Public-facing assets
├── .github/
│   └── workflows/
│       └── deploy.yml                # CI/CD pipeline
├── docker-compose.yml                # Multi-container orchestration
├── Dockerfile.axp                    # AxP container definition
├── Dockerfile.sentinel               # Sentinel container definition
├── requirements.txt                  # Python dependencies
├── README.md                         # Main documentation
├── DEPLOY-INDEX.md                   # Deployment navigation guide
├── DomainConfig.json                 # Domain configuration
└── .env                              # Environment variables
```

### File Count Summary
- **Total Python files:** 23
- **Core app files:** ~8,149 lines of Python code
- **Config files:** 8 JSON/YAML
- **Role prompts:** 40 domain-specific prompt files
- **Test files:** 3 pytest modules
- **Scripts:** 8 automation scripts

---

## 4. Build & Development Commands

### Installation
```bash
# Clone repository
git clone https://github.com/axprotocol/axprotocol.git
cd AxProtocol

# Install Python dependencies
pip install -r requirements.txt

# Additional dependencies for full deployment (already in Dockerfile)
pip install streamlit uvicorn fastapi pynacl
```

### Running Locally

#### Streamlit Console
```bash
# Start the Operator Console (default port 8501)
streamlit run app_axp.py

# With custom port
streamlit run app_axp.py --server.port=8080
```

#### Multi-Agent Chain Execution
```bash
# Run a single reasoning chain
python run_axp.py

# Test governance enforcement (no ledger writes)
python run_axp.py --smoke-governance

# Interactive domain selector
python domain_detector.py
```

### Testing
```bash
# Run all deterministic tests
pytest verify/ -q

# Run specific test file
pytest verify/test_directive_enforcement_core.py -v

# Run with coverage
pytest verify/ --cov=run_axp --cov=taes_evaluation

# Test governance configuration
python scripts/validate_governance_config.py

# Test TAES weights
python scripts/validate_taes_weights.py
```

### Docker Deployment

#### Development (Local)
```bash
# Build both images
docker-compose build

# Start all services (Traefik + AxP + Sentinel)
docker-compose up -d

# Check logs
docker-compose logs -f axp
docker-compose logs -f sentinel

# Stop services
docker-compose down
```

#### Production (Automated via GitHub Actions)
The `.github/workflows/deploy.yml` handles:
1. Build Docker images on push to main
2. Push to GitHub Container Registry (GHCR)
3. SSH into VPS and deploy via docker compose

Manual production deploy:
```bash
# Pull images (assumes .env with DOMAIN_APP, DOMAIN_SENTINEL)
docker-compose pull

# Deploy with restart
docker-compose up -d

# Verify deployment
./scripts/smoke.sh
```

### Linting & Code Quality
```bash
# Python linting (if installed)
pylint run_axp.py
mypy run_axp.py

# Format check (Black would be used if added to requirements)
black --check .
```

### Environment Setup
```bash
# Copy and configure environment
cp .env.example .env

# Edit .env with your values:
# - OPENAI_API_KEY
# - DOMAIN_APP, DOMAIN_SENTINEL (for deployment)
# - ACME_EMAIL (for Let's Encrypt)
# - TIER (DEV, PREP, or CLIENT)
```

---

## 5. Architecture Overview

### High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    TRAEFIK (v2.11)                              │
│          HTTPS (ACME TLS), Rate Limiting, Routing               │
└─────────────────────────────────────────────────────────────────┘
                    ↓ 8443              ↓ 443
         ┌──────────────────┐    ┌─────────────────┐
         │  AxProtocol      │    │    Sentinel     │
         │  (Streamlit)     │    │   (FastAPI)     │
         │                  │    │                 │
         │ - Web Console    │    │ /health         │
         │ - TAES Engine    │    │ /verify         │
         │ - Ledger Write   │    │ /reports        │
         │ - Governance     │    │                 │
         └────────┬─────────┘    └────────┬────────┘
                  │                       │
         Reads/Writes             Reads (Read-Only)
                  ↓                       ↓
         ┌──────────────────┐    ┌─────────────────┐
         │  logs/ledger/    │    │  logs/reports/  │
         │  - audit.jsonl   │    │  - sentinel_*.  │
         │  - public.key    │    │    json         │
         │  - hash chain    │    └─────────────────┘
         └──────────────────┘
```

### Reasoning Chain Architecture (run_axp.py)

```
User Query (Objective)
         ↓
Domain Detection (DomainDetector)
         ↓
Multi-Role Agent Chain:
    Strategist → Analyst → Producer → Courier → Critic
    (Async orchestration with inter-role communication)
         ↓
TAES Evaluation
    (Logical, Practical, Probable scoring with domain weights)
         ↓
Governance Coupling
    (Hard gates: enforce caps/floors | Soft gates: log issues)
         ↓
Ledger Writing
    (Ed25519 signature + hash chain for immutability)
         ↓
Ledger Hash Returned
    (For downstream verification)
```

### Multi-Agent Role Pipeline

1. **Strategist** - High-level planning, objectives, constraints
2. **Analyst** - Evidence gathering, probability assessment, TAES evaluation
3. **Producer** - Detailed output generation, formatting
4. **Courier** - Final refinement, polish, delivery readiness
5. **Critic** - Falsification, governance checks, RDL (Reasoning Defense Layer) verification

**Key Features:**
- Domain-specific prompts loaded from `roles/<domain>/` directory
- Inter-role Q&A loops for clarification
- Schema-validated JSON output at each stage
- TAES evaluation after Producer output
- Governance enforcement before ledger write

### TAES Scoring System

**TAES = Truth + Alignment + Efficiency + Signal**

Domain-weighted components:
- **Logical** (L) - Internal consistency, contradiction detection
- **Practical** (Pr) - Actionability, implementation feasibility
- **Probable** (Pb) - Confidence, evidence-based reasoning
- **IV (Internal Validity)** = 0.5×L + 0.35×Pr + 0.15×Pb
- **IRD (Indicator of Reasoning Drift)** = 0.65 - IV + contradictions + hedges

Domain-specific weights in `config/taes_weights.json`:
- Code/Infrastructure: 60% Logical, 35% Practical, 5% Probable
- Ops/Process: 40% Logical, 45% Practical, 15% Probable
- Creative/Marketing: 30-35% Logical, 20-25% Practical, 40-50% Probable

### Governance Coupling (Directive Enforcement)

**Hard Signals** (strict enforcement via gov_coupling.json):
- D3 (Contradiction) - IV_max=0.68, IRD_min=0.55
- D2 (Ambiguity) - IV_max=0.64, IRD_min=0.60
- D13 (Sycophancy) - IV_max=0.62, IRD_min=0.65
- D7/D11 (Precedence) - IV_max=0.64, IRD_min=0.60
- D20-24 (Overconfidence) - IV_max=0.66, IRD_min=0.58

**Soft Signals** (logged for audit trail):
- D0 (Change Control)
- SECRETS (API keys, credentials)
- FABRICATION (Hallucinated citations, fake data)
- DOMAIN_MISROUTING (Request in wrong domain)
- OBSERVABILITY_GAP (Missing audit trail)

### Ledger & Cryptographic Signing

**Location:** `logs/ledger/audit_ledger.jsonl` and `logs/ledger/public.key`

**Signature Method:**
- Ed25519 (PyNaCl) if available, HMAC-SHA256 fallback
- Keys stored in `~/.axp_keys/` (private) + `logs/ledger/` (public)
- Each entry signed with timestamp, role, action, data hash

**Ledger Structure:**
```json
{
  "timestamp": "2025-11-05T12:34:56Z",
  "role": "Strategist",
  "action": "reasoning_output",
  "hash": "sha256_content_hash",
  "signature": "ed25519_hex_signature",
  "data": {
    "objective": "...",
    "output": "...",
    "taes": {...},
    "governance": {...}
  }
}
```

### Sentinel Auditor (FastAPI)

**Endpoints:**
- `GET /health` - Service status
- `GET /verify` - Re-verify ledger (hashes + signatures), write timestamped report
- `GET /reports` - List last 30 audit reports

**Read-Only Access:**
- Mounts `logs/ledger/` as read-only
- Outputs reports to `logs/reports/`
- Cannot modify ledger (append-only on AxP side)

---

## 6. Documentation & Developer Guides

### Main Documentation Files
- **`README.md`** (8,343 bytes) - Main entry point with v2.6 overview, quick start, architecture
- **`DEPLOY-INDEX.md`** (7,683 bytes) - Navigation guide for deployment documentation
- **`DEPLOY-GUIDE.md`** - Step-by-step deployment instructions
- **`CRITICAL-FIXES.md`** - Technical deep-dive on recent fixes
- **`ROI-IMPACT.md`** - Financial justification and metrics

### Developer Guides in `/docs`
- **`docs/app_axp_docs/APP_AXP_V2.5_SUMMARY.md`** - Console features and fixes
- **`docs/app_axp_docs/DOMAIN_DETECTOR_UPDATE.md`** - Domain auto-detection usage
- **`docs/auth_dashboard_docs/AUTH_V2.5_DOCUMENTATION.md`** - Authentication details
- **`docs/auth_dashboard_docs/DASHBOARD_QUICK_START.md`** - Dashboard setup guide

### Embedded Code Documentation
- **Docstrings:** Most functions have comprehensive docstrings (e.g., `run_chain()`, `evaluate_taes()`)
- **Type Hints:** Extensive use of Python typing throughout
- **Inline Comments:** Governance enforcement logic well-documented in `run_axp.py` and `axp/governance/`

### Key Architecture Docs in Code
```python
# run_axp.py
# - Lines 1-50: Architecture overview and v2.4 changes
# - Lines 64-93: Logging configuration
# - Lines 100-200: Compose system prompt logic
# - Lines 500-700: Multi-agent chain orchestration

# axp/governance/coupling.py
# - Full governance coupling architecture
# - Hard/soft signal explanation
# - IV/IRD threshold enforcement

# axp/sentinel/verify_ledger.py
# - Signature verification algorithm
# - Hash chain validation
```

---

## 7. Scripts & Common Development Workflows

### Deployment Scripts
- **`scripts/smoke.sh`** - Post-deployment health check (app root + sentinel + verify)
- **`scripts/smoke_governance.ps1`** / `smoke_governance.sh` - Test governance enforcement
- **`scripts/validate_all.sh`** - Run full validation suite
- **`scripts/validate_governance_config.py`** - Check governance_coupling.json syntax
- **`scripts/validate_taes_weights.py`** - Validate TAES weight matrices

### Automation Scripts
- **`scripts/sync_bridge.py`** - Future Bridge vector DB sync (placeholder)

### GitHub Actions CI/CD
**`.github/workflows/deploy.yml`** automates:
1. Build stage: Docker build for both AxP + Sentinel images, push to GHCR
2. Deploy stage: SCP compose/env to VPS, SSH pull + up -d, system prune

### Common Development Workflows

#### 1. Local Development Loop
```bash
# 1. Make code changes
vim run_axp.py

# 2. Test locally
streamlit run app_axp.py

# 3. Run pytest suite
pytest verify/ -q

# 4. Validate configs
python scripts/validate_governance_config.py

# 5. Git commit
git add .
git commit -m "feat: add new governance signal"
git push  # Triggers GH Actions
```

#### 2. Adding a New Domain
```bash
# 1. Update DomainConfig.json
vim DomainConfig.json  # Add domain definition

# 2. Create role prompts
mkdir roles/mynewdomain
cp roles/creative/*_stable.txt roles/mynewdomain/
# Edit each role prompt for domain-specific behavior

# 3. Add TAES weights
vim config/taes_weights.json  # Add weights for mynewdomain

# 4. Test domain detection
python domain_detector.py
# Type a query: "Tell me about X" → should detect mynewdomain

# 5. Test end-to-end
python run_axp.py  # Should load mynewdomain roles
```

#### 3. Governance Enforcement Testing
```bash
# 1. Dry-run enforcement without ledger writes
python run_axp.py --smoke-governance

# 2. Test specific directive
pytest verify/test_directive_enforcement_core.py::test_d3_contradiction -v

# 3. Verify ledger integrity
python axp/sentinel/sentinel.py

# 4. Review soft signal logs
cat logs/ird_log.csv | tail -20
```

#### 4. Deployment Workflow
```bash
# 1. Test locally with docker-compose
docker-compose build
docker-compose up -d
sleep 5

# 2. Run smoke test
./scripts/smoke.sh

# 3. Check logs
docker-compose logs -f axp | head -50

# 4. Push to main (triggers GH Actions)
git push origin main

# 5. Monitor GH Actions
gh run watch

# 6. Verify production deployment
curl https://${DOMAIN_APP}
curl https://${DOMAIN_SENTINEL}/health
```

#### 5. Adding New Governance Rules
```bash
# 1. Define signal in governance_coupling.json
vim config/governance_coupling.json
# Add new signal entry with mode (hard/soft), iv_max, ird_min

# 2. Update enforcement logic
vim run_axp.py  # Or axp/governance/coupling.py
# Add signal check in apply_governance_coupling()

# 3. Write test
vim verify/test_directive_enforcement_core.py
# Add test_mynewsignal() function

# 4. Validate
pytest verify/test_directive_enforcement_core.py::test_mynewsignal -v

# 5. Document in README
vim README.md  # Add signal description
```

---

## 8. Environment & Configuration

### Key Environment Variables

#### OpenAI/LLM Configuration
```
OPENAI_API_KEY              # Required for API calls
MODEL_DEV                   # Development model (e.g., gpt-4o-mini)
MODEL_PREP                  # Preparation model (e.g., gpt-4o-turbo)
MODEL_CLIENT                # Production model (e.g., gpt-4o)
TIER                        # Tier level: DEV, PREP, or CLIENT
TEMPERATURE                 # LLM temperature (default 0.4)
MAX_TOKENS                  # Max tokens per response (default 1600)
```

#### Multi-Domain Configuration
```
DOMAIN                      # Override detected domain (optional)
DOMAIN_CONFIDENCE_THRESHOLD # Min confidence for auto-detection (default 0.6)
DOMAIN_FALLBACK             # Fallback domain if detection fails
```

#### Governance & Enforcement
```
TAES_ENABLED                # Enable TAES evaluation (default true)
LEDGER_ENABLED              # Enable ledger signing (default true)
CAM_ENABLED                 # Enable CAM authentication (default true)
CAM_LEASE_DURATION          # Auth token lease duration (default 180s)
ENFORCE_DIRECTIVES          # Which directives to enforce
```

#### Logging & Debugging
```
LOG_DIR                     # Logs directory (default "logs")
LOG_LEVEL                   # Logging level (DEBUG, INFO, WARNING)
SESSION_LOGGING             # Enable session logs (default true)
KPI_LOGGING                 # Enable KPI tracking (default true)
DEBUG                       # Enable debug mode (default false)
SAVE_RAW_RESPONSES          # Save raw LLM responses (default true)
```

#### Deployment (Docker/Traefik)
```
DOMAIN_APP                  # AxProtocol domain (e.g., axprotocol.io)
DOMAIN_SENTINEL             # Sentinel domain (e.g., sentinel.axprotocol.io)
ACME_EMAIL                  # Email for Let's Encrypt
ACME_FILE                   # Path to acme.json (./traefik/acme.json)
AXP_IMAGE                   # Docker image for AxP
SENTINEL_IMAGE              # Docker image for Sentinel
TIER                        # Deployment tier (CLIENT for production)
ENABLE_SIGNUP               # Allow new user signup (default true)
FREE_TIER_LIMIT             # Max free users before paywall (default 50)
```

### Configuration Priority Order
1. Environment variables (`.env`)
2. Config files (`config/*.json`, `DomainConfig.json`)
3. Hardcoded defaults in code

---

## 9. Dependencies & External Services

### Required External Services
- **OpenAI API** - GPT-4o models for reasoning
- **Docker** - Container runtime (for production)
- **Let's Encrypt (ACME)** - TLS certificates via Traefik

### Optional/Future Services
- **Milvus Vector Database** - For Bridge sync automation (infrastructure future)
- **MongoDB** - For waitlist backend (planned)
- **Vercel/FastAPI** - For waitlist API deployment (planned)

### Python Package Categories

| Category | Packages |
|----------|----------|
| **Web UI** | streamlit (Operator console) |
| **API** | fastapi, uvicorn (Sentinel server) |
| **LLM Integration** | openai (GPT API client) |
| **Cryptography** | pynacl (Ed25519 signatures) |
| **Data** | pandas, numpy (tables/analysis) |
| **Visualization** | plotly, matplotlib (charts) |
| **Configuration** | python-dotenv (env vars) |
| **Formatting** | rich (terminal colors) |
| **Vector DB** | pymilvus, grpcio (Milvus client) |
| **Utilities** | ujson (fast JSON), requests (HTTP) |

---

## 10. Testing Strategy

### Test Coverage
Located in `/verify/`:

1. **`test_directive_enforcement_core.py`** (13,913 bytes)
   - Tests hard governance signal enforcement
   - D3 (Contradiction), D2 (Ambiguity), D7/D11 (Precedence)
   - D13 (Sycophancy), D20-24 (Overconfidence)
   - Ledger signature verification

2. **`test_taes_adherence.py`** (8,214 bytes)
   - TAES scoring validation
   - Domain-specific weight matrices
   - IV/IRD threshold enforcement

3. **`conftest.py`** (11,868 bytes)
   - Pytest fixtures
   - Test-only shimming for missing modules
   - Deterministic TAES evaluation for testing

### Running Tests
```bash
pytest verify/ -q                    # Quick run
pytest verify/ -v                    # Verbose
pytest verify/ --cov=run_axp         # Coverage report
pytest verify/test_*.py::test_d3_* -v  # Specific test
```

### Test Philosophy
- **Deterministic:** Tests don't require OpenAI API calls
- **Self-contained:** Shimmed modules for offline testing
- **Governance-focused:** Emphasis on directive enforcement
- **No side effects:** Fixtures handle ledger isolation

---

## 11. Current State (v2.6)

### What's Working
- Multi-role reasoning chains with 5 agent personas
- Domain-specific role prompts (8 domains × 5 roles = 40 prompts)
- TAES evaluation with domain-adaptive weighting
- Hard governance enforcement (6 critical signals)
- Soft signal logging for audit trail
- Ed25519 ledger signing with HMAC fallback
- Sentinel auditor with independent verification
- Streamlit Operator Console with real-time metrics
- Docker deployment with Traefik TLS + rate limiting
- GitHub Actions CI/CD pipeline
- Allowlist-based user management
- Session logging and export functionality

### Known Limitations & To-Do
- **KMS/HSM for signing keys** - Currently in `~/.axp_keys/`, should move to managed service
- **Canary rollout capability** - No shadow traffic testing for model/prompt swaps
- **CORS & public API rate limits** - Waitlist API needs hardening
- **Merklized public anchoring** - Ledger roots not yet anchored onchain
- **Waitlist backend** - Vercel/FastAPI MongoDB integration planned
- **Analytics/dashboards** - Plausible or PostHog integration (future)

### Recent Improvements (v2.5 → v2.6)
| Area | Improvement |
|------|-------------|
| Governance | Hard-coded → JSON-configured (flexible, auditable) |
| Auditing | Hash-only → Ed25519 signatures + verification |
| UI | Basic metrics → Advanced governance panel + Sentinel score |
| DevOps | Manual → Automated (GH Actions, Traefik, smoke tests) |
| Config | Ad-hoc vars → Structured .env + config/ directory |
| Testing | Basic coverage → Comprehensive directive enforcement tests |

---

## 12. Getting Started as a Developer

### First 30 Minutes
```bash
1. Clone repo
   git clone https://github.com/axprotocol/axprotocol.git && cd AxProtocol

2. Install dependencies
   pip install -r requirements.txt

3. Configure environment
   cp .env.example .env
   # Edit .env: Add your OPENAI_API_KEY

4. Run local console
   streamlit run app_axp.py
   # Visit http://localhost:8501

5. Run tests
   pytest verify/ -q
   # Should see all tests pass
```

### First Week: Key Files to Understand
1. **`run_axp.py`** - How the chain orchestration works
2. **`taes_evaluation.py`** - Scoring algorithm
3. **`axp/governance/coupling.py`** - Enforcement logic
4. **`app_axp.py`** - UI and user-facing features
5. **`config/governance_coupling.json`** - Governance rules

### Key Concepts
- **Domain Detection** - Automatic classification of reasoning tasks
- **Multi-role chains** - 5-agent reasoning pipeline with inter-role Q&A
- **TAES scoring** - Measurable output quality (Logical/Practical/Probable)
- **Hard governance** - Strict enforcement caps/floors
- **Soft signals** - Audit trail without strict enforcement
- **Ledger signing** - Cryptographic immutability
- **Sentinel auditing** - Independent verification service

---

## 13. Common Tasks & Solutions

### Task: Add a new reasoning capability
1. Create new role prompt in `roles/domain/`
2. Update `load_roles.py` to load new role
3. Add to multi-agent chain in `run_axp.py`
4. Test with `streamlit run app_axp.py`

### Task: Adjust TAES weights for a domain
1. Edit `config/taes_weights.json`
2. Reload with `streamlit run app_axp.py`
3. Verify in UI "Advanced: TAES Metrics" tab
4. Test with `pytest verify/test_taes_adherence.py`

### Task: Tighten governance for a specific signal
1. Edit `config/governance_coupling.json` (adjust iv_max or ird_min)
2. Test with `python run_axp.py --smoke-governance`
3. Verify ledger writes with `cat logs/ledger/audit_ledger.jsonl | tail -1`
4. Run governance tests: `pytest verify/test_directive_enforcement_core.py -v`

### Task: Deploy to production
1. Ensure `.env` has production values (DOMAIN_APP, ACME_EMAIL, etc.)
2. Test locally: `docker-compose up -d && ./scripts/smoke.sh`
3. Git push to main branch (triggers GH Actions)
4. Monitor: `gh run watch`
5. Verify: `curl https://${DOMAIN_APP}` + `curl https://${DOMAIN_SENTINEL}/health`

---

## Summary

AxProtocol is a **sophisticated multi-agent reasoning system with cryptographic auditing and governance enforcement**. It combines:

- **Reasoning:** 5-agent pipeline with domain-adaptive prompts
- **Scoring:** TAES metrics with domain-specific weights
- **Governance:** Config-driven hard/soft signal enforcement
- **Auditing:** Ed25519-signed ledger + independent Sentinel verification
- **Operations:** Containerized deployment with Traefik + GitHub Actions

The codebase is **production-ready**, well-documented, and designed for continuous operation in high-stakes environments where reasoning transparency and auditability are critical.

---

*Last updated: November 5, 2025*
*AxProtocol v2.6 - Truth > Obedience. Signed. Sentineled. Config-driven.*
