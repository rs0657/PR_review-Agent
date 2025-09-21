#!/usr/bin/env python3
"""
Simple CLI test that demonstrates the application without heavy dependencies.
"""
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_cli_help():
    """Test CLI help functionality without importing everything."""
    print("🔧 Testing CLI functionality...")
    
    try:
        # Test if we can import the CLI module directly
        import pr_review_agent.cli as cli_module
        print("  ✅ CLI module exists")
        
        # Check if main function exists
        if hasattr(cli_module, 'main'):
            print("  ✅ Main function found")
        else:
            print("  ❌ Main function not found")
            
        # Check if click is available
        import click
        print("  ✅ Click dependency available")
        
        return True
        
    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        return False

def show_available_commands():
    """Show what commands would be available."""
    print("\n📋 Available Commands (when dependencies are installed):")
    print("  pr-review --help           - Show help")
    print("  pr-review review           - Review a pull request")
    print("  pr-review config           - Manage configuration")
    print("  pr-review status           - Show status")

def test_basic_config():
    """Test basic configuration without external dependencies."""
    print("\n⚙️  Testing basic configuration...")
    
    try:
        # Import just the config module
        from pr_review_agent.core.config import Config
        
        # Create a basic config
        config = Config()
        print("  ✅ Config created successfully")
        
        # Test if config file exists
        config_file = Path("config/pr_review_config.yaml")
        if config_file.exists():
            print(f"  ✅ Config file found: {config_file}")
        else:
            print(f"  ⚠️  Config file not found: {config_file}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Config test failed: {e}")
        return False

def main():
    """Main test function."""
    print("🚀 PR Review Agent - Lightweight Test")
    print("=" * 40)
    
    # Test basic functionality
    structure_ok = test_cli_help()
    config_ok = test_basic_config()
    
    show_available_commands()
    
    print("\n📊 Test Summary")
    print("=" * 20)
    
    if structure_ok and config_ok:
        print("✅ Basic structure is working!")
        print("\n💡 Next steps:")
        print("   1. Install dependencies: pip install pygithub python-gitlab")
        print("   2. Or use a virtual environment to avoid system conflicts")
        print("   3. Or use pipx: pipx install .")
        return 0
    else:
        print("❌ Some basic functionality issues found")
        return 1

if __name__ == "__main__":
    sys.exit(main())