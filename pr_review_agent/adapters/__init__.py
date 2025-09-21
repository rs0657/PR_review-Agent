"""
Adapter package initialization
Import all adapters to register them with the factory
"""

from .base import GitServerAdapter, AdapterFactory
from .github import GitHubAdapter
from .gitlab import GitLabAdapter
from .bitbucket import BitbucketAdapter

__all__ = [
    "GitServerAdapter", 
    "AdapterFactory",
    "GitHubAdapter",
    "GitLabAdapter", 
    "BitbucketAdapter"
]
