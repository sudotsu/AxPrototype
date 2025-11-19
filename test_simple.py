#!/usr/bin/env python3
"""
Simple multi-domain test - Windows compatible
"""

import os
import sys
from datetime import datetime

# Color output for Windows
try:
    import colorama
    colorama.init()
    HAS_COLOR = True
except ImportError:
    HAS_COLOR = False

def green(text):
    return f"\033[92m{text}\033[0m" if HAS_COLOR else text

def red(text):
    return f"\033[91m{text}\033[0m" if HAS_COLOR else text

def yellow(text):
    return f"\033[93m{text}\033[0m" if HAS_COLOR else text

def blue(text):
    return f"\033[94m{text}\033[0m" if HAS_COLOR else text

print("="*70)
print("AxProtocol Multi-Domain Simple Test")
print("="*70)
print()

# Test cases
tests = [
    ("marketing", "Launch Instagram campaign for local coffee shop"),
    ("technical", "Build REST API for user authentication with OAuth"),
    ("ops", "Design employee onboarding workflow for 50 new hires"),
    ("creative", "Create brand identity for eco-friendly startup"),
    ("education", "Develop 8-week Python programming course for beginners"),
]

results = []

for i, (domain, objective) in enumerate(tests, 1):
    print(f"\n[Test {i}/{len(tests)}] {blue(domain.upper())}")
    print(f"Objective: {objective[:60]}...")

    # Set environment
    os.environ['DOMAIN'] = domain
    os.environ['TIER'] = 'DEV'

    try:
        # Import and run directly (no subprocess)
        import importlib
        import sys

        # Capture original argv
        original_argv = sys.argv.copy()

        # Set argv for run.py
        sys.argv = ['run.py', objective]

        # Reload run module to execute with new objective
        if 'run' in sys.modules:
            importlib.reload(sys.modules['run'])
        else:
            import run

        # Restore argv
        sys.argv = original_argv

        print(green("  ✅ PASS"))
        results.append((domain, True))

    except Exception as e:
        print(red(f"  ❌ FAIL: {str(e)[:50]}"))
        results.append((domain, False))

# Summary
print("\n" + "="*70)
print("Summary")
print("="*70)

passed = sum(1 for _, success in results if success)
failed = len(results) - passed

print(f"\nTotal: {len(results)}")
print(green(f"Passed: {passed}"))
if failed > 0:
    print(red(f"Failed: {failed}"))

# By domain
print("\nBy Domain:")
for domain, success in results:
    status = green("✅") if success else red("❌")
    print(f"  {status} {domain}")

success_rate = (passed / len(results) * 100) if results else 0
print(f"\nSuccess Rate: {success_rate:.0f}%")

if success_rate == 100:
    print(green("\n🎉 ALL TESTS PASSED!"))
else:
    print(yellow("\n⚠️ Some tests need attention"))

print("\n" + "="*70)