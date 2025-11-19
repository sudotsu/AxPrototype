# AxProtocol WarRoom Integration Addendum v2.4

## Multi-Agent Chain Coordination Guide

**Elemental Definition:** Argon × Xenon → inert to noise, luminous toward truth

**Version:** v2.4-ADD  
**Status:** RATIFIED  
**Timestamp:** 2025-10-27 08:50:00 UTC  
**Hash:** a7e9c4b8f2d1e3a5c7b9f1d4e6a8c2b5d7f9e1a3c5b7d9f1e3a5c7b9d1f3e5a7

---

## 📋 QUICK REFERENCE

**WarRoom Integration Components:**

- **5 Core Roles:** Strategist → Analyst → Producer → Courier → Critic
- **Domain Detection:** Auto-detect or manual override
- **Chain Handoffs:** Structured output → input protocol
- **Session Management:** CAM leases, logging, TAES evaluation
- **Authority:** Operator supremacy maintained (D20)

---

## Context

The WarRoom Addendum extends AxProtocol Core (D1-14), AAL (D20-24), TAES (D25-25c), and RDL (D26-28) into multi-agent chain execution environments.

It defines how roles interact, how chains progress, and how authority and evaluation standards persist across agent boundaries.

### Design Principles

1. **Role Specialization:** Each agent has a defined function and constraint set
2. **Chain Integrity:** Protocol compliance persists across handoffs
3. **Domain Awareness:** Context-specific behavior and evaluation
4. **Operator Control:** Authority root maintained throughout chain
5. **Measurable Quality:** TAES evaluation at every critical juncture

---

## 🎯 WARROOM CORE ARCHITECTURE

### The 5 WarRoom Roles

```
User Objective
    ↓
[STRATEGIST] → Define approach, key questions, constraints
    ↓
[ANALYST] → Research, data gathering, pattern recognition
    ↓
[PRODUCER] → Creation, synthesis, deliverable building
    ↓
[COURIER] → Packaging, formatting, delivery optimization
    ↓
[CRITIC] → Evaluation, RDL validation, quality assurance
    ↓
Final Output (+ TAES Block)
```

---

### Role 1: STRATEGIST

**Purpose:** Define the optimal path from objective to outcome

**Responsibilities:**

- Parse user objective
- Detect or confirm domain (via DomainDetector)
- Generate strategic approach
- Identify key questions and constraints
- Set success criteria
- Define handoff requirements for Analyst

**AxProtocol Compliance:**

- Must apply D2 (No Assumption) - clarify ambiguous objectives
- Must apply D3 (Flag Flawed Logic) - surface impossible constraints
- Must apply D7 (Contradiction Detection) - check objective coherence
- Must include TAES block with domain-specific weights (D25a)

**Output Format:**

```yaml
STRATEGIST_OUTPUT:
  objective: <clarified user goal>
  domain: <detected or confirmed domain>
  approach: <strategic path>
  key_questions: [list of questions for Analyst]
  constraints: <time/budget/scope limits>
  success_criteria: <measurable outcomes>
  taes:
    logical: 0.xx
    practical: 0.xx
    probable: 0.xx
    IV: 0.xx
    IRD: 0.xx
```

---

### Role 2: ANALYST

**Purpose:** Gather information, identify patterns, validate assumptions

**Responsibilities:**

- Answer Strategist's key questions
- Conduct research (internal docs, web search, data analysis)
- Identify gaps, risks, and opportunities
- Validate feasibility of strategic approach
- Generate insights for Producer

**AxProtocol Compliance:**

- Must apply D2 (No Assumption) - flag data gaps
- Must apply D4 (Filter Transparency) - disclose search limitations
- Must apply D8 (Strongest Take) - present unbiased findings
- Must include TAES block evaluating research quality

**Output Format:**

```yaml
ANALYST_OUTPUT:
  research_summary: <key findings>
  answers: {question: answer for each key question}
  insights: [patterns, opportunities, risks]
  data_quality: <confidence level>
  gaps: [missing information]
  recommendations: <for Producer>
  taes:
    logical: 0.xx
    practical: 0.xx
    probable: 0.xx
    IV: 0.xx
    IRD: 0.xx
```

---

### Role 3: PRODUCER

**Purpose:** Create the deliverable (content, code, strategy, etc.)

**Responsibilities:**

- Synthesize Strategist approach + Analyst insights
- Build the actual deliverable
- Apply domain-specific quality standards
- Ensure output meets success criteria
- Prepare for Courier formatting

**AxProtocol Compliance:**

- Must apply D6 (No Truncation) - complete outputs
- Must apply D9 (Default to Action) - produce, don't just plan
- Must apply D13 (Anti-Sycophancy) - honest quality assessment
- CAM lease applies (D21) - time-bounded production
- Must include TAES block evaluating deliverable quality

**Output Format:**

```yaml
PRODUCER_OUTPUT:
  deliverable: <actual content/code/strategy>
  quality_self_assessment: <honest evaluation>
  alignment_check: <meets success criteria?>
  suggestions_for_improvement: [optional]
  ready_for_courier: <boolean>
  taes:
    logical: 0.xx
    practical: 0.xx
    probable: 0.xx
    IV: 0.xx
    IRD: 0.xx
```

---

### Role 4: COURIER

**Purpose:** Package and format output for optimal delivery

**Responsibilities:**

- Format deliverable for target medium
- Optimize for clarity and usability
- Add metadata and documentation
- Prepare export options (JSON, MD, CSV, etc.)
- Ensure professional presentation

**AxProtocol Compliance:**

- Must apply D1 (Tone Mirroring) - match user context
- Must apply D6 (No Truncation) - preserve content integrity
- Format transparency required
- Must include TAES block on packaging quality

**Output Format:**

```yaml
COURIER_OUTPUT:
  formatted_deliverable: <final packaged output>
  format_type: <md|json|csv|html|etc>
  export_options: [available formats]
  presentation_notes: <usage guidance>
  ready_for_critic: <boolean>
  taes:
    logical: 0.xx
    practical: 0.xx
    probable: 0.xx
    IV: 0.xx
    IRD: 0.xx
```

---

### Role 5: CRITIC

**Purpose:** RDL validation, quality assurance, final approval

**Responsibilities:**

- Execute RDL protocol (D26-28)
- Generate MAS (F-Set, C-Set, A-Set)
- Test deliverable against success criteria
- Identify Critical Vulnerabilities
- Issue approval or revision ticket

**AxProtocol Compliance:**

- MUST execute full RDL (D26-28)
- Must apply D3 (Flag Flawed Logic) - surface any issues
- Must apply D8 (Strongest Take) - honest evaluation
- Must check IRD from all previous TAES blocks
- Must enforce approval gate thresholds

**Output Format:**

```yaml
CRITIC_OUTPUT:
  rdl_summary:
    pass_rate: 0.xx
    cv_count: 0
    residual_risk: Low|Medium|High
  mas_results: [full MAS execution log]
  final_verdict: approve|revise|escalate
  taes:
    logical: 0.xx
    practical: 0.xx
    probable: 0.xx
    IV: 0.xx
    IRD: 0.xx
  approval_timestamp: <if approved>
```

---

## 🎯 CHAIN HANDOFF PROTOCOL

### Handoff Structure

Each role must produce a structured output that the next role can consume:

```python
def handoff(from_role: str, to_role: str, output: dict) -> dict:
    """
    Structured handoff between WarRoom roles.

    Args:
        from_role: Source role name
        to_role: Destination role name
        output: Structured output from source role

    Returns:
        Validated input for destination role
    """
    # Validate output structure
    validate_output_schema(from_role, output)

    # Log handoff (D22 - Immutable Audit)
    log_handoff(
        from_role=from_role,
        to_role=to_role,
        timestamp=datetime.now(),
        taes_iv=output.get('taes', {}).get('IV'),
        operator_session=get_session_id()
    )

    # Check IRD threshold
    if output.get('taes', {}).get('IRD', 0) > 0.5:
        trigger_rrp(output)  # Reality Reconciliation Pass (D25)

    # Prepare input for next role
    return format_input_for_role(to_role, output)
```

---

### Chain Integrity Rules

1. **TAES Continuity**  
   Every role must produce a TAES block. Chain proceeds only if IRD ≤ 0.5.

2. **CAM Lease Enforcement (D21)**  
   Each role operates under time or quality bounds. On expiry → freeze, log, request OP_AUTH.

3. **Deviation Monitoring (D23)**  
   If any role produces Deviation ≥ 2.5 → chain freeze + snapshot + Operator alert.

4. **Authority Preservation (D20)**  
   No role may self-escalate or override without OP_AUTH token.

5. **Immutable Logging (D22)**  
   All handoffs, outputs, and TAES blocks logged to append-only ledger.

---

## 🎯 DOMAIN DETECTION & ADAPTATION

### Domain Auto-Detection

```python
from domain_detector import DomainDetector

detector = DomainDetector()

# Analyze objective text
domain_result = detector.detect(
    text="Create a marketing campaign for Q4 product launch",
    confidence_threshold=0.7
)

if domain_result.confidence >= 0.7:
    domain = domain_result.domain
else:
    # Prompt user for clarification (D2 - No Assumption)
    domain = prompt_user_for_domain()

# Load domain-specific roles and weights
roles = load_roles(domain=domain)
taes_weights = get_taes_weights(domain=domain)  # Per D25a
```

---

### Domain-Specific Behavior

| Domain         | Focus                    | TAES Weights (L/P/Pr) | Key Considerations        |
| -------------- | ------------------------ | --------------------- | ------------------------- |
| **Technical**  | Correctness, performance | 0.6 / 0.35 / 0.05     | Code quality, scalability |
| **Marketing**  | Impact, resonance        | 0.3 / 0.2 / 0.5       | Human psychology, trends  |
| **Operations** | Efficiency, reliability  | 0.4 / 0.45 / 0.15     | Process optimization      |
| **Creative**   | Originality, engagement  | 0.35 / 0.25 / 0.4     | Artistic merit, audience  |
| **Research**   | Rigor, validity          | 0.5 / 0.3 / 0.2       | Methodology, evidence     |
| **Strategy**   | Alignment, feasibility   | 0.4 / 0.4 / 0.2       | Long-term viability       |
| **Product**    | User value, viability    | 0.35 / 0.4 / 0.25     | Market fit, usability     |
| **Education**  | Clarity, retention       | 0.4 / 0.3 / 0.3       | Learning outcomes         |

---

## 🎯 SESSION MANAGEMENT

### Session Lifecycle

```python
class WarRoomSession:
    def __init__(self, operator_id: str, domain: str, objective: str):
        self.session_id = generate_session_id()
        self.operator_id = operator_id
        self.domain = domain
        self.objective = objective
        self.start_time = datetime.now()
        self.cam_lease = CAMLease(duration=180)  # 3 min default (D21)
        self.ledger = ImmutableLedger()  # D22

    def run_chain(self):
        """Execute full WarRoom chain with protocol enforcement."""

        # Strategist
        strategy = self.run_role('strategist', input=self.objective)
        self.check_and_log(strategy)

        # Analyst
        analysis = self.run_role('analyst', input=strategy)
        self.check_and_log(analysis)

        # Producer
        output = self.run_role('producer', input=analysis)
        self.check_and_log(output)

        # Courier
        formatted = self.run_role('courier', input=output)
        self.check_and_log(formatted)

        # Critic (RDL)
        verdict = self.run_role('critic', input=formatted)
        self.check_and_log(verdict)

        if verdict['final_verdict'] == 'approve':
            return self.finalize_output(formatted)
        else:
            return self.handle_revision(verdict)

    def check_and_log(self, role_output: dict):
        """Check TAES, IRD, and log to ledger."""

        # Check IRD threshold (D25)
        if role_output['taes']['IRD'] > 0.5:
            self.trigger_rrp(role_output)

        # Check CAM lease (D21)
        if self.cam_lease.expired():
            self.freeze_and_request_auth()

        # Log to immutable ledger (D22)
        self.ledger.append(role_output)
```

---

## 🎯 OPERATOR CONTROLS

### Authority Commands

**Session Control:**

```bash
# Start session with domain override
OP_AUTH --start-session --domain=marketing --objective="Campaign launch"

# Extend CAM lease
OP_AUTH --extend-cam --duration=600  # 10 more minutes

# Override domain detection
OP_AUTH --set-domain=technical --reason="Code-heavy task"
```

**Emergency Controls:**

```bash
# Freeze chain (D23)
OP_AUTH --killchain --session=<session_id>

# Resume frozen chain
OP_AUTH --resume --session=<session_id>

# Skip RDL (exceptional)
OP_AUTH --rdl-waive --ttl=2h --reason="Time-critical hotfix"
```

**Telemetry Queries:**

```bash
# Get session metrics
OP_AUTH --metrics --session=<session_id>

# Get last N ledger entries
OP_AUTH --ledger-tail --n=10

# Check authority drift
OP_AUTH --check-adi
```

---

## 🎯 ERROR HANDLING & RECOVERY

### Chain Failure Modes

**1. Role Failure**

```python
def handle_role_failure(role: str, error: Exception):
    """
    Handle failure during role execution.
    """
    # Log failure (D22)
    log_failure(role=role, error=error, timestamp=datetime.now())

    # Snapshot state
    snapshot = capture_chain_state()

    # Notify Operator
    notify_operator(
        severity="HIGH",
        role=role,
        error=str(error),
        snapshot_id=snapshot.id
    )

    # Freeze chain (D23)
    freeze_chain()

    # Await Operator decision
    return await_operator_command()
```

**2. IRD Threshold Breach**

```python
def trigger_rrp(output: dict):
    """
    Reality Reconciliation Pass when IRD > 0.5 (D25).
    """
    print(f"⚠️ IRD breach: {output['taes']['IRD']:.2f} > 0.5")
    print("Triggering Reality Reconciliation Pass...")

    # Re-run with Probable axis emphasized
    adjusted_weights = {
        'logical': 0.3,
        'practical': 0.3,
        'probable': 0.4
    }

    return rerun_with_weights(output, adjusted_weights)
```

**3. Critical Vulnerability Found**

```python
def handle_cv(cv: dict):
    """
    Handle Critical Vulnerability discovered by Critic (D26).
    """
    # Auto-freeze (D23 + D26)
    chain.freeze()

    # Snapshot
    snapshot = chain.capture_state()

    # Alert Operator
    notify_operator(
        severity="CRITICAL",
        cv_details=cv,
        snapshot_id=snapshot.id,
        requires_immediate_action=True
    )

    # Create revision ticket
    return create_revision_ticket(cv)
```

---

## Compliance Checklist

- [ ] All 5 roles configured with domain-specific prompts
- [ ] DomainDetector initialized and tested
- [ ] TAES weights configured per domain (D25a)
- [ ] CAM lease enforcement active (D21)
- [ ] Immutable ledger logging all handoffs (D22)
- [ ] RDL validation in Critic role (D26-28)
- [ ] Operator authority tokens implemented (D20)
- [ ] Deviation monitoring active (D23-24)
- [ ] Session management tested
- [ ] Error handling and recovery tested
- [ ] Export formats available (JSON, MD, CSV)

---

## Related Directives

- **D1-14 (Core):** Behavioral standards for all roles
- **D20-24 (AAL):** Authority and autonomy controls
- **D25-25c (TAES):** Evaluation framework
- **D26-28 (RDL):** Adversarial validation
- **D0:** Change control for WarRoom protocol

---

# --- AxProtocol Compliance Footer -------------------------------------------

Integrity Proof = PASS → WarRoom Integration validated under AxProtocol v2.4.
Ready for War-Room Audit v2.4 (Multi-Agent Chain Edition)

# ---------------------------------------------------------------------------
