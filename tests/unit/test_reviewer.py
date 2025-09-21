"""Tests for core reviewer module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from pr_review_agent.core.reviewer import PRReviewer
from pr_review_agent.core.config import Config
from pr_review_agent.adapters.base import PRInfo, FileChange, ReviewSummary
from pr_review_agent.analyzers.base import AnalysisResult


class TestPRReviewer:
    """Test PRReviewer class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = Config(
            github_token="test_token",
            openai_api_key="test_key"
        )
        self.reviewer = PRReviewer(self.config)
    
    def test_initialization(self):
        """Test PRReviewer initialization."""
        assert self.reviewer.config == self.config
        assert self.reviewer.adapter is None
        assert self.reviewer.feedback_manager is not None
        assert self.reviewer.analysis_manager is not None
        assert self.reviewer.scorer is not None
    
    @patch('pr_review_agent.adapters.base.AdapterFactory.create_adapter')
    def test_setup_adapter_github(self, mock_create_adapter):
        """Test setting up GitHub adapter."""
        mock_adapter = Mock()
        mock_create_adapter.return_value = mock_adapter
        
        self.reviewer.setup_adapter('github')
        
        assert self.reviewer.adapter == mock_adapter
        mock_create_adapter.assert_called_once_with('github', self.config)
    
    @patch('pr_review_agent.adapters.base.AdapterFactory.create_adapter')
    def test_setup_adapter_gitlab(self, mock_create_adapter):
        """Test setting up GitLab adapter."""
        mock_adapter = Mock()
        mock_create_adapter.return_value = mock_adapter
        
        self.reviewer.setup_adapter('gitlab')
        
        assert self.reviewer.adapter == mock_adapter
        mock_create_adapter.assert_called_once_with('gitlab', self.config)
    
    def test_setup_adapter_invalid(self):
        """Test setting up invalid adapter raises error."""
        with pytest.raises(ValueError, match="Unsupported git server"):
            self.reviewer.setup_adapter('invalid_server')
    
    @patch('pr_review_agent.core.reviewer.PRReviewer.setup_adapter')
    def test_review_pr_success(self, mock_setup_adapter):
        """Test successful PR review."""
        # Mock adapter
        mock_adapter = Mock()
        mock_setup_adapter.return_value = None
        self.reviewer.adapter = mock_adapter
        
        # Mock PR info
        pr_info = PRInfo(
            title="Test PR",
            description="Test description",
            author="test_user",
            files_changed=[
                FileChange(
                    path="test.py",
                    content="def test(): pass",
                    change_type="modified",
                    additions=1,
                    deletions=0
                )
            ]
        )
        mock_adapter.get_pr_info.return_value = pr_info
        
        # Mock analysis results
        analysis_result = AnalysisResult(
            file_path="test.py",
            issues=[],
            metrics={'complexity': 1},
            suggestions=[]
        )
        
        with patch.object(self.reviewer.analysis_manager, 'analyze_files') as mock_analyze:
            with patch.object(self.reviewer.feedback_manager, 'generate_feedback') as mock_feedback:
                with patch.object(self.reviewer.scorer, 'calculate_score') as mock_score:
                    with patch.object(mock_adapter, 'post_review') as mock_post:
                        
                        mock_analyze.return_value = {'test.py': analysis_result}
                        mock_feedback.return_value = "Great code!"
                        mock_score.return_value = Mock(overall_score=85, grade='B')
                        
                        result = self.reviewer.review_pr('github', 'owner/repo', 123)
                        
                        assert isinstance(result, ReviewSummary)
                        assert result.overall_score == 85
                        assert result.grade == 'B'
                        
                        mock_adapter.get_pr_info.assert_called_once_with('owner/repo', 123)
                        mock_analyze.assert_called_once()
                        mock_feedback.assert_called_once()
                        mock_score.assert_called_once()
                        mock_post.assert_called_once()
    
    def test_review_pr_no_adapter(self):
        """Test review fails when no adapter is set up."""
        with pytest.raises(RuntimeError, match="No adapter configured"):
            self.reviewer.review_pr('github', 'owner/repo', 123)
    
    @patch('pr_review_agent.core.reviewer.PRReviewer.setup_adapter')
    def test_review_pr_adapter_error(self, mock_setup_adapter):
        """Test review handles adapter errors."""
        mock_adapter = Mock()
        mock_setup_adapter.return_value = None
        self.reviewer.adapter = mock_adapter
        
        mock_adapter.get_pr_info.side_effect = Exception("API Error")
        
        with pytest.raises(Exception, match="API Error"):
            self.reviewer.review_pr('github', 'owner/repo', 123)
    
    def test_analyze_files_success(self):
        """Test successful file analysis."""
        files = [
            FileChange(
                path="test1.py",
                content="def test1(): pass",
                change_type="added",
                additions=1,
                deletions=0
            ),
            FileChange(
                path="test2.js",
                content="function test2() {}",
                change_type="modified",
                additions=1,
                deletions=1
            )
        ]
        
        analysis_result1 = AnalysisResult(
            file_path="test1.py",
            issues=[],
            metrics={'complexity': 1},
            suggestions=[]
        )
        
        analysis_result2 = AnalysisResult(
            file_path="test2.js",
            issues=[],
            metrics={'complexity': 2},
            suggestions=[]
        )
        
        with patch.object(self.reviewer.analysis_manager, 'analyze_files') as mock_analyze:
            mock_analyze.return_value = {
                'test1.py': analysis_result1,
                'test2.js': analysis_result2
            }
            
            results = self.reviewer.analyze_files(files)
            
            assert len(results) == 2
            assert 'test1.py' in results
            assert 'test2.js' in results
            assert results['test1.py'] == analysis_result1
            assert results['test2.js'] == analysis_result2
    
    def test_analyze_files_empty(self):
        """Test analyzing empty file list."""
        results = self.reviewer.analyze_files([])
        
        assert results == {}
    
    def test_analyze_files_with_filtering(self):
        """Test file analysis with size filtering."""
        # Create a config with small max file size
        config = Config(max_file_size=10)
        reviewer = PRReviewer(config)
        
        files = [
            FileChange(
                path="small.py",
                content="def test(): pass",  # Small file
                change_type="added",
                additions=1,
                deletions=0
            ),
            FileChange(
                path="large.py", 
                content="def test(): pass" * 100,  # Large file
                change_type="added",
                additions=1,
                deletions=0
            )
        ]
        
        with patch.object(reviewer.analysis_manager, 'analyze_files') as mock_analyze:
            mock_analyze.return_value = {'small.py': Mock()}
            
            results = reviewer.analyze_files(files)
            
            # Only small file should be analyzed
            mock_analyze.assert_called_once()
            called_files = mock_analyze.call_args[0][0]
            assert len(called_files) == 1
            assert called_files[0].path == "small.py"
    
    @patch('pr_review_agent.core.reviewer.PRReviewer.setup_adapter')
    def test_generate_summary(self, mock_setup_adapter):
        """Test generating review summary."""
        mock_adapter = Mock()
        self.reviewer.adapter = mock_adapter
        
        pr_info = PRInfo(
            title="Test PR",
            description="Test description", 
            author="test_user",
            files_changed=[]
        )
        
        analysis_results = {
            'test.py': AnalysisResult(
                file_path='test.py',
                issues=[],
                metrics={'complexity': 1},
                suggestions=[]
            )
        }
        
        feedback = "Great code!"
        scorecard = Mock()
        scorecard.overall_score = 85
        scorecard.grade = 'B'
        scorecard.category_scores = {'security': 90, 'performance': 80}
        
        summary = self.reviewer._generate_summary(
            pr_info, analysis_results, feedback, scorecard
        )
        
        assert isinstance(summary, ReviewSummary)
        assert summary.overall_score == 85
        assert summary.grade == 'B'
        assert summary.feedback == feedback
        assert len(summary.file_analyses) == 1
        assert 'test.py' in summary.file_analyses
    
    def test_filter_files_by_size(self):
        """Test filtering files by size."""
        config = Config(max_file_size=20)
        reviewer = PRReviewer(config)
        
        files = [
            FileChange(path="small.py", content="short", change_type="added", additions=1, deletions=0),
            FileChange(path="large.py", content="a" * 50, change_type="added", additions=1, deletions=0),
        ]
        
        filtered = reviewer._filter_files(files)
        
        assert len(filtered) == 1
        assert filtered[0].path == "small.py"
    
    def test_filter_files_by_extension(self):
        """Test filtering files by extension."""
        config = Config(supported_extensions=['.py', '.js'])
        reviewer = PRReviewer(config)
        
        files = [
            FileChange(path="test.py", content="python", change_type="added", additions=1, deletions=0),
            FileChange(path="test.js", content="javascript", change_type="added", additions=1, deletions=0),
            FileChange(path="test.txt", content="text", change_type="added", additions=1, deletions=0),
        ]
        
        filtered = reviewer._filter_files(files)
        
        assert len(filtered) == 2
        assert any(f.path == "test.py" for f in filtered)
        assert any(f.path == "test.js" for f in filtered)
        assert not any(f.path == "test.txt" for f in filtered)
