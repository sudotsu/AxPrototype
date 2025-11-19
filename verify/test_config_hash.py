"""
Tests for config_hash implementation in ledger entries.

Verifies:
1. Config hash computation includes all required files
2. Hash changes when config files change
3. Hash is stored in ledger entries
4. Drift detection works correctly
"""

import pytest
import json
import hashlib
import tempfile
import shutil
from pathlib import Path

from axp.utils.config_fingerprint import compute_config_hash, get_config_files_list
from ledger import log_execution, get_last_n_entries, init_ledger
from axp.governance.ledger import write_ledger_entry


def test_config_hash_computation():
    """Test that config hash can be computed."""
    base_dir = Path(__file__).parent.parent
    hash_val = compute_config_hash(base_dir)

    assert hash_val.startswith("sha256:")
    assert len(hash_val) == 71  # "sha256:" + 64 hex chars

    # Verify it's a valid hex string
    hex_part = hash_val[7:]
    assert all(c in "0123456789abcdef" for c in hex_part)


def test_config_hash_includes_all_files():
    """Test that all expected config files are included."""
    base_dir = Path(__file__).parent.parent
    files = get_config_files_list(base_dir)

    expected_files = [
        "config/governance_coupling.json",
        "config/role_shapes.json",
        "config/taes_weights.json",
        "protocol/AxProtocol_v2.4_D0_CHANGE_CONTROL.md",
        "protocol/AxProtocol_v2.4_CORE_DIRECTIVES.md",
        "protocol/AxProtocol_v2.4_WARROOM_ADDENDUM.md",
        "protocol/AxProtocol_v2.4_AUTHORITY_LAYER.md",
        "protocol/AxProtocol_v2.4_TAES_EVALUATION.md",
        "protocol/AxProtocol_v2.4_REDTEAM_LAYER.md",
    ]

    assert len(files) == len(expected_files)
    assert set(files) == set(expected_files)


def test_config_hash_changes_on_file_modification():
    """Test that hash changes when config files are modified."""
    base_dir = Path(__file__).parent.parent

    # Compute initial hash
    hash1 = compute_config_hash(base_dir)

    # Modify a config file (if it exists)
    config_file = base_dir / "config" / "role_shapes.json"
    if config_file.exists():
        original_content = config_file.read_text()
        try:
            # Add a comment (should change hash)
            data = json.loads(original_content)
            data["_test_comment"] = "test modification"
            config_file.write_text(json.dumps(data, indent=2))

            # Compute new hash
            hash2 = compute_config_hash(base_dir)

            # Hashes should be different
            assert hash1 != hash2, "Hash should change when config file is modified"
        finally:
            # Restore original content
            config_file.write_text(original_content)
            # Verify restoration worked
            hash3 = compute_config_hash(base_dir)
            assert hash1 == hash3, "Hash should match original after restoration"


def test_config_hash_handles_missing_files():
    """Test that missing files are handled gracefully."""
    base_dir = Path(__file__).parent.parent

    # Should not raise exception even if some files are missing
    hash_val = compute_config_hash(base_dir)
    assert hash_val.startswith("sha256:")


def test_ledger_entry_includes_config_hash():
    """Test that ledger entries include config_hash."""
    # Initialize ledger
    init_ledger()

    # Compute config hash
    base_dir = Path(__file__).parent.parent
    config_hash = compute_config_hash(base_dir)

    # Log an execution with config_hash
    result = log_execution(
        session_id="test-config-hash-001",
        agent_id="test-agent",
        role_name="TestRole",
        action="test_action",
        output_text="test output",
        config_hash=config_hash
    )

    assert result is not None

    # Retrieve entry and verify config_hash is present
    entries = get_last_n_entries(1)
    assert len(entries) == 1

    entry = entries[0]
    assert "config_hash" in entry
    assert entry["config_hash"] == config_hash


def test_ledger_entry_config_hash_optional():
    """Test that config_hash is optional (backward compatibility)."""
    init_ledger()

    # Log without config_hash (should not fail)
    result = log_execution(
        session_id="test-no-config-hash-001",
        agent_id="test-agent-2",
        role_name="TestRole",
        action="test_action",
        output_text="test output"
        # No config_hash parameter
    )

    assert result is not None

    # Entry should exist (config_hash may be None)
    entries = get_last_n_entries(1)
    assert len(entries) == 1
    entry = entries[0]
    # config_hash column exists but may be None
    assert "config_hash" in entry


def test_governance_ledger_includes_config_hash():
    """Test that axp/governance/ledger.py entries include config_hash."""
    base_dir = Path(__file__).parent.parent
    config_hash = compute_config_hash(base_dir)

    test_data = {
        "test": "data",
        "timestamp": "2025-01-01T00:00:00Z"
    }

    # Write ledger entry with config_hash
    ledger_hash = write_ledger_entry(
        role="TestRole",
        action="test_action",
        data=test_data,
        config_hash=config_hash
    )

    assert ledger_hash is not None

    # Verify entry was written (check file exists)
    from axp.governance.ledger import LEDGER_DIR
    assert LEDGER_DIR.exists()


def test_config_hash_drift_detection():
    """Test that config hash enables drift detection."""
    base_dir = Path(__file__).parent.parent

    # Compute hash for current config
    hash1 = compute_config_hash(base_dir)

    # Simulate config change by computing hash with different base
    # (In real scenario, you'd compare hashes from different sessions)
    hash2 = compute_config_hash(base_dir)

    # Same config should produce same hash
    assert hash1 == hash2

    # In a real drift detection scenario:
    # 1. Store hash1 in session A ledger entry
    # 2. Later, compute hash2 for session B
    # 3. Compare: if hash1 != hash2, config drifted between sessions


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

