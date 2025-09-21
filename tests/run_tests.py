"""
Test runner script for the PR Review Agent
"""
import sys
import os
import subprocess
from pathlib import Path

def main():
    """Run all tests and generate coverage report"""
    project_root = Path(__file__).parent.parent
    
    print("🧪 Running PR Review Agent Tests")
    print("=" * 50)
    
    # Change to project directory
    os.chdir(project_root)
    
    # Install test dependencies if needed
    print("📦 Installing test dependencies...")
    subprocess.run([
        sys.executable, "-m", "pip", "install", 
        "pytest", "pytest-cov", "responses"
    ], check=False)
    
    # Run tests with coverage
    print("\n🔍 Running unit tests...")
    test_cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-v",
        "--cov=pr_review_agent",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov",
        "--cov-fail-under=70"
    ]
    
    result = subprocess.run(test_cmd)
    
    if result.returncode == 0:
        print("\n✅ All tests passed!")
        print("\n📊 Coverage report generated in htmlcov/index.html")
    else:
        print("\n❌ Some tests failed!")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
