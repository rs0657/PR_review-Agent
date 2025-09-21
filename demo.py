#!/usr/bin/env python3
"""
PR Review Agent Demo

This demo script shows the core functionality of the PR Review Agent
without requiring external dependencies.
"""

import sys
import json
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def demo_basic_functionality():
    """Demonstrate basic PR Review Agent functionality."""
    print("🚀 PR Review Agent Demo")
    print("=" * 50)
    
    # Simulate configuration
    print("\n📋 1. Configuration Demo")
    print("✅ GitHub Token: Configured")
    print("✅ AI Provider: OpenAI (Demo Mode)")
    print("✅ Analysis Enabled: Security, Performance, Structure")
    
    # Simulate file analysis
    print("\n📊 2. Code Analysis Demo")
    sample_files = [
        {
            "path": "src/main.py",
            "issues": [
                {"type": "security", "severity": "medium", "message": "Potential SQL injection vulnerability"},
                {"type": "performance", "severity": "low", "message": "Consider using list comprehension"}
            ],
            "metrics": {"complexity": 8, "lines": 150, "functions": 5}
        },
        {
            "path": "src/utils.py", 
            "issues": [
                {"type": "style", "severity": "low", "message": "Missing docstring"}
            ],
            "metrics": {"complexity": 3, "lines": 45, "functions": 2}
        }
    ]
    
    for file_info in sample_files:
        print(f"\n📄 Analyzing {file_info['path']}:")
        print(f"  📏 Lines: {file_info['metrics']['lines']}")
        print(f"  🔧 Functions: {file_info['metrics']['functions']}")
        print(f"  📊 Complexity: {file_info['metrics']['complexity']}")
        
        if file_info['issues']:
            print("  ⚠️  Issues found:")
            for issue in file_info['issues']:
                severity_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}
                emoji = severity_emoji.get(issue['severity'], "🔵")
                print(f"    {emoji} {issue['type'].title()}: {issue['message']}")
        else:
            print("  ✅ No issues found")
    
    # Simulate AI feedback
    print("\n🤖 3. AI Feedback Demo")
    ai_feedback = """
**Overall Assessment:** This pull request shows good code structure but has some areas for improvement.

**Security Concerns:**
- Found potential SQL injection vulnerability in main.py line 42
- Recommend using parameterized queries

**Performance Suggestions:**
- Consider optimizing the data processing loop in main.py
- List comprehension could improve readability and performance

**Code Quality:**
- Good function organization and naming conventions
- Missing documentation in some functions
- Consider adding type hints for better maintainability

**Recommendations:**
1. Fix the SQL injection vulnerability (High Priority)
2. Add missing docstrings 
3. Consider refactoring complex functions
4. Add unit tests for new functionality
"""
    
    print(ai_feedback)
    
    # Simulate scoring
    print("\n📈 4. Scoring Demo")
    scores = {
        "Security": 75,
        "Performance": 85, 
        "Structure": 90,
        "Style": 80
    }
    
    total_score = sum(scores.values()) / len(scores)
    
    print("Category Scores:")
    for category, score in scores.items():
        bar = "█" * (score // 5) + "░" * (20 - score // 5)
        print(f"  {category:12} [{bar}] {score}%")
    
    print(f"\n🎯 Overall Score: {total_score:.1f}/100")
    
    # Determine grade
    if total_score >= 90:
        grade = "A+"
    elif total_score >= 85:
        grade = "A"
    elif total_score >= 80:
        grade = "B+"
    elif total_score >= 75:
        grade = "B"
    elif total_score >= 70:
        grade = "B-"
    else:
        grade = "C"
    
    print(f"🏆 Grade: {grade}")
    
    # Simulate CLI commands
    print("\n💻 5. CLI Commands Demo")
    commands = [
        "pr-review --help",
        "pr-review status",
        "pr-review review --server github --repo owner/repo --pr 123",
        "pr-review analyze --files src/main.py src/utils.py",
        "pr-review configure --interactive"
    ]
    
    print("Available commands:")
    for cmd in commands:
        print(f"  $ {cmd}")
    
    print("\n✨ Demo completed! The PR Review Agent is ready to use.")
    print("\n📚 Next Steps:")
    print("1. Set up your API keys in .env file")
    print("2. Install dependencies: pip install -r requirements.txt")
    print("3. Run: python -m pr_review_agent.cli --help")

def demo_package_structure():
    """Show the package structure."""
    print("\n📁 Package Structure:")
    structure = """
pr-review-agent/
├── pr_review_agent/          # Main package
│   ├── core/                 # Core functionality
│   │   ├── config.py        # Configuration management
│   │   ├── reviewer.py      # Main review orchestrator
│   │   ├── ai_feedback.py   # AI providers
│   │   └── scorer.py        # Scoring system
│   ├── adapters/            # Git server adapters
│   │   ├── github.py        # GitHub integration
│   │   ├── gitlab.py        # GitLab integration
│   │   └── bitbucket.py     # Bitbucket integration
│   ├── analyzers/           # Code analyzers
│   │   ├── base.py          # Base analyzer classes
│   │   └── manager.py       # Analysis coordination
│   └── cli.py               # Command-line interface
├── tests/                   # Test suite
├── config/                  # Configuration files
└── docs/                    # Documentation
"""
    print(structure)

if __name__ == "__main__":
    demo_basic_functionality()
    demo_package_structure()