#!/usr/bin/env python3
"""
PR Review Agent - Comprehensive Verification Script

This script runs a complete verification suite to ensure the PR Review Agent
is working properly across all components and features.
"""

import sys
import os
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any

class VerificationSuite:
    """Comprehensive verification test suite."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent  # Go up one level from scripts/
        self.passed_tests = 0
        self.total_tests = 0
        self.failed_tests = []
        
    def run_verification(self) -> bool:
        """Run complete verification suite."""
        print("🔍 PR Review Agent - Comprehensive Verification")
        print("=" * 60)
        print(f"📁 Project Root: {self.project_root}")
        print()
        
        # Run all verification tests
        test_groups = [
            ("🏗️  Project Structure", self._verify_project_structure),
            ("📦 Package Imports", self._verify_package_imports),
            ("💻 CLI Functionality", self._verify_cli_functionality),
            ("🔧 Configuration System", self._verify_configuration),
            ("📊 Analysis Engine", self._verify_analysis_engine),
            ("🤖 AI Integration", self._verify_ai_integration),
            ("📈 Scoring System", self._verify_scoring_system),
            ("🔌 Adapter System", self._verify_adapters),
            ("📚 Documentation", self._verify_documentation),
            ("🧪 Test Coverage", self._verify_tests),
        ]
        
        for group_name, test_func in test_groups:
            print(f"\n{group_name}")
            print("-" * 40)
            test_func()
        
        # Generate final report
        return self._generate_report()
    
    def _test(self, name: str, condition: bool, error_msg: str = None) -> bool:
        """Helper method to run a test and track results."""
        self.total_tests += 1
        if condition:
            print(f"  ✅ {name}")
            self.passed_tests += 1
            return True
        else:
            print(f"  ❌ {name}")
            if error_msg:
                print(f"     💡 {error_msg}")
            self.failed_tests.append(name)
            return False
    
    def _verify_project_structure(self):
        """Verify project directory structure."""
        required_dirs = [
            "pr_review_agent",
            "pr_review_agent/core",
            "pr_review_agent/adapters",
            "pr_review_agent/analyzers",
            "tests",
            "tests/unit",
            "config",
            ".github/workflows",
            "scripts"
        ]
        
        for dir_path in required_dirs:
            full_path = self.project_root / dir_path
            self._test(
                f"Directory exists: {dir_path}",
                full_path.exists() and full_path.is_dir(),
                f"Create missing directory: {dir_path}"
            )
        
        required_files = [
            "README.md",
            "LICENSE",
            "requirements.txt",
            "setup.py",
            ".gitignore",
            ".env.template",
            "config/pr_review_config.yaml"
        ]
        
        for file_path in required_files:
            full_path = self.project_root / file_path
            self._test(
                f"File exists: {file_path}",
                full_path.exists() and full_path.is_file(),
                f"Create missing file: {file_path}"
            )
    
    def _verify_package_imports(self):
        """Verify Python package can be imported."""
        import_tests = [
            ("Core config module", "from pr_review_agent.core.config import Config"),
            ("Standalone CLI", "import standalone_cli"),
            ("Demo script", "import demo"),
        ]
        
        for test_name, import_statement in import_tests:
            try:
                exec(import_statement)
                self._test(f"Import: {test_name}", True)
            except ImportError as e:
                self._test(f"Import: {test_name}", False, f"Import error: {e}")
            except Exception as e:
                self._test(f"Import: {test_name}", False, f"Error: {e}")
    
    def _verify_cli_functionality(self):
        """Verify CLI commands work properly."""
        cli_tests = [
            ("Help command", ["python", "standalone_cli.py", "--help"]),
            ("Status command", ["python", "standalone_cli.py", "status"]),
            ("Configure command", ["python", "standalone_cli.py", "configure"]),
        ]
        
        for test_name, command in cli_tests:
            try:
                result = subprocess.run(
                    command, 
                    cwd=self.project_root,
                    capture_output=True, 
                    text=True, 
                    timeout=10
                )
                self._test(
                    f"CLI: {test_name}",
                    result.returncode == 0,
                    f"Command failed with code {result.returncode}: {result.stderr[:100]}"
                )
            except subprocess.TimeoutExpired:
                self._test(f"CLI: {test_name}", False, "Command timed out")
            except Exception as e:
                self._test(f"CLI: {test_name}", False, f"Error running command: {e}")
    
    def _verify_configuration(self):
        """Verify configuration system."""
        config_file = self.project_root / "config" / "pr_review_config.yaml"
        env_template = self.project_root / ".env.template"
        
        self._test(
            "Configuration file exists",
            config_file.exists(),
            "Create config/pr_review_config.yaml"
        )
        
        self._test(
            "Environment template exists",
            env_template.exists(),
            "Create .env.template file"
        )
        
        # Test configuration loading
        try:
            with open(config_file, 'r') as f:
                content = f.read()
            self._test(
                "Configuration file readable",
                len(content) > 0,
                "Configuration file appears to be empty"
            )
        except Exception as e:
            self._test("Configuration file readable", False, f"Error reading config: {e}")
    
    def _verify_analysis_engine(self):
        """Verify code analysis components."""
        analysis_files = [
            "pr_review_agent/analyzers/base.py",
            "pr_review_agent/analyzers/manager.py",
            "pr_review_agent/analyzers/__init__.py"
        ]
        
        for file_path in analysis_files:
            full_path = self.project_root / file_path
            self._test(
                f"Analysis file: {Path(file_path).name}",
                full_path.exists() and full_path.stat().st_size > 100,
                f"File missing or too small: {file_path}"
            )
        
        # Test analysis functionality using demo
        try:
            result = subprocess.run(
                ["python", "standalone_cli.py", "analyze", "--files", "README.md"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=10
            )
            self._test(
                "Analysis engine execution",
                result.returncode == 0 and "Analysis completed" in result.stdout,
                "Analysis command failed or didn't complete properly"
            )
        except Exception as e:
            self._test("Analysis engine execution", False, f"Error: {e}")
    
    def _verify_ai_integration(self):
        """Verify AI integration components."""
        ai_files = [
            "pr_review_agent/core/ai_feedback.py"
        ]
        
        for file_path in ai_files:
            full_path = self.project_root / file_path
            self._test(
                f"AI component: {Path(file_path).name}",
                full_path.exists() and full_path.stat().st_size > 500,
                f"File missing or too small: {file_path}"
            )
        
        # Test AI feedback generation using demo
        try:
            result = subprocess.run(
                ["python", "standalone_cli.py", "review", "--server", "github", "--repo", "test/repo", "--pr", "1"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=15
            )
            self._test(
                "AI feedback generation",
                result.returncode == 0 and "AI Feedback" in result.stdout,
                "AI feedback generation failed"
            )
        except Exception as e:
            self._test("AI feedback generation", False, f"Error: {e}")
    
    def _verify_scoring_system(self):
        """Verify scoring system."""
        scorer_file = self.project_root / "pr_review_agent" / "core" / "scorer.py"
        
        self._test(
            "Scorer module exists",
            scorer_file.exists() and scorer_file.stat().st_size > 500,
            "Scorer module missing or too small"
        )
        
        # Test scoring functionality
        try:
            result = subprocess.run(
                ["python", "standalone_cli.py", "review", "--server", "github", "--repo", "test/repo", "--pr", "1"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=15
            )
            
            has_scores = any(keyword in result.stdout for keyword in [
                "Overall Score", "Grade:", "Security:", "Performance:"
            ])
            
            self._test(
                "Scoring system execution",
                result.returncode == 0 and has_scores,
                "Scoring system didn't generate expected output"
            )
        except Exception as e:
            self._test("Scoring system execution", False, f"Error: {e}")
    
    def _verify_adapters(self):
        """Verify git server adapters."""
        adapter_files = [
            "pr_review_agent/adapters/base.py",
            "pr_review_agent/adapters/github.py",
            "pr_review_agent/adapters/gitlab.py",
            "pr_review_agent/adapters/bitbucket.py"
        ]
        
        for file_path in adapter_files:
            full_path = self.project_root / file_path
            self._test(
                f"Adapter: {Path(file_path).stem}",
                full_path.exists() and full_path.stat().st_size > 300,
                f"Adapter file missing or too small: {file_path}"
            )
        
        # Test adapter system
        for server in ["github", "gitlab", "bitbucket"]:
            try:
                result = subprocess.run(
                    ["python", "standalone_cli.py", "review", "--server", server, "--repo", "test/repo", "--pr", "1"],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                self._test(
                    f"Adapter functionality: {server}",
                    result.returncode == 0,
                    f"{server} adapter failed"
                )
            except Exception as e:
                self._test(f"Adapter functionality: {server}", False, f"Error: {e}")
    
    def _verify_documentation(self):
        """Verify documentation completeness."""
        doc_files = [
            ("README.md", 1000),
            ("CONTRIBUTING.md", 500),
            ("SECURITY.md", 500),
            ("HOW_TO_RUN.md", 500),
            ("CHANGELOG.md", 200)
        ]
        
        for file_path, min_size in doc_files:
            full_path = self.project_root / file_path
            self._test(
                f"Documentation: {file_path}",
                full_path.exists() and full_path.stat().st_size > min_size,
                f"Documentation missing or too small: {file_path}"
            )
        
        # Check README content
        readme_path = self.project_root / "README.md"
        if readme_path.exists():
            try:
                content = readme_path.read_text()
                required_sections = ["Installation", "Usage", "Features", "Examples"]
                for section in required_sections:
                    self._test(
                        f"README section: {section}",
                        section.lower() in content.lower(),
                        f"README missing {section} section"
                    )
            except Exception as e:
                self._test("README content check", False, f"Error reading README: {e}")
    
    def _verify_tests(self):
        """Verify test suite."""
        test_files = [
            "tests/__init__.py",
            "tests/conftest.py",
            "tests/run_tests.py",
            "tests/test_integration.py",
            "tests/unit/test_config.py",
            "tests/unit/test_reviewer.py",
            "tests/unit/test_adapters.py",
            "tests/unit/test_analyzers.py",
            "tests/unit/test_scorer.py",
            "tests/unit/test_cli.py"
        ]
        
        for file_path in test_files:
            full_path = self.project_root / file_path
            self._test(
                f"Test file: {Path(file_path).name}",
                full_path.exists() and full_path.stat().st_size > 50,
                f"Test file missing or empty: {file_path}"
            )
        
        # Test the demo functionality
        try:
            result = subprocess.run(
                ["python", "demo.py"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=10
            )
            self._test(
                "Demo script execution",
                result.returncode == 0 and "Demo completed" in result.stdout,
                "Demo script failed to run properly"
            )
        except Exception as e:
            self._test("Demo script execution", False, f"Error: {e}")
    
    def _generate_report(self) -> bool:
        """Generate verification report."""
        print(f"\n📊 Verification Results")
        print("=" * 60)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"✅ Tests Passed: {self.passed_tests}")
        print(f"❌ Tests Failed: {len(self.failed_tests)}")
        print(f"📊 Total Tests: {self.total_tests}")
        print(f"🎯 Success Rate: {success_rate:.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ Failed Tests:")
            for test in self.failed_tests:
                print(f"  • {test}")
            print(f"\n💡 Recommendations:")
            if any("import" in test.lower() for test in self.failed_tests):
                print("  • Install missing dependencies: pip install -r requirements.txt")
            if any("file" in test.lower() for test in self.failed_tests):
                print("  • Check file permissions and project structure")
            if any("cli" in test.lower() for test in self.failed_tests):
                print("  • Verify Python path and CLI functionality")
        
        if success_rate >= 90:
            print(f"\n🎉 EXCELLENT! Your PR Review Agent is working perfectly!")
            print(f"🏆 Ready for hackathon presentation and production use!")
        elif success_rate >= 75:
            print(f"\n✅ GOOD! Your PR Review Agent is mostly working.")
            print(f"🔧 Fix the failed tests for optimal performance.")
        elif success_rate >= 50:
            print(f"\n⚠️  PARTIAL! Your PR Review Agent has some issues.")
            print(f"🛠️  Address the failed tests to improve functionality.")
        else:
            print(f"\n❌ NEEDS WORK! Multiple issues found.")
            print(f"🔨 Focus on fixing the core functionality first.")
        
        return success_rate >= 75

def main():
    """Main verification function."""
    verifier = VerificationSuite()
    success = verifier.run_verification()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()