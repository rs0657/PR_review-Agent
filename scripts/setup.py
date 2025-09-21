#!/usr/bin/env python3
"""
Quick Setup Script for PR Review Agent

This script helps set up the development environment and validates the installation.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def run_command(command: str, description: str) -> bool:
    """Run a command and return success status."""
    print(f"🔄 {description}...")
    try:
        if platform.system() == "Windows":
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        else:
            result = subprocess.run(command.split(), check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stdout:
            print(f"STDOUT: {e.stdout}")
        if e.stderr:
            print(f"STDERR: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible."""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major != 3 or version.minor < 8:
        print(f"❌ Python 3.8+ required, found {version.major}.{version.minor}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def setup_virtual_environment():
    """Set up virtual environment."""
    if os.path.exists("venv"):
        print("✅ Virtual environment already exists")
        return True
    
    return run_command(
        f"{sys.executable} -m venv venv",
        "Creating virtual environment"
    )

def install_dependencies():
    """Install project dependencies."""
    if platform.system() == "Windows":
        pip_cmd = "venv\\Scripts\\pip"
    else:
        pip_cmd = "venv/bin/pip"
    
    commands = [
        (f"{pip_cmd} install --upgrade pip", "Upgrading pip"),
        (f"{pip_cmd} install -r requirements.txt", "Installing requirements"),
        (f"{pip_cmd} install -e .", "Installing package in development mode"),
    ]
    
    for command, description in commands:
        if not run_command(command, description):
            return False
    
    return True

def run_tests():
    """Run the test suite."""
    if platform.system() == "Windows":
        python_cmd = "venv\\Scripts\\python"
    else:
        python_cmd = "venv/bin/python"
    
    return run_command(
        f"{python_cmd} -m pytest tests/ -v",
        "Running tests"
    )

def validate_installation():
    """Validate the installation."""
    if platform.system() == "Windows":
        python_cmd = "venv\\Scripts\\python"
    else:
        python_cmd = "venv/bin/python"
    
    commands = [
        (f"{python_cmd} -c \"import pr_review_agent; print('✅ Package import successful')\"", 
         "Testing package import"),
        (f"{python_cmd} scripts/validate_structure.py", 
         "Validating project structure"),
    ]
    
    for command, description in commands:
        if not run_command(command, description):
            return False
    
    return True

def main():
    """Main setup function."""
    print("🚀 PR Review Agent - Quick Setup")
    print("=" * 40)
    
    # Change to project directory
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    print(f"📁 Working in: {project_root}")
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Setup steps
    steps = [
        ("Virtual Environment", setup_virtual_environment),
        ("Dependencies", install_dependencies),
        ("Installation Validation", validate_installation),
    ]
    
    for step_name, step_func in steps:
        print(f"\n📋 Step: {step_name}")
        if not step_func():
            print(f"❌ Setup failed at step: {step_name}")
            sys.exit(1)
    
    # Optional: Run tests
    print(f"\n📋 Optional: Running Tests")
    if run_tests():
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed, but setup is complete")
    
    print("\n🎉 Setup completed successfully!")
    print("\n📚 Next steps:")
    print("1. Copy .env.template to .env and configure your API keys")
    print("2. Run 'pr-review --help' to see available commands")
    print("3. Try 'pr-review status' to check configuration")
    
    # Activation instructions
    if platform.system() == "Windows":
        print("4. Activate virtual environment: venv\\Scripts\\activate")
    else:
        print("4. Activate virtual environment: source venv/bin/activate")

if __name__ == "__main__":
    main()
