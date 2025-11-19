#!/usr/bin/env python3
"""
AxProtocol Multi-Domain Testing Suite
Runs comprehensive tests across all domains with various objectives
"""

import os
import sys
import subprocess
import time
from datetime import datetime
from pathlib import Path

# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    """Print formatted section header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.END}\n")

def print_test(test_num, total, domain, objective):
    """Print test information"""
    print(f"{Colors.CYAN}[Test {test_num}/{total}]{Colors.END} {Colors.BOLD}{domain.upper()}{Colors.END}")
    print(f"  Objective: {objective[:80]}...")
    print(f"  Running...")

def run_test(domain, objective, force_domain=True, tier="DEV"):
    """
    Run a single test and return results

    Args:
        domain: Expected domain
        objective: Test objective
        force_domain: Whether to force the domain or let auto-detect
        tier: Model tier to use

    Returns:
        Dict with test results
    """
    start_time = time.time()

    # Build command
    env = os.environ.copy()
    env['TIER'] = tier

    if force_domain:
        env['DOMAIN'] = domain
        cmd = ['python', 'run.py', objective]
    else:
        cmd = ['python', 'run.py', objective]

    try:
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        elapsed = time.time() - start_time

        # Parse output for key metrics
        output = result.stdout
        success = result.returncode == 0

        # Extract TAES metrics if present
        taes_scores = []
        for line in output.split('\n'):
            if 'TAES → IV:' in line:
                taes_scores.append(line.strip())

        # Extract critic score if present
        critic_score = None
        for line in output.split('\n'):
            if 'Average score' in line or 'Scores →' in line:
                critic_score = line.strip()
                break

        # Find log file
        log_file = None
        for line in output.split('\n'):
            if 'Session log:' in line:
                log_file = line.split('Session log:')[-1].strip()
                break

        return {
            'success': success,
            'elapsed': elapsed,
            'taes_scores': taes_scores,
            'critic_score': critic_score,
            'log_file': log_file,
            'output': output,
            'error': result.stderr if not success else None
        }

    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'elapsed': 300,
            'error': 'Test timed out after 5 minutes'
        }
    except Exception as e:
        return {
            'success': False,
            'elapsed': 0,
            'error': str(e)
        }

def print_result(result):
    """Print test result"""
    if result['success']:
        print(f"  {Colors.GREEN}✅ SUCCESS{Colors.END} ({result['elapsed']:.1f}s)")
        if result['taes_scores']:
            print(f"  TAES: {len(result['taes_scores'])} evaluations")
        if result['critic_score']:
            print(f"  {result['critic_score']}")
        if result['log_file']:
            print(f"  Log: {result['log_file']}")
    else:
        print(f"  {Colors.RED}❌ FAILED{Colors.END}")
        if result.get('error'):
            print(f"  Error: {result['error'][:100]}")

# Define test cases
TEST_CASES = [
    # Marketing domain tests
    {
        'domain': 'marketing',
        'objective': 'Launch Instagram campaign for local coffee shop targeting millennials',
        'force_domain': False  # Let auto-detect
    },
    {
        'domain': 'marketing',
        'objective': 'Create lead generation funnel for B2B SaaS product with 100 leads in 30 days',
        'force_domain': False
    },
    {
        'domain': 'marketing',
        'objective': 'Book 5 tree service jobs in 7 days in Omaha using Nextdoor, Facebook, and Craigslist',
        'force_domain': True  # Force to test manual override
    },

    # Technical domain tests
    {
        'domain': 'technical',
        'objective': 'Build REST API for user authentication with OAuth 2.0 and JWT tokens',
        'force_domain': False
    },
    {
        'domain': 'technical',
        'objective': 'Design microservices architecture for e-commerce platform handling 10k requests/sec',
        'force_domain': False
    },
    {
        'domain': 'technical',
        'objective': 'Implement CI/CD pipeline with automated testing, Docker, and Kubernetes deployment',
        'force_domain': True
    },

    # Operations domain tests
    {
        'domain': 'ops',
        'objective': 'Design employee onboarding workflow for 50 new hires per month with 2-person HR team',
        'force_domain': False
    },
    {
        'domain': 'ops',
        'objective': 'Optimize customer support process to reduce response time from 24h to 4h',
        'force_domain': False
    },
    {
        'domain': 'ops',
        'objective': 'Create incident response procedure for production outages with escalation paths',
        'force_domain': True
    },

    # Creative domain tests
    {
        'domain': 'creative',
        'objective': 'Design brand identity for eco-friendly startup including logo, colors, and voice',
        'force_domain': False
    },
    {
        'domain': 'creative',
        'objective': 'Create 10-episode podcast series about entrepreneurship with guest interview format',
        'force_domain': False
    },
    {
        'domain': 'creative',
        'objective': 'Develop content strategy and visual style guide for lifestyle brand on Instagram',
        'force_domain': True
    },

    # Education domain tests
    {
        'domain': 'education',
        'objective': 'Create 8-week online course teaching Python programming to complete beginners',
        'force_domain': False
    },
    {
        'domain': 'education',
        'objective': 'Design corporate leadership training program with 6 modules and capstone project',
        'force_domain': False
    },
    {
        'domain': 'education',
        'objective': 'Develop certification curriculum for data science with hands-on labs and assessments',
        'force_domain': True
    },
]

def run_all_tests(tier="DEV", skip_slow=False):
    """Run all test cases"""

    print_header("AxProtocol Multi-Domain Testing Suite")
    print(f"Tier: {tier}")
    print(f"Total tests: {len(TEST_CASES)}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if skip_slow:
        print(f"{Colors.YELLOW}Note: Skipping slow tests{Colors.END}")

    results = []
    total_tests = len(TEST_CASES)

    for i, test_case in enumerate(TEST_CASES, 1):
        domain = test_case['domain']
        objective = test_case['objective']
        force_domain = test_case['force_domain']

        print_test(i, total_tests, domain, objective)

        result = run_test(domain, objective, force_domain, tier)
        result['test_case'] = test_case
        results.append(result)

        print_result(result)

        # Small delay between tests
        time.sleep(2)

    return results

def print_summary(results):
    """Print test summary"""

    print_header("Test Summary")

    # Overall stats
    total = len(results)
    passed = sum(1 for r in results if r['success'])
    failed = total - passed

    print(f"Total: {total}")
    print(f"{Colors.GREEN}Passed: {passed}{Colors.END}")
    if failed > 0:
        print(f"{Colors.RED}Failed: {failed}{Colors.END}")

    # Time stats
    total_time = sum(r['elapsed'] for r in results)
    avg_time = total_time / total if total > 0 else 0

    print(f"\nTotal time: {total_time:.1f}s")
    print(f"Average time: {avg_time:.1f}s per test")

    # Domain breakdown
    print(f"\n{Colors.BOLD}By Domain:{Colors.END}")
    domains = {}
    for r in results:
        domain = r['test_case']['domain']
        if domain not in domains:
            domains[domain] = {'passed': 0, 'failed': 0}
        if r['success']:
            domains[domain]['passed'] += 1
        else:
            domains[domain]['failed'] += 1

    for domain, stats in sorted(domains.items()):
        total_domain = stats['passed'] + stats['failed']
        print(f"  {domain:12} {stats['passed']}/{total_domain} passed")

    # Auto-detect vs forced
    print(f"\n{Colors.BOLD}Detection Method:{Colors.END}")
    auto = sum(1 for r in results if not r['test_case']['force_domain'] and r['success'])
    forced = sum(1 for r in results if r['test_case']['force_domain'] and r['success'])
    print(f"  Auto-detected: {auto} passed")
    print(f"  Force domain:  {forced} passed")

    # Failed tests details
    if failed > 0:
        print(f"\n{Colors.RED}{Colors.BOLD}Failed Tests:{Colors.END}")
        for i, r in enumerate(results, 1):
            if not r['success']:
                domain = r['test_case']['domain']
                objective = r['test_case']['objective'][:60]
                print(f"  {i}. [{domain}] {objective}...")
                if r.get('error'):
                    print(f"     Error: {r['error'][:80]}")

    # Success rate
    success_rate = (passed / total * 100) if total > 0 else 0
    print(f"\n{Colors.BOLD}Success Rate: {success_rate:.1f}%{Colors.END}")

    if success_rate == 100:
        print(f"{Colors.GREEN}{Colors.BOLD}🎉 ALL TESTS PASSED!{Colors.END}")
    elif success_rate >= 80:
        print(f"{Colors.YELLOW}⚠️  Most tests passed, review failures{Colors.END}")
    else:
        print(f"{Colors.RED}❌ Multiple failures, investigation needed{Colors.END}")

def save_results(results, output_file="test_results.txt"):
    """Save detailed results to file"""

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("AxProtocol Multi-Domain Test Results\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*70 + "\n\n")

        for i, r in enumerate(results, 1):
            test_case = r['test_case']
            f.write(f"Test {i}: {test_case['domain'].upper()}\n")
            f.write(f"Objective: {test_case['objective']}\n")
            f.write(f"Force Domain: {test_case['force_domain']}\n")
            f.write(f"Status: {'PASS' if r['success'] else 'FAIL'}\n")
            f.write(f"Time: {r['elapsed']:.1f}s\n")

            if r.get('taes_scores'):
                f.write(f"TAES Evaluations: {len(r['taes_scores'])}\n")
                for score in r['taes_scores']:
                    f.write(f"  {score}\n")

            if r.get('critic_score'):
                f.write(f"Critic: {r['critic_score']}\n")

            if r.get('log_file'):
                f.write(f"Log: {r['log_file']}\n")

            if r.get('error'):
                f.write(f"Error: {r['error']}\n")

            f.write("\n" + "-"*70 + "\n\n")

    print(f"\n{Colors.CYAN}Detailed results saved to: {output_file}{Colors.END}")

def main():
    """Main test runner"""

    # Parse command line arguments
    tier = "DEV"
    skip_slow = False
    save_to_file = True

    if len(sys.argv) > 1:
        if 'PREP' in sys.argv:
            tier = "PREP"
        elif 'CLIENT' in sys.argv:
            tier = "CLIENT"

        if '--fast' in sys.argv or '-f' in sys.argv:
            skip_slow = True

        if '--no-save' in sys.argv:
            save_to_file = False

    # Run tests
    results = run_all_tests(tier=tier, skip_slow=skip_slow)

    # Print summary
    print_summary(results)

    # Save results
    if save_to_file:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"test_results_{timestamp}_{tier.lower()}.txt"
        save_results(results, output_file)

    # Exit with appropriate code
    failed = sum(1 for r in results if not r['success'])
    sys.exit(0 if failed == 0 else 1)

if __name__ == "__main__":
    main()