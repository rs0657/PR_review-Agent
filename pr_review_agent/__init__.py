"""PR Review Agent - AI-powered Pull Request Review Tool.

This package provides intelligent code review capabilities for pull requests
across multiple git hosting platforms (GitHub, GitLab, Bitbucket) using
AI-powered analysis and feedback generation.

Key Features:
- Multi-platform git server support
- AI-powered code analysis and feedback
- Configurable scoring system
- Security, performance, and structure analysis
- Rich command-line interface
- Extensible architecture

Example Usage:
    from pr_review_agent import PRReviewer, Config
    
    config = Config(github_token="your_token", openai_api_key="your_key")
    reviewer = PRReviewer(config)
    
    # Review a pull request
    result = reviewer.review_pr("github", "owner/repo", 123)
    print(f"Score: {result.overall_score}, Grade: {result.grade}")

For detailed documentation and examples, visit:
https://pr-review-agent.readthedocs.io/
"""

__version__ = "1.0.0"
__author__ = "PR Review Agent Team"
__email__ = "team@pr-review-agent.com"
__license__ = "MIT"

# Core exports for easy access
from .core.reviewer import PRReviewer
from .core.config import Config, ConfigManager
from .core.scorer import PRScorer, ScoreCard
from .core.ai_feedback import FeedbackManager

# Adapter exports
from .adapters.base import AdapterFactory, GitServerAdapter
from .adapters.github import GitHubAdapter
from .adapters.gitlab import GitLabAdapter
from .adapters.bitbucket import BitbucketAdapter

# Analyzer exports
from .analyzers.manager import AnalysisManager
from .analyzers.base import BaseAnalyzer, AnalysisResult

__all__ = [
    # Core classes
    "PRReviewer",
    "Config", 
    "ConfigManager",
    "PRScorer",
    "ScoreCard",
    "FeedbackManager",
    
    # Adapters
    "AdapterFactory",
    "GitServerAdapter", 
    "GitHubAdapter",
    "GitLabAdapter",
    "BitbucketAdapter",
    
    # Analyzers
    "AnalysisManager",
    "BaseAnalyzer",
    "AnalysisResult",
    
    # Package metadata
    "__version__",
    "__author__",
    "__email__",
    "__license__",
]
