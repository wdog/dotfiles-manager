#!/usr/bin/env python3
"""
Test runner script for dotfiles-manager
Provides easy way to run tests with different configurations
"""

import sys
import subprocess
import argparse
import os
from pathlib import Path


def run_command(cmd, description=""):
    """Run a command and handle output"""
    if description:
        print(f"\n🔄 {description}")
        print("-" * 50)

    try:
        result = subprocess.run(cmd, shell=True, check=True, text=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {e}")
        return False


def check_dependencies():
    """Check if test dependencies are installed"""
    required_packages = ["pytest", "pytest-cov", "pytest-mock"]
    missing_packages = []

    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print("❌ Missing test dependencies:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\nInstall with: pip install -r tests/requirements.txt")
        return False

    return True


def run_unit_tests(verbose=False, coverage=False):
    """Run unit tests"""
    cmd = "python -m pytest tests/ -k 'not integration'"

    if verbose:
        cmd += " -v"

    if coverage:
        cmd += " --cov=dotfiles_manager --cov-report=html --cov-report=term-missing"

    return run_command(cmd, "Running unit tests")


def run_integration_tests(verbose=False):
    """Run integration tests"""
    cmd = "python -m pytest tests/test_integration.py -m integration"

    if verbose:
        cmd += " -v"

    return run_command(cmd, "Running integration tests")


def run_all_tests(verbose=False, coverage=False):
    """Run all tests"""
    cmd = "python -m pytest tests/"

    if verbose:
        cmd += " -v"

    if coverage:
        cmd += " --cov=dotfiles_manager --cov-report=html --cov-report=term-missing"

    return run_command(cmd, "Running all tests")


def run_specific_test(test_path, verbose=False):
    """Run specific test file or test function"""
    cmd = f"python -m pytest {test_path}"

    if verbose:
        cmd += " -v"

    return run_command(cmd, f"Running specific test: {test_path}")


def generate_coverage_report():
    """Generate detailed coverage report"""
    cmd = "python -m pytest tests/ --cov=dotfiles_manager --cov-report=html --cov-report=term-missing --cov-report=xml"

    success = run_command(cmd, "Generating coverage report")

    if success:
        print("\n📊 Coverage reports generated:")
        print("   - HTML: htmlcov/index.html")
        print("   - XML: coverage.xml")
        print("   - Terminal output above")

    return success


def lint_code():
    """Run code linting (if available)"""
    linters = [
        ("flake8", "flake8 dotfiles_manager/ tests/"),
        ("pylint", "pylint dotfiles_manager/"),
        ("black", "black --check dotfiles_manager/ tests/")
    ]

    results = []
    for linter_name, linter_cmd in linters:
        try:
            subprocess.run(["which", linter_name], check=True, capture_output=True)
            success = run_command(linter_cmd, f"Running {linter_name}")
            results.append((linter_name, success))
        except subprocess.CalledProcessError:
            print(f"⚠️  {linter_name} not installed, skipping")

    return all(result[1] for result in results) if results else True


def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(description="Test runner for dotfiles-manager")
    parser.add_argument("--unit", action="store_true", help="Run only unit tests")
    parser.add_argument("--integration", action="store_true", help="Run only integration tests")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--lint", action="store_true", help="Run code linting")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--test", help="Run specific test file or function")
    parser.add_argument("--check-deps", action="store_true", help="Check test dependencies")

    args = parser.parse_args()

    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)

    print("🧪 Dotfiles Manager Test Runner")
    print("=" * 40)

    # Check dependencies first
    if args.check_deps:
        if check_dependencies():
            print("✅ All test dependencies are installed")
        sys.exit(0)

    if not check_dependencies():
        sys.exit(1)

    success = True

    # Run linting if requested
    if args.lint:
        success = lint_code() and success

    # Run specific test
    if args.test:
        success = run_specific_test(args.test, args.verbose) and success

    # Run unit tests
    elif args.unit:
        success = run_unit_tests(args.verbose, args.coverage) and success

    # Run integration tests
    elif args.integration:
        success = run_integration_tests(args.verbose) and success

    # Generate coverage report
    elif args.coverage:
        success = generate_coverage_report() and success

    # Run all tests (default)
    else:
        success = run_all_tests(args.verbose, args.coverage) and success

    # Summary
    print("\n" + "=" * 40)
    if success:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()