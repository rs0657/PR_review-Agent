#!/usr/bin/env python3
"""
Project Structure Validator

This script validates the PR Review Agent project structure to ensure
all required files are present and properly organized.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple

class ProjectValidator:
    """Validates project structure and reports issues."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.errors: List[str] = []
        self.warnings: List[str] = []
        
    def validate(self) -> bool:
        """Run all validation checks."""
        print("🔍 Validating PR Review Agent project structure...")
        print(f"📁 Project root: {self.project_root}")
        print()
        
        # Check directory structure
        self._check_directory_structure()
        
        # Check required files
        self._check_required_files()
        
        # Check Python package structure
        self._check_python_packages()
        
        # Check configuration files
        self._check_configuration_files()
        
        # Check documentation
        self._check_documentation()
        
        # Check tests
        self._check_tests()
        
        # Report results
        return self._report_results()
    
    def _check_directory_structure(self):
        """Check main directory structure."""
        required_dirs = [
            "pr_review_agent",
            "pr_review_agent/core",
            "pr_review_agent/adapters", 
            "pr_review_agent/analyzers",
            "tests",
            "tests/unit",
            "config",
            ".github/workflows"
        ]
        
        print("📂 Checking directory structure...")
        for dir_path in required_dirs:
            full_path = self.project_root / dir_path
            if not full_path.exists():
                self.errors.append(f"Missing required directory: {dir_path}")
            elif not full_path.is_dir():
                self.errors.append(f"Path exists but is not a directory: {dir_path}")
            else:
                print(f"  ✅ {dir_path}")
        print()
    
    def _check_required_files(self):
        """Check required project files."""
        required_files = [
            "README.md",
            "requirements.txt", 
            "pyproject.toml",
            "setup.py",
            ".gitignore",
            ".env.template",
            "LICENSE",
            "CHANGELOG.md",
            "CONTRIBUTING.md",
            "SECURITY.md"
        ]
        
        print("📄 Checking required files...")
        for file_path in required_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                if file_path in ["LICENSE", "CHANGELOG.md"]:
                    self.warnings.append(f"Recommended file missing: {file_path}")
                else:
                    self.errors.append(f"Required file missing: {file_path}")
            elif not full_path.is_file():
                self.errors.append(f"Path exists but is not a file: {file_path}")
            else:
                print(f"  ✅ {file_path}")
        print()
    
    def _check_python_packages(self):
        """Check Python package structure."""
        package_files = {
            "pr_review_agent/__init__.py": "Main package init",
            "pr_review_agent/cli.py": "CLI interface",
            "pr_review_agent/core/__init__.py": "Core package init",
            "pr_review_agent/core/config.py": "Configuration management",
            "pr_review_agent/core/reviewer.py": "Main reviewer class",
            "pr_review_agent/core/ai_feedback.py": "AI feedback system",
            "pr_review_agent/core/scorer.py": "Scoring system",
            "pr_review_agent/adapters/__init__.py": "Adapters package init",
            "pr_review_agent/adapters/base.py": "Base adapter classes",
            "pr_review_agent/adapters/github.py": "GitHub adapter",
            "pr_review_agent/adapters/gitlab.py": "GitLab adapter",
            "pr_review_agent/adapters/bitbucket.py": "Bitbucket adapter",
            "pr_review_agent/analyzers/__init__.py": "Analyzers package init",
            "pr_review_agent/analyzers/base.py": "Base analyzer classes",
            "pr_review_agent/analyzers/manager.py": "Analysis manager",
        }
        
        print("🐍 Checking Python package files...")
        for file_path, description in package_files.items():
            full_path = self.project_root / file_path
            if not full_path.exists():
                self.errors.append(f"Missing Python file: {file_path} ({description})")
            elif not full_path.is_file():
                self.errors.append(f"Path exists but is not a file: {file_path}")
            else:
                print(f"  ✅ {file_path}")
        print()
    
    def _check_configuration_files(self):
        """Check configuration files."""
        config_files = [
            "config/pr_review_config.yaml",
            ".github/workflows/ci.yml"
        ]
        
        print("⚙️  Checking configuration files...")
        for file_path in config_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                self.errors.append(f"Missing configuration file: {file_path}")
            else:
                print(f"  ✅ {file_path}")
        print()
    
    def _check_documentation(self):
        """Check documentation files."""
        doc_files = {
            "README.md": "Main documentation",
            "CONTRIBUTING.md": "Contribution guidelines",
            "SECURITY.md": "Security policy"
        }
        
        print("📚 Checking documentation...")
        for file_path, description in doc_files.items():
            full_path = self.project_root / file_path
            if full_path.exists():
                # Check file size (should have content)
                if full_path.stat().st_size < 100:
                    self.warnings.append(f"Documentation file seems too small: {file_path}")
                else:
                    print(f"  ✅ {file_path}")
            else:
                self.errors.append(f"Missing documentation: {file_path} ({description})")
        print()
    
    def _check_tests(self):
        """Check test files."""
        test_files = [
            "tests/__init__.py",
            "tests/conftest.py",
            "tests/run_tests.py",
            "tests/test_integration.py",
            "tests/unit/__init__.py",
            "tests/unit/test_config.py",
            "tests/unit/test_reviewer.py",
            "tests/unit/test_adapters.py",
            "tests/unit/test_analyzers.py",
            "tests/unit/test_scorer.py",
            "tests/unit/test_cli.py"
        ]
        
        print("🧪 Checking test files...")
        for file_path in test_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                self.warnings.append(f"Missing test file: {file_path}")
            else:
                print(f"  ✅ {file_path}")
        print()
    
    def _report_results(self) -> bool:
        """Report validation results."""
        print("📊 Validation Results")
        print("=" * 50)
        
        if not self.errors and not self.warnings:
            print("🎉 Perfect! Project structure is properly organized.")
            return True
        
        if self.errors:
            print(f"❌ Found {len(self.errors)} error(s):")
            for error in self.errors:
                print(f"  • {error}")
            print()
        
        if self.warnings:
            print(f"⚠️  Found {len(self.warnings)} warning(s):")
            for warning in self.warnings:
                print(f"  • {warning}")
            print()
        
        if self.errors:
            print("❌ Project structure validation FAILED")
            print("Please fix the errors above before proceeding.")
            return False
        else:
            print("✅ Project structure validation PASSED")
            print("Warnings are optional improvements.")
            return True

def main():
    """Main validation function."""
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        project_root = os.getcwd()
    
    validator = ProjectValidator(project_root)
    success = validator.validate()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
