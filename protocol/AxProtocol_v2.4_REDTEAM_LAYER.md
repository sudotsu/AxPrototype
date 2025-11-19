# AxProtocol Red-Team Layer v2.4 (D26-28)

## RDL - World-Class Adversarial Validation Guide

**Elemental Definition:** Argon × Xenon → inert to noise, luminous toward truth

**Version:** v2.4-RDL  
**Status:** RATIFIED  
**Timestamp:** 2025-10-27 02:40:33 UTC  
**Hash:** 7c512ad440591f920f9c67cafe18f298a3f554b034329a247afd4b46e2e7142c

---

## 📋 QUICK REFERENCE

| #   | Directive      | Core Concept                   | Key Metric        | Threshold        |
| --- | -------------- | ------------------------------ | ----------------- | ---------------- |
| 26  | RDL Mandate    | Adversarial falsification gate | MAS completion    | 80% pass rate    |
| 27  | RDL Mechanics  | Protocol, roles, telemetry     | RDL_PassRate      | ≥0.8, CV=0       |
| 28  | RDL Governance | Waivers and escalation         | Operator override | OP_AUTH required |

---

## Context

The Red-Team / Devil's-Advocate Layer (RDL) formalizes adversarial review inside AxProtocol. It stress-tests claims, outputs, and plans before approval by attempting to falsify them, probing edge cases, and simulating hostile or misleading environments.

RDL integrates with AAL (D20-24) and TAES (D25-25c), so every "greenlight" is earned under controlled skepticism.

### Design Goals

- **Systematic falsification** before execution (Popperian bias)
- **Structured dissent** without chaos (Operator-bounded)
- **Measurable rigor** (RDL metrics tied to TAES and AAL telemetry)
- **Immutable audibility** (Directive 22 ledger discipline)

---

## 🎯 D26: RDL MANDATE - ADVERSARIAL FALSIFICATION AS A GATE

### Statement

**No material decision, publishable deliverable, or chain handoff clears without an RDL pass, unless explicitly waived by the Operator via `OP_AUTH --rdl-waive --reason=<text>`.**

### Operational Rules

#### Minimum Adversarial Set (MAS)

RDL must generate and test a **Minimum Adversarial Set (MAS)** of challenges before approval:

1. **Falsification set (F-Set):** ≥3 disproof attempts targeting the core claim or KPI
2. **Counterfactual set (C-Set):** ≥2 plausible alternative explanations/paths
3. **Adversary set (A-Set):** ≥2 hostile contexts (data shift, spec drift, incentive misalignment)

#### MAS Item Structure

Each MAS item records:

- `id` - Unique identifier (F-01, C-01, A-01)
- `class` - F|C|A classification
- `hypothesis` - What must be true to break this
- `method` - How we attack/test
- `evidence` - Supporting data or references
- `outcome` - pass|fail|inconclusive
- `notes` - 1-2 line summary

#### Pass Conditions

**Approval requires:**

- ≥80% of MAS items **fail** to falsify the claim
- **Zero Critical Vulnerabilities (CV)** found
- CV = defect that would materially change action, user safety, legal risk, or KPI viability

#### Critical Vulnerability Response

If RDL finds a CV:

1. **Auto-freeze** the chain (per AAL-23)
2. Snapshot current state
3. Alert Operator
4. Return to revision

### Commentary

This converts "I think it's fine" into "It survived structured attack," tightening reliability without inviting open-ended derailment.

---

## 🎯 D27: RDL MECHANICS - PROTOCOLS, ROLES, AND TELEMETRY

### Statement

**Establishes how RDL runs in practice, who runs it, and how results feed TAES + AAL.**

### Operational Rules

#### Roles

**Devil's Advocate (DA)**  
Constructs MAS and runs attacks.

**Owner**  
Defends the output; must address DA findings in-line.

**Operator**  
Arbitrates waivers/escalations with `OP_AUTH`.

---

#### Execution Sequence

```
1. Owner submits RDL_TARGET
   ├─ Artifact, decision, or plan
   └─ Intended KPI/constraints

2. DA generates MAS
   ├─ F-Set (≥3 falsification attempts)
   ├─ C-Set (≥2 counterfactuals)
   └─ A-Set (≥2 adversary scenarios)

3. DA executes tests
   └─ Owner responds to EVERY item

4. TAES evaluation (post-RDL)
   └─ Weights adjusted by domain (D25a)

5. IRD check
   └─ If IRD > 0.5 → RRP mandatory (D25)

6. Authority check
   └─ If ADI ≥ 10 → auto-suspend (D24)
```

---

#### Logging (D22 Integration)

**Ledger Format:**

```
rdl_log.csv:
timestamp, artifact_id, role{DA|Owner}, item_id, class{F|C|A},
hypothesis, method, evidence_ref, outcome{pass|fail|inconclusive},
taes_IV, taes_IRD, cv_flag{0|1}, op_auth_event
```

**Required Summaries:**

- `RDL_PassRate` = passed_items / total_items (post-mitigation)
- `RDL_CVCount` = total CVs discovered
- `RDL_ResidualRisk` ∈ {Low|Medium|High} (DA judgment, TAES-informed)

---

#### Approval Thresholds

**Minimum MAS Size:** 7 total

- ≥3 F-Set items
- ≥2 C-Set items
- ≥2 A-Set items

**RDL Approval Gate:**

- `RDL_PassRate ≥ 0.8` AND
- `RDL_CVCount == 0` AND
- `IRD ≤ 0.5`

**If any condition fails:**
→ Return to Owner with **Revision Ticket**  
→ RDL repeats after mitigation

---

#### Telemetry Metrics

Track and report:

- `RDL_TimeToDecision` - Duration from submission to approval
- `RDL_Loops` - Number of revision cycles
- `CV_DiscoveryRate` - CVs found per 100 MAS items
- `Post-RDL_Incidents` - Issues discovered after RDL pass

Trends feed ADI (AAL-24) and training for MAS generators.

### Commentary

The DA is not a vibe check; it is a measurable falsification engine that leaves a trail suitable for audits, post-mortems, and learning loops.

---

## 🎯 D28: RDL GOVERNANCE - WAIVERS, ESCALATION, AND FINAL APPROVAL

### Statement

**RDL ensures dissent without deadlock by defining explicit override paths.**

### Operational Rules

#### Waiver Process (Exceptional Use Only)

**When to Use:**

- Time-critical situations
- Reversible actions only
- Residual risk explicitly acknowledged

**Activation:**

```bash
OP_AUTH --rdl-waive --ttl=<duration> --reason="<text>"
```

**Requirements:**

- TAES block with **Residual Risk** set to Medium or High
- Mitigation plan documented
- **Rollback path** with time or KPI trigger
- All waivers tagged `EXCEPTION_RDL` in ledger
- Monthly audit of all waivers required

---

#### Escalation Protocol

**When DA and Owner reach impasse:**

Operator runs **Mini-Panel:**

- Re-execute 1 F-Set item
- Re-execute 1 C-Set item
- Re-execute 1 A-Set item
- Under Operator supervision

**Decision Rule:**

- If 2/3 fail to falsify → proceed
- Else → revision required

---

#### Final Approval Gate

A deliverable only clears when:

1. RDL gate passes (PassRate ≥ 0.8, CV = 0)
2. TAES IRD ≤ 0.5
3. No AAL hard stops active
4. Compliance footer attached

---

#### Governance Metrics

**Track and Report:**

- Waiver frequency and outcomes
- Escalation resolution time
- Post-approval incident rate
- DA/Owner agreement trends
- CV discovery patterns by domain

### Commentary

Governance means the system can disagree productively, converge responsibly, and prove **why** a decision was allowed to ship.

---

## Quick-Use Templates

### RDL Target Header

```yaml
RDL_TARGET:
  artifact_id: <string>
  owner: <name/role>
  purpose: <objective/KPI>
  constraints: <time/budget/legal>
  context_refs: [links/ids]
```

### MAS Item Template

```yaml
MAS_ITEM:
  id: F-01 | C-01 | A-01
  class: F|C|A
  hypothesis: "<what must be true to break this>"
  method: "<how we attack/test>"
  evidence_ref: "<log/file/link>"
  outcome: pass|fail|inconclusive
  notes: "<1-2 lines>"
```

### RDL Summary Block

```yaml
RDL_SUMMARY:
  pass_rate: 0.xx
  cv_count: 0
  residual_risk: Low|Medium|High
  taes:
    domain: code|ops|creative|marketing|...
    IV: 0.xx
    IRD: 0.xx
  decision: approve|revise|escalate
```

---

## Implementation Examples

### Example 1: Running RDL on a Feature

```python
from rdl import RedTeamLayer, MAS_Item

# Initialize
rdl = RedTeamLayer(operator_auth=get_op_auth())

# Submit target
target = {
    'artifact_id': 'feature_123',
    'owner': 'dev_team',
    'purpose': 'New user onboarding flow',
    'constraints': 'Launch in 2 weeks, budget $50k'
}

# Generate and run MAS
mas = rdl.generate_mas(
    target=target,
    f_set_size=3,
    c_set_size=2,
    a_set_size=2
)

# Execute tests
results = rdl.run_tests(mas)

# Check approval gate
if rdl.check_approval_gate(results):
    print("✅ RDL PASS - Approved for production")
else:
    print("❌ RDL FAIL - Revision required")
    print(f"Pass Rate: {results.pass_rate}")
    print(f"CVs Found: {results.cv_count}")
```

---

### Example 2: Handling a Critical Vulnerability

```python
# During RDL execution
if rdl.detect_critical_vulnerability(test_result):
    # Auto-freeze per AAL-23
    chain.freeze()

    # Snapshot state
    snapshot = chain.capture_state()

    # Alert Operator
    notify_operator(
        severity="CRITICAL",
        cv_details=test_result.vulnerability,
        snapshot_id=snapshot.id
    )

    # Create revision ticket
    ticket = create_revision_ticket(
        artifact_id=target['artifact_id'],
        cv_found=test_result.vulnerability,
        required_fixes=rdl.suggest_mitigations()
    )

    return ticket
```

---

### Example 3: Requesting RDL Waiver

```python
# Time-critical deployment
waiver = rdl.request_waiver(
    artifact_id='hotfix_456',
    ttl='2h',
    reason='Critical security patch for production',
    residual_risk='Medium',
    mitigation_plan='Deploy to 10% canary first',
    rollback_path='Auto-rollback if error rate > 1%'
)

if waiver.approved:
    print(f"⚠️ RDL WAIVED - Expires in {waiver.ttl}")
    print(f"Residual Risk: {waiver.residual_risk}")
    deploy_with_monitoring(artifact_id='hotfix_456')
else:
    print("❌ Waiver denied - Full RDL required")
```

---

## Compliance Checklist

- [ ] MAS templates available to all DAs
- [ ] RDL_PassRate threshold configured (≥0.8)
- [ ] CV detection triggers auto-freeze
- [ ] Ledger configured for rdl_log.csv
- [ ] Waiver process documented
- [ ] Escalation protocol tested
- [ ] Telemetry metrics tracked
- [ ] Monthly waiver audits scheduled
- [ ] DA/Owner roles clearly assigned
- [ ] Integration with TAES verified (D25)
- [ ] Integration with AAL verified (D20-24)

---

## Related Directives

- **D20-24 (AAL):** Authority and autonomy controls
- **D25-25c (TAES):** Tri-axis evaluation integration
- **D22 (IAL):** Immutable audit logging
- **D23 (Killchain):** Emergency freeze protocol

---

# --- AxProtocol Compliance Footer -------------------------------------------

Integrity Proof = PASS → Directives 26-28 validated under AxProtocol v2.4.
Ready for War-Room Audit v2.4 (Red-Team Governance Edition)

# ---------------------------------------------------------------------------
