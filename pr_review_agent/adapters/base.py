"""
Base adapter interface for git servers
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class PRInfo:
    """Pull Request information"""
    id: str
    number: int
    title: str
    description: str
    author: str
    source_branch: str
    target_branch: str
    status: str  # open, closed, merged
    created_at: datetime
    updated_at: datetime
    url: str
    repository: str
    files_changed: List[str]
    additions: int
    deletions: int
    commits: int


@dataclass
class FileChange:
    """Represents a changed file in a PR"""
    filename: str
    status: str  # added, modified, deleted, renamed
    additions: int
    deletions: int
    patch: str
    content_before: Optional[str] = None
    content_after: Optional[str] = None


@dataclass
class ReviewComment:
    """Represents a review comment"""
    file_path: str
    line_number: Optional[int]
    message: str
    severity: str  # info, warning, error
    suggestion: Optional[str] = None
    category: str = "general"  # security, performance, style, etc.


@dataclass
class ReviewSummary:
    """Summary of PR review"""
    overall_score: float
    comments: List[ReviewComment]
    summary_message: str
    recommendation: str  # approve, request_changes, comment


class GitServerAdapter(ABC):
    """Abstract base class for git server adapters"""
    
    def __init__(self, base_url: str, token: str, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.timeout = timeout
    
    @abstractmethod
    def get_pr_info(self, repository: str, pr_number: int) -> PRInfo:
        """Get pull request information"""
        pass
    
    @abstractmethod
    def get_pr_files(self, repository: str, pr_number: int) -> List[FileChange]:
        """Get list of changed files in a pull request"""
        pass
    
    @abstractmethod
    def get_file_content(self, repository: str, file_path: str, ref: str) -> str:
        """Get content of a file at a specific commit/branch"""
        pass
    
    @abstractmethod
    def post_review(self, repository: str, pr_number: int, review: ReviewSummary) -> bool:
        """Post a review to the pull request"""
        pass
    
    @abstractmethod
    def post_inline_comment(self, repository: str, pr_number: int, comment: ReviewComment) -> bool:
        """Post an inline comment to a specific line"""
        pass
    
    @abstractmethod
    def update_pr_status(self, repository: str, pr_number: int, status: str, description: str) -> bool:
        """Update PR status check"""
        pass
    
    def validate_connection(self) -> bool:
        """Validate connection to the git server"""
        try:
            return self._test_connection()
        except Exception:
            return False
    
    @abstractmethod
    def _test_connection(self) -> bool:
        """Test connection implementation"""
        pass
    
    def _get_headers(self) -> Dict[str, str]:
        """Get common headers for API requests"""
        return {
            'Authorization': f'Bearer {self.token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    
    def _handle_api_error(self, response) -> None:
        """Handle API error responses"""
        if response.status_code == 401:
            raise Exception("Authentication failed. Please check your token.")
        elif response.status_code == 403:
            raise Exception("Access forbidden. Check your permissions.")
        elif response.status_code == 404:
            raise Exception("Resource not found.")
        elif response.status_code >= 400:
            raise Exception(f"API error: {response.status_code} - {response.text}")


class AdapterFactory:
    """Factory for creating git server adapters"""
    
    _adapters = {}
    
    @classmethod
    def register_adapter(cls, server_type: str, adapter_class):
        """Register an adapter class for a server type"""
        cls._adapters[server_type] = adapter_class
    
    @classmethod
    def create_adapter(cls, server_type: str, base_url: str, token: str, **kwargs) -> GitServerAdapter:
        """Create an adapter instance for the specified server type"""
        if server_type not in cls._adapters:
            raise ValueError(f"Unsupported server type: {server_type}")
        
        adapter_class = cls._adapters[server_type]
        return adapter_class(base_url, token, **kwargs)
    
    @classmethod
    def get_supported_servers(cls) -> List[str]:
        """Get list of supported server types"""
        return list(cls._adapters.keys())
