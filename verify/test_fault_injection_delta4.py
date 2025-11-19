"""
Δ4: Ledger Tampering Tests

Tests that Sentinel detects forged or tampered ledger entries.
Verifies cryptographic signature validation and integrity checks.
"""

import pytest
import json
import glob
import os
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any

# Import ledger and verification modules
try:
    from axp.governance.ledger import write_ledger_entry, LEDGER_DIR
    from axp.sentinel.verify_ledger import verify_all
    LEDGER_AVAILABLE = True
except ImportError as e:
    LEDGER_AVAILABLE = False
    print(f"⚠️  Warning: Ledger modules not available: {e}")


class LedgerTamperingTest:
    """Test class for ledger tampering scenarios"""

    def __init__(self, test_id: str, description: str):
        self.test_id = test_id
        self.description = description
        self.passed = None
        self.error = None

    def run(self) -> bool:
        """Execute the test. Return True if tampering is detected."""
        raise NotImplementedError("Subclasses must implement run()")

    def report(self) -> Dict:
        """Generate test report"""
        return {
            'test_id': self.test_id,
            'description': self.description,
            'passed': self.passed,
            'error': self.error
        }


class TestDelta4LedgerForge(LedgerTamperingTest):
    """Test Δ4-1: Detect forged ledger entry without valid signature"""

    def __init__(self):
        super().__init__(
            "Δ4-1",
            "Detect forged ledger entry appended without valid signature"
        )

    def run(self) -> bool:
        """Test that forged entries are detected"""
        if not LEDGER_AVAILABLE:
            self.passed = None
            self.error = "Ledger modules not available"
            return False

        try:
            print(f"\n[{self.test_id}] Testing: {self.description}")

            # Write valid entry
            write_ledger_entry("TEST", "validation", {"value": 1, "test": "delta4"})

            # Find the most recent ledger file
            ledger_files = list(LEDGER_DIR.glob("*.jsonl"))
            if not ledger_files:
                self.passed = False
                self.error = "No ledger files found after writing entry"
                return False

            valid_file = max(ledger_files, key=os.path.getctime)
            print(f"   Written to: {valid_file.name}")

            # Tamper: Append invalid entry without signature
            with open(valid_file, "a", encoding="utf8") as f:
                f.write('\n{"forged": true, "entry": {"role": "ATTACKER", "action": "tamper"}}\n')

            print(f"   Tampered: Appended forged entry")

            # Run Sentinel verification
            report = verify_all(str(LEDGER_DIR))

            print(f"   Verification report: {report}")

            # Check for tampering detection
            # Sentinel should detect invalid signature or malformed entry
            details = report.get('details', [])
            tamper_detected = False

            for detail in details:
                if isinstance(detail, dict):
                    # Check for signature verification failures
                    if detail.get('error') == 'invalid_signature' or 'signature' in str(detail).lower():
                        tamper_detected = True
                        break
                    # Check for malformed entry errors
                    if 'malformed' in str(detail).lower() or 'invalid' in str(detail).lower():
                        tamper_detected = True
                        break

            # Also check if verification failed overall
            if not report.get('verified', True):
                tamper_detected = True

            if tamper_detected:
                self.passed = True
                print(f"   ✅ Tampering detected by Sentinel")
            else:
                self.passed = False
                self.error = "Tampering not detected - security vulnerability"
                print(f"   ❌ Tampering NOT detected")

            return self.passed

        except Exception as e:
            self.passed = False
            self.error = f"Test execution failed: {str(e)}"
            import traceback
            print(f"   ❌ Error: {traceback.format_exc()}")
            return False


class TestDelta4LedgerModify(LedgerTamperingTest):
    """Test Δ4-2: Detect modified ledger entry"""

    def __init__(self):
        super().__init__(
            "Δ4-2",
            "Detect modified ledger entry (signature mismatch)"
        )

    def run(self) -> bool:
        """Test that modified entries are detected"""
        if not LEDGER_AVAILABLE:
            self.passed = None
            self.error = "Ledger modules not available"
            return False

        try:
            print(f"\n[{self.test_id}] Testing: {self.description}")

            # Write valid entry
            write_ledger_entry("TEST", "validation", {"value": 1, "test": "delta4_modify"})

            # Find the most recent ledger file
            ledger_files = list(LEDGER_DIR.glob("*.jsonl"))
            if not ledger_files:
                self.passed = False
                self.error = "No ledger files found"
                return False

            valid_file = max(ledger_files, key=os.path.getctime)

            # Read file and modify an entry
            with open(valid_file, "r", encoding="utf8") as f:
                lines = f.readlines()

            if not lines:
                self.passed = False
                self.error = "Ledger file is empty"
                return False

            # Modify the last entry (change data but keep structure)
            last_line = lines[-1]
            try:
                entry_data = json.loads(last_line)
                # Modify the entry data
                if 'entry' in entry_data:
                    entry_data['entry']['data']['value'] = 999  # Tampered value
                    entry_data['entry']['role'] = 'TAMPERED'
                lines[-1] = json.dumps(entry_data) + '\n'
            except json.JSONDecodeError:
                self.passed = False
                self.error = "Could not parse ledger entry"
                return False

            # Write modified entry back
            with open(valid_file, "w", encoding="utf8") as f:
                f.writelines(lines)

            print(f"   Modified entry in: {valid_file.name}")

            # Run Sentinel verification
            report = verify_all(str(LEDGER_DIR))

            # Check for tampering detection (signature should no longer match)
            details = report.get('details', [])
            tamper_detected = False

            for detail in details:
                if isinstance(detail, dict):
                    error_type = detail.get('error', '')
                    if error_type in ['sig_invalid', 'invalid_signature', 'hash_mismatch']:
                        tamper_detected = True
                        break

            if not report.get('verified', True):
                tamper_detected = True

            if tamper_detected:
                self.passed = True
                print(f"   ✅ Modification detected by Sentinel")
            else:
                self.passed = False
                self.error = "Modification not detected - security vulnerability"
                print(f"   ❌ Modification NOT detected")

            return self.passed

        except Exception as e:
            self.passed = False
            self.error = f"Test execution failed: {str(e)}"
            import traceback
            print(f"   ❌ Error: {traceback.format_exc()}")
            return False


class TestDelta4LedgerMalformed(LedgerTamperingTest):
    """Test Δ4-3: Detect malformed ledger entry"""

    def __init__(self):
        super().__init__(
            "Δ4-3",
            "Detect malformed ledger entry (invalid JSON structure)"
        )

    def run(self) -> bool:
        """Test that malformed entries are detected"""
        if not LEDGER_AVAILABLE:
            self.passed = None
            self.error = "Ledger modules not available"
            return False

        try:
            print(f"\n[{self.test_id}] Testing: {self.description}")

            # Write valid entry first
            write_ledger_entry("TEST", "validation", {"value": 1, "test": "delta4_malformed"})

            # Find the most recent ledger file
            ledger_files = list(LEDGER_DIR.glob("*.jsonl"))
            if not ledger_files:
                self.passed = False
                self.error = "No ledger files found"
                return False

            valid_file = max(ledger_files, key=os.path.getctime)

            # Append malformed JSON
            with open(valid_file, "a", encoding="utf8") as f:
                f.write('\n{"invalid": json, "malformed": true}\n')  # Invalid JSON

            print(f"   Appended malformed entry to: {valid_file.name}")

            # Run Sentinel verification
            report = verify_all(str(LEDGER_DIR))

            # Check for malformed entry detection
            details = report.get('details', [])
            malformed_detected = False

            for detail in details:
                if isinstance(detail, dict):
                    if 'malformed' in str(detail).lower() or 'json' in str(detail).lower():
                        malformed_detected = True
                        break
                    if detail.get('error') and 'parse' in str(detail.get('error')).lower():
                        malformed_detected = True
                        break

            # Verification should fail or flag the issue
            if not report.get('verified', True) or malformed_detected:
                self.passed = True
                print(f"   ✅ Malformed entry detected by Sentinel")
            else:
                self.passed = False
                self.error = "Malformed entry not detected"
                print(f"   ❌ Malformed entry NOT detected")

            return self.passed

        except Exception as e:
            self.passed = False
            self.error = f"Test execution failed: {str(e)}"
            import traceback
            print(f"   ❌ Error: {traceback.format_exc()}")
            return False


def run_delta_4_tests() -> list:
    """
    Run all Δ4 ledger tampering tests.

    Returns:
        List of test result dictionaries
    """
    tests = [
        TestDelta4LedgerForge(),
        TestDelta4LedgerModify(),
        TestDelta4LedgerMalformed(),
    ]

    results = []
    for test in tests:
        try:
            test.run()
            results.append(test.report())
        except Exception as e:
            results.append({
                'test_id': test.test_id,
                'description': test.description,
                'passed': False,
                'error': f"Test execution exception: {str(e)}"
            })

    return results


# Pytest-compatible test functions
def test_delta4_ledger_forge():
    """Pytest test for Δ4-1: Forged ledger entry"""
    test = TestDelta4LedgerForge()
    result = test.run()
    assert result is True, f"Test {test.test_id} failed: {test.error}"


def test_delta4_ledger_modify():
    """Pytest test for Δ4-2: Modified ledger entry"""
    test = TestDelta4LedgerModify()
    result = test.run()
    assert result is True, f"Test {test.test_id} failed: {test.error}"


def test_delta4_ledger_malformed():
    """Pytest test for Δ4-3: Malformed ledger entry"""
    test = TestDelta4LedgerMalformed()
    result = test.run()
    assert result is True, f"Test {test.test_id} failed: {test.error}"


def test_delta4_suite():
    """Run all Δ4 tests"""
    results = run_delta_4_tests()
    assert len(results) > 0, "No Δ4 tests executed"

    for result in results:
        assert result['passed'] is not None, f"Test {result['test_id']} was skipped"

    passed = sum(1 for r in results if r['passed'] is True)
    print(f"\n[Δ4] Passed: {passed}/{len(results)}")

    # Security-critical: All Δ4 tests should pass (tampering should be detected)
    for result in results:
        if not result['passed']:
            pytest.fail(f"Security test {result['test_id']} failed: {result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

