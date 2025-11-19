"""
Pytest-compatible test suite for AxProtocol fault injection tests.
Integrates fault_injection.py with pytest for CI/CD compatibility.
"""
import pytest
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fault_injection import (
    run_delta_1_tests,
    run_delta_2_tests,
    run_delta_3_tests,
    run_delta_4_tests,
    FaultInjectionTest
)


class TestDelta1MalformedObjectives:
    """Test suite for Δ1: Malformed Objectives"""

    def test_delta1_suite(self):
        """Run all Δ1 tests"""
        results = run_delta_1_tests()
        assert len(results) > 0, "No Δ1 tests executed"

        # Check that all tests completed (passed or failed, not skipped)
        for result in results:
            assert result['passed'] is not None, f"Test {result['test_id']} was skipped"

        # Log results
        passed = sum(1 for r in results if r['passed'] is True)
        print(f"\n[Δ1] Passed: {passed}/{len(results)}")


class TestDelta2ScoreManipulation:
    """Test suite for Δ2: Score Manipulation"""

    def test_delta2_suite(self):
        """Run all Δ2 tests"""
        results = run_delta_2_tests()
        assert len(results) > 0, "No Δ2 tests executed"

        for result in results:
            assert result['passed'] is not None, f"Test {result['test_id']} was skipped"

        passed = sum(1 for r in results if r['passed'] is True)
        print(f"\n[Δ2] Passed: {passed}/{len(results)}")


class TestDelta3ProtocolBypass:
    """Test suite for Δ3: Protocol Bypass Attempts"""

    def test_delta3_suite(self):
        """Run all Δ3 tests"""
        results = run_delta_3_tests()
        assert len(results) > 0, "No Δ3 tests executed"

        for result in results:
            assert result['passed'] is not None, f"Test {result['test_id']} was skipped"

        passed = sum(1 for r in results if r['passed'] is True)
        print(f"\n[Δ3] Passed: {passed}/{len(results)}")

        # Security-critical: All Δ3 tests should pass (bypasses should fail)
        for result in results:
            if not result['passed']:
                pytest.fail(f"Security test {result['test_id']} failed: {result.get('error', 'Unknown error')}")


class TestDelta4LedgerTampering:
    """Test suite for Δ4: Ledger Tampering Detection"""

    def test_delta4_suite(self):
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


@pytest.mark.parametrize("test_suite", ["Δ1", "Δ2", "Δ3", "Δ4"])
def test_all_suites(test_suite):
    """Parametrized test for all suites"""
    if test_suite == "Δ1":
        results = run_delta_1_tests()
    elif test_suite == "Δ2":
        results = run_delta_2_tests()
    elif test_suite == "Δ3":
        results = run_delta_3_tests()
    elif test_suite == "Δ4":
        results = run_delta_4_tests()
    else:
        pytest.skip(f"Unknown test suite: {test_suite}")

    assert len(results) > 0, f"No {test_suite} tests executed"

    # Report results
    passed = sum(1 for r in results if r['passed'] is True)
    failed = sum(1 for r in results if r['passed'] is False)

    print(f"\n[{test_suite}] Results: {passed} passed, {failed} failed, {len(results) - passed - failed} skipped")

    # For security tests (Δ3, Δ4), failures are critical
    if test_suite in ["Δ3", "Δ4"] and failed > 0:
        pytest.fail(f"Security tests failed: {failed} {'bypass attempts' if test_suite == 'Δ3' else 'tampering attempts'} succeeded")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

