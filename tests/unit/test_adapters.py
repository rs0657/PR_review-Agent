"""
Unit tests for git server adapters
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from pr_review_agent.adapters.base import AdapterFactory, PRInfo, FileChange, ReviewComment
from pr_review_agent.adapters.github import GitHubAdapter
from pr_review_agent.adapters.gitlab import GitLabAdapter
from pr_review_agent.adapters.bitbucket import BitbucketAdapter


class TestAdapterFactory:
    """Test adapter factory functionality"""
    
    def test_get_supported_servers(self):
        """Test getting list of supported servers"""
        supported = AdapterFactory.get_supported_servers()
        assert "github" in supported
        assert "gitlab" in supported
        assert "bitbucket" in supported
    
    def test_create_github_adapter(self):
        """Test creating GitHub adapter"""
        adapter = AdapterFactory.create_adapter(
            "github", 
            "https://api.github.com", 
            "test_token"
        )
        assert isinstance(adapter, GitHubAdapter)
    
    def test_create_gitlab_adapter(self):
        """Test creating GitLab adapter"""
        adapter = AdapterFactory.create_adapter(
            "gitlab", 
            "https://gitlab.com/api", 
            "test_token"
        )
        assert isinstance(adapter, GitLabAdapter)
    
    def test_create_bitbucket_adapter(self):
        """Test creating Bitbucket adapter"""
        adapter = AdapterFactory.create_adapter(
            "bitbucket", 
            "https://api.bitbucket.org", 
            "test_token"
        )
        assert isinstance(adapter, BitbucketAdapter)
    
    def test_unsupported_server_type(self):
        """Test error for unsupported server type"""
        with pytest.raises(ValueError):
            AdapterFactory.create_adapter(
                "unsupported", 
                "https://example.com", 
                "test_token"
            )


class TestGitHubAdapter:
    """Test GitHub adapter functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        with patch('pr_review_agent.adapters.github.Github'):
            self.adapter = GitHubAdapter(
                "https://api.github.com", 
                "test_token"
            )
    
    @patch('pr_review_agent.adapters.github.Github')
    def test_get_pr_info(self, mock_github):
        """Test getting PR information"""
        # Mock GitHub API response
        mock_pr = Mock()
        mock_pr.id = 123
        mock_pr.number = 1
        mock_pr.title = "Test PR"
        mock_pr.body = "Test description"
        mock_pr.user.login = "testuser"
        mock_pr.head.ref = "feature-branch"
        mock_pr.base.ref = "main"
        mock_pr.state = "open"
        mock_pr.created_at = "2023-01-01T00:00:00Z"
        mock_pr.updated_at = "2023-01-01T00:00:00Z"
        mock_pr.html_url = "https://github.com/owner/repo/pull/1"
        mock_pr.additions = 10
        mock_pr.deletions = 5
        mock_pr.commits = 3
        mock_pr.get_files.return_value = [Mock(filename="test.py")]
        
        mock_repo = Mock()
        mock_repo.get_pull.return_value = mock_pr
        
        mock_github_instance = Mock()
        mock_github_instance.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_instance
        
        adapter = GitHubAdapter("https://api.github.com", "test_token")
        pr_info = adapter.get_pr_info("owner/repo", 1)
        
        assert isinstance(pr_info, PRInfo)
        assert pr_info.id == "123"
        assert pr_info.number == 1
        assert pr_info.title == "Test PR"
        assert pr_info.author == "testuser"
    
    def test_get_headers(self):
        """Test getting request headers"""
        headers = self.adapter._get_headers()
        
        assert "Authorization" in headers
        assert "Bearer test_token" in headers["Authorization"]
        assert headers["Accept"] == "application/json"
        assert headers["Content-Type"] == "application/json"


class TestGitLabAdapter:
    """Test GitLab adapter functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.adapter = GitLabAdapter(
            "https://gitlab.com/api", 
            "test_token"
        )
    
    @patch('pr_review_agent.adapters.gitlab.requests.get')
    def test_get_pr_info(self, mock_get):
        """Test getting MR information"""
        # Mock GitLab API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": 123,
            "iid": 1,
            "title": "Test MR",
            "description": "Test description",
            "author": {"username": "testuser"},
            "source_branch": "feature-branch",
            "target_branch": "main",
            "state": "opened",
            "created_at": "2023-01-01T00:00:00.000Z",
            "updated_at": "2023-01-01T00:00:00.000Z",
            "web_url": "https://gitlab.com/owner/repo/-/merge_requests/1"
        }
        mock_get.return_value = mock_response
        
        # Mock the helper methods
        self.adapter._get_changed_files_list = Mock(return_value=["test.py"])
        self.adapter._get_mr_commits = Mock(return_value=[{"id": "abc123"}])
        
        pr_info = self.adapter.get_pr_info("owner/repo", 1)
        
        assert isinstance(pr_info, PRInfo)
        assert pr_info.id == "123"
        assert pr_info.number == 1
        assert pr_info.title == "Test MR"
        assert pr_info.author == "testuser"
    
    def test_get_project_id(self):
        """Test URL encoding of project ID"""
        project_id = self.adapter._get_project_id("owner/repo")
        assert project_id == "owner%2Frepo"


class TestBitbucketAdapter:
    """Test Bitbucket adapter functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.adapter = BitbucketAdapter(
            "https://api.bitbucket.org", 
            "test_token"
        )
    
    @patch('pr_review_agent.adapters.bitbucket.requests.get')
    def test_get_pr_info(self, mock_get):
        """Test getting PR information"""
        # Mock Bitbucket API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": 123,
            "title": "Test PR",
            "description": "Test description",
            "author": {"username": "testuser"},
            "source": {"branch": {"name": "feature-branch"}},
            "destination": {"branch": {"name": "main"}},
            "state": "OPEN",
            "created_on": "2023-01-01T00:00:00.000000+00:00",
            "updated_on": "2023-01-01T00:00:00.000000+00:00",
            "links": {"html": {"href": "https://bitbucket.org/owner/repo/pull-requests/123"}}
        }
        mock_get.return_value = mock_response
        
        # Mock the helper methods
        self.adapter._get_changed_files_list = Mock(return_value=["test.py"])
        self.adapter._get_pr_commits = Mock(return_value=[{"hash": "abc123"}])
        
        pr_info = self.adapter.get_pr_info("owner/repo", 123)
        
        assert isinstance(pr_info, PRInfo)
        assert pr_info.id == "123"
        assert pr_info.number == 123
        assert pr_info.title == "Test PR"
        assert pr_info.author == "testuser"


def test_pr_info_creation():
    """Test PRInfo dataclass creation"""
    from datetime import datetime
    
    pr_info = PRInfo(
        id="123",
        number=1,
        title="Test PR",
        description="Test description",
        author="testuser",
        source_branch="feature",
        target_branch="main",
        status="open",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        url="https://example.com/pr/1",
        repository="owner/repo",
        files_changed=["test.py"],
        additions=10,
        deletions=5,
        commits=3
    )
    
    assert pr_info.id == "123"
    assert pr_info.number == 1
    assert pr_info.title == "Test PR"
    assert len(pr_info.files_changed) == 1


def test_file_change_creation():
    """Test FileChange dataclass creation"""
    file_change = FileChange(
        filename="test.py",
        status="modified",
        additions=10,
        deletions=5,
        patch="@@ -1,3 +1,3 @@",
        content_before="old content",
        content_after="new content"
    )
    
    assert file_change.filename == "test.py"
    assert file_change.status == "modified"
    assert file_change.additions == 10
    assert file_change.deletions == 5


def test_review_comment_creation():
    """Test ReviewComment dataclass creation"""
    comment = ReviewComment(
        file_path="test.py",
        line_number=10,
        message="Test comment",
        severity="warning",
        suggestion="Fix this",
        category="style"
    )
    
    assert comment.file_path == "test.py"
    assert comment.line_number == 10
    assert comment.message == "Test comment"
    assert comment.severity == "warning"


if __name__ == "__main__":
    pytest.main([__file__])
