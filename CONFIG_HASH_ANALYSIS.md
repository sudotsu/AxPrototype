# Config Hash Implementation Analysis

## Does It Make Sense? ✅ **YES**

**Goal**: Immutable proof that protocol config (directives, weights, shapes) hasn't drifted.

**Why This Matters:**
1. **Audit Trail**: Verify exact config state at time of execution
2. **Drift Detection**: Detect accidental or malicious config changes
3. **Reproducibility**: Recreate exact execution conditions
4. **Security**: Detect unauthorized modifications
5. **Debugging**: Correlate issues with config changes

## Is It Beneficial? ✅ **YES - Highly Beneficial**

### Benefits:
- ✅ **Compliance**: Aligns with Directive 22 (immutable ledger)
- ✅ **Forensics**: Can prove config state for any historical execution
- ✅ **CI/CD**: Can detect config drift in deployments
- ✅ **Debugging**: "Why did this session behave differently?" → Check config_hash
- ✅ **Security**: Detects tampering with governance config

## Implementation Considerations

### 1. Which Config Files to Include?

**Core Governance Config (MUST):**
- ✅ `config/governance_coupling.json` - Hard/soft signal definitions
- ✅ `config/role_shapes.json` - Role boundary enforcement
- ✅ `config/taes_weights.json` - Domain-specific TAES weights

**Protocol Directives (SHOULD):**
- ✅ `protocol/AxProtocol_v2.4_D0_CHANGE_CONTROL.md`
- ✅ `protocol/AxProtocol_v2.4_CORE_DIRECTIVES.md`
- ✅ `protocol/AxProtocol_v2.4_WARROOM_ADDENDUM.md`
- ✅ `protocol/AxProtocol_v2.4_AUTHORITY_LAYER.md`
- ✅ `protocol/AxProtocol_v2.4_TAES_EVALUATION.md`
- ✅ `protocol/AxProtocol_v2.4_REDTEAM_LAYER.md`

**Optional (MAYBE):**
- ⚠️ `DomainConfig.json` - Affects domain detection, but changes frequently
- ⚠️ `config/auth_settings.yaml` - Security config, but may contain secrets

**Recommendation**: Include directives + core governance config. Exclude DomainConfig (too dynamic) and auth_settings (may contain secrets).

### 2. Hash Computation Strategy

**Option A: Per-Session (RECOMMENDED)**
- Compute once at session start
- Store in session context
- All entries in session share same config_hash
- **Pros**: Efficient, consistent
- **Cons**: If config changes mid-session, won't detect it

**Option B: Per-Entry**
- Compute hash for each ledger entry
- **Pros**: Detects mid-session changes
- **Cons**: Expensive, redundant

**Recommendation**: **Per-Session** - Config shouldn't change mid-session anyway.

### 3. Which Ledger System?

**Current State:**
- `ledger.py` (root) - SQLite, used by `log_execution()` in chain execution
- `axp/governance/ledger.py` - JSONL with Ed25519, used by TAES

**Recommendation**: Add to **BOTH**:
1. `ledger.py` - Add `config_hash` column to SQLite table
2. `axp/governance/ledger.py` - Add `config_hash` to entry dict

### 4. Missing Files Handling

**Strategy**: Include file path + content hash in fingerprint
- If file missing: hash empty string or "[MISSING: filename]"
- Ensures hash changes if file is added/removed
- Prevents silent failures

## Recommended Implementation

### Phase 1: Create Config Fingerprint Utility

```python
# axp/utils/config_fingerprint.py
def compute_config_hash(base_dir: Path) -> str:
    """
    Compute SHA256 hash of all protocol config files.

    Includes:
    - Governance coupling
    - Role shapes
    - TAES weights
    - All directive markdown files

    Returns:
        SHA256 hash as hex string (prefixed with "sha256:")
    """
```

### Phase 2: Update Ledger Systems

**For `ledger.py` (SQLite):**
- Add `config_hash TEXT` column
- Update `log_execution()` to accept `config_hash` parameter
- Compute hash at session start, pass to all entries

**For `axp/governance/ledger.py` (JSONL):**
- Add `config_hash` to entry dict
- Update `write_ledger_entry()` to accept `config_hash` parameter

### Phase 3: Integration

- Compute hash once in `run_chain()` at session start
- Pass to all `log_execution()` calls
- Store in session results for verification

## Potential Issues & Solutions

### Issue 1: Config Changes Mid-Session
**Solution**: Compute hash at session start, document that config shouldn't change mid-session

### Issue 2: Missing Files
**Solution**: Include "[MISSING: filename]" in hash, ensures hash changes when file added

### Issue 3: File Ordering
**Solution**: Sort file paths alphabetically before hashing

### Issue 4: Performance
**Solution**: Cache hash per session (already computing once)

## Testing Strategy

1. **Unit Test**: `test_config_hash_computation()` - Verify hash changes when config changes
2. **Integration Test**: `test_ledger_config_hash()` - Verify hash stored in entries
3. **Drift Test**: `test_config_drift_detection()` - Verify hash mismatch detection

## Conclusion

**Verdict**: ✅ **Implement This**

This is a **high-value, low-risk** improvement that:
- Strengthens auditability
- Enables drift detection
- Improves debugging
- Aligns with AxProtocol's immutable ledger principle

**Priority**: **High** - Should be implemented before production deployment.

