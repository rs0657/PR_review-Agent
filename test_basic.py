#!/usr/bin/env python3
"""
Basic test script to validate the PR Review Agent structure
without requiring all dependencies.
"""
import sys
import os
from pathlib import Path

def test_import_structure():
    """Test if the basic package structure can be imported."""
    print("🧪 Testing package structure...")
    
    # Add the current directory to Python path
    sys.path.insert(0, str(Path(__file__).parent))
    
    try:
        # Test basic config import
        from pr_review_agent.core.config import Config
        print("  ✅ Core config module imported successfully")
        
        # Test if we can create a basic config
        config = Config()
        print("  ✅ Config object created successfully")
        
        # Test CLI structure (without running it)
        import pr_review_agent.cli
        print("  ✅ CLI module imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Other error: {e}")
        return False

def test_config_loading():
    """Test configuration loading."""
    print("\n⚙️  Testing configuration...")
    
    try:
        from pr_review_agent.core.config import Config
        
        # Test if config file exists
        config_path = Path("config/pr_review_config.yaml")
        if config_path.exists():
            print(f"  ✅ Config file found: {config_path}")
        else:
            print(f"  ⚠️  Config file not found: {config_path}")
        
        # Test basic config creation
        config = Config()
        print("  ✅ Config instance created")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Config test failed: {e}")
        return False

def test_project_structure():
    """Test if all required project files exist."""
    print("\n📁 Testing project structure...")
    
    required_files = [
        "pyproject.toml",
        "README.md",
        "LICENSE",
        "requirements.txt",
        ".gitignore",
        "pr_review_agent/__init__.py",
        "pr_review_agent/cli.py",
        "pr_review_agent/core/__init__.py",
        "pr_review_agent/core/config.py",
        "tests/__init__.py"
    ]
    
    all_good = True
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} - MISSING")
            all_good = False
    
    return all_good

def main():
    """Run all basic tests."""
    print("🔍 PR Review Agent - Basic Functionality Test")
    print("=" * 50)
    
    tests = [
        ("Project Structure", test_project_structure),
        ("Import Structure", test_import_structure),
        ("Configuration", test_config_loading),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    print("\n📊 Test Results Summary")
    print("=" * 30)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\nPassed: {passed}/{len(results)} tests")
    
    if passed == len(results):
        print("\n🎉 All basic tests passed! The project structure is solid.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())