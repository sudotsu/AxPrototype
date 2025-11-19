# Config Hash Implementation ✅

## Summary

Successfully implemented `config_hash` in ledger entries for immutable proof that protocol config hasn't drifted.

## Implementation Details

### 1. Config Fingerprint Utility (`axp/utils/config_fingerprint.py`)

**Created:**
- `compute_config_hash(base_dir)` - Computes SHA256 hash of all protocol config files
- `get_config_files_list(base_dir)` - Returns list of files included in fingerprint

**Files Included:**
- `config/governance_coupling.json` - Hard/soft signal definitions
- `config/role_shapes.json` - Role boundary enforcement
- `config/taes_weights.json` - Domain-specific TAES weights
- `protocol/AxProtocol_v2.4_D0_CHANGE_CONTROL.md` - Directive D0
- `protocol/AxProtocol_v2.4_CORE_DIRECTIVES.md` - Directives D1-14
- `protocol/AxProtocol_v2.4_WARROOM_ADDENDUM.md` - Directives D15-19
- `protocol/AxProtocol_v2.4_AUTHORITY_LAYER.md` - Directives D20-24
- `protocol/AxProtocol_v2.4_TAES_EVALUATION.md` - Directives D25-25c
- `protocol/AxProtocol_v2.4_REDTEAM_LAYER.md` - Directives D26-28

**Features:**
- ✅ Sorts files alphabetically for consistent hashing
- ✅ Normalizes JSON files (sort_keys=True) for deterministic hashing
- ✅ Handles missing files gracefully (includes "[MISSING: filename]")
- ✅ Returns prefixed hash: `sha256:<hex>`

### 2. SQLite Ledger (`ledger.py`)

**Changes:**
- Added `config_hash TEXT` column to `audit_log` table
- Added migration to add column for existing databases
- Updated `log_execution()` to accept optional `config_hash` parameter
- Updated `get_last_n_entries()` to include `config_hash` in results

**Backward Compatibility:**
- ✅ `config_hash` is optional (defaults to `None`)
- ✅ Existing entries have `config_hash = None` (acceptable)
- ✅ Migration handles existing databases gracefully

### 3. JSONL Ledger (`axp/governance/ledger.py`)

**Changes:**
- Updated `write_ledger_entry()` to accept optional `config_hash` parameter
- Adds `config_hash` to entry dict if provided
- Included in signed payload for cryptographic verification

### 4. Chain Integration (`axp/orchestration/chain.py`)

**Changes:**
- Computes `config_hash` once at session start
- Passes `config_hash` to all `log_execution()` calls
- Passes `config_hash` to all `evaluate_taes()` calls
- Prints config hash prefix for visibility: `[AxProtocol] Config hash: sha256:29de65ae94973957a7fc324...`

### 5. TAES Integration (`taes_evaluation.py`)

**Changes:**
- Updated `evaluate_taes()` to accept optional `config_hash` parameter
- Updated `evaluate_taes_async()` to accept optional `config_hash` parameter
- Passes `config_hash` to `write_ledger_entry()` calls

**Backward Compatibility:**
- ✅ `config_hash` is optional (defaults to `None`)
- ✅ Existing code that doesn't pass `config_hash` still works

### 6. Tests (`verify/test_config_hash.py`)

**Created comprehensive test suite:**
- `test_config_hash_computation()` - Verify hash can be computed
- `test_config_hash_includes_all_files()` - Verify all files included
- `test_config_hash_changes_on_file_modification()` - Verify drift detection
- `test_config_hash_handles_missing_files()` - Verify graceful handling
- `test_ledger_entry_includes_config_hash()` - Verify SQLite storage
- `test_ledger_entry_config_hash_optional()` - Verify backward compatibility
- `test_governance_ledger_includes_config_hash()` - Verify JSONL storage
- `test_config_hash_drift_detection()` - Verify drift detection capability

## Usage

### Computing Config Hash

```python
from axp.utils.config_fingerprint import compute_config_hash
from pathlib import Path

base_dir = Path(__file__).parent
config_hash = compute_config_hash(base_dir)
# Returns: "sha256:29de65ae94973957a7fc324..."
```

### Using in Ledger Entries

```python
from ledger import log_execution
from axp.utils.config_fingerprint import compute_config_hash

config_hash = compute_config_hash(Path("."))

log_execution(
    session_id="session-001",
    agent_id="strategist-01",
    role_name="Strategist",
    action="generate_strategy",
    output_text="...",
    config_hash=config_hash  # ← Include config hash
)
```

### Drift Detection

```python
# Session A (earlier)
entry_a = get_last_n_entries(1)[0]
hash_a = entry_a["config_hash"]

# Session B (later)
hash_b = compute_config_hash(Path("."))

# Detect drift
if hash_a != hash_b:
    print(f"⚠️ Config drift detected!")
    print(f"  Session A: {hash_a[:20]}...")
    print(f"  Session B: {hash_b[:20]}...")
```

## Benefits

1. ✅ **Audit Trail**: Every ledger entry records exact config state
2. ✅ **Drift Detection**: Can detect config changes between sessions
3. ✅ **Reproducibility**: Can verify exact config used for any execution
4. ✅ **Security**: Detects unauthorized config modifications
5. ✅ **Debugging**: Correlate issues with config changes
6. ✅ **Compliance**: Aligns with Directive 22 (immutable ledger)

## Testing

Run tests:
```bash
pytest verify/test_config_hash.py -v
```

Verify hash computation:
```bash
python -c "from axp.utils.config_fingerprint import compute_config_hash; from pathlib import Path; print(compute_config_hash(Path('.')))"
```

## Migration Notes

- **Existing databases**: Migration automatically adds `config_hash` column
- **Existing entries**: Will have `config_hash = None` (acceptable)
- **New entries**: Will include `config_hash` if provided
- **Backward compatibility**: All changes are optional parameters

## Files Changed

1. ✅ `axp/utils/config_fingerprint.py` (NEW)
2. ✅ `axp/utils/__init__.py` - Added exports
3. ✅ `ledger.py` - Added column and parameter
4. ✅ `axp/governance/ledger.py` - Added to entry dict
5. ✅ `axp/orchestration/chain.py` - Compute and pass hash
6. ✅ `taes_evaluation.py` - Accept and pass hash
7. ✅ `verify/test_config_hash.py` (NEW)

## Next Steps (Optional)

1. **Add Sentinel verification**: Verify config_hash consistency across sessions
2. **Add UI display**: Show config_hash in `app_axp.py` session history
3. **Add CLI tool**: `python -m axp.utils.config_fingerprint` to print current hash
4. **Add drift alerts**: Warn if config_hash changes between sessions

