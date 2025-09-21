"""Tests for CLI module."""

import pytest
from unittest.mock import patch, Mock, MagicMock
from click.testing import CliRunner

from pr_review_agent.cli import main, review, analyze, configure, status
from pr_review_agent.core.config import Config
from pr_review_agent.adapters.base import ReviewSummary


class TestCLI:
    """Test CLI commands."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    def test_main_help(self):
        """Test main command help."""
        result = self.runner.invoke(main, ['--help'])
        
        assert result.exit_code == 0
        assert 'PR Review Agent' in result.output
        assert 'review' in result.output
        assert 'analyze' in result.output
        assert 'configure' in result.output
        assert 'status' in result.output
    
    @patch('pr_review_agent.cli.PRReviewer')
    @patch('pr_review_agent.cli.ConfigManager.load_from_file')
    def test_review_command_success(self, mock_load_config, mock_reviewer_class):
        """Test successful review command."""
        # Mock config
        mock_config = Config(github_token="test_token")
        mock_load_config.return_value = mock_config
        
        # Mock reviewer
        mock_reviewer = Mock()
        mock_reviewer_class.return_value = mock_reviewer
        
        # Mock review result
        mock_summary = ReviewSummary(
            overall_score=85,
            grade='B',
            feedback="Good code!",
            file_analyses={},
            recommendations=[]
        )
        mock_reviewer.review_pr.return_value = mock_summary
        
        result = self.runner.invoke(review, [
            '--server', 'github',
            '--repo', 'owner/repo', 
            '--pr', '123'
        ])
        
        assert result.exit_code == 0
        assert 'Review completed successfully!' in result.output
        assert 'Overall Score: 85' in result.output
        assert 'Grade: B' in result.output
        
        mock_reviewer.review_pr.assert_called_once_with('github', 'owner/repo', 123)
    
    @patch('pr_review_agent.cli.PRReviewer')
    @patch('pr_review_agent.cli.ConfigManager.load_from_file')
    def test_review_command_missing_repo(self, mock_load_config, mock_reviewer_class):
        """Test review command with missing repo parameter."""
        result = self.runner.invoke(review, [
            '--server', 'github',
            '--pr', '123'
        ])
        
        assert result.exit_code != 0
        assert 'Missing option' in result.output or 'Usage:' in result.output
    
    @patch('pr_review_agent.cli.PRReviewer')
    @patch('pr_review_agent.cli.ConfigManager.load_from_file')
    def test_review_command_error(self, mock_load_config, mock_reviewer_class):
        """Test review command with error."""
        # Mock config
        mock_config = Config(github_token="test_token")
        mock_load_config.return_value = mock_config
        
        # Mock reviewer with error
        mock_reviewer = Mock()
        mock_reviewer_class.return_value = mock_reviewer
        mock_reviewer.review_pr.side_effect = Exception("API Error")
        
        result = self.runner.invoke(review, [
            '--server', 'github',
            '--repo', 'owner/repo',
            '--pr', '123'
        ])
        
        assert result.exit_code != 0
        assert 'Error during review' in result.output
        assert 'API Error' in result.output
    
    @patch('pr_review_agent.cli.PRReviewer')
    @patch('pr_review_agent.cli.ConfigManager.load_from_file') 
    def test_analyze_command_success(self, mock_load_config, mock_reviewer_class):
        """Test successful analyze command."""
        # Mock config
        mock_config = Config()
        mock_load_config.return_value = mock_config
        
        # Mock reviewer
        mock_reviewer = Mock()
        mock_reviewer_class.return_value = mock_reviewer
        
        # Mock analysis result
        from pr_review_agent.analyzers.base import AnalysisResult
        mock_result = AnalysisResult(
            file_path="test.py",
            issues=[],
            metrics={'complexity': 1},
            suggestions=[]
        )
        mock_reviewer.analysis_manager.analyze_file.return_value = mock_result
        
        # Create a temporary file
        with self.runner.isolated_filesystem():
            with open('test.py', 'w') as f:
                f.write('def test(): pass')
            
            result = self.runner.invoke(analyze, ['--files', 'test.py'])
            
            assert result.exit_code == 0
            assert 'Analysis completed' in result.output
            assert 'test.py' in result.output
    
    def test_analyze_command_missing_files(self):
        """Test analyze command with missing files parameter."""
        result = self.runner.invoke(analyze, [])
        
        assert result.exit_code != 0
        assert 'Missing option' in result.output or 'Usage:' in result.output
    
    @patch('pr_review_agent.cli.ConfigManager.load_from_file')
    def test_analyze_command_file_not_found(self, mock_load_config):
        """Test analyze command with non-existent file."""
        mock_config = Config()
        mock_load_config.return_value = mock_config
        
        result = self.runner.invoke(analyze, ['--files', 'nonexistent.py'])
        
        assert result.exit_code != 0
        assert 'not found' in result.output.lower()
    
    @patch('pr_review_agent.cli.ConfigManager.load_from_file')
    @patch('pr_review_agent.cli.ConfigManager.save_to_file')
    def test_configure_command_success(self, mock_save_config, mock_load_config):
        """Test successful configure command."""
        # Mock existing config
        mock_config = Config()
        mock_load_config.return_value = mock_config
        
        result = self.runner.invoke(configure, [
            '--github-token', 'new_github_token',
            '--openai-key', 'new_openai_key',
            '--ai-provider', 'huggingface'
        ])
        
        assert result.exit_code == 0
        assert 'Configuration updated successfully' in result.output
        
        # Verify save was called
        mock_save_config.assert_called_once()
        saved_config = mock_save_config.call_args[0][0]
        assert saved_config.github_token == 'new_github_token'
        assert saved_config.openai_api_key == 'new_openai_key'
        assert saved_config.ai_provider == 'huggingface'
    
    @patch('pr_review_agent.cli.ConfigManager.load_from_file')
    @patch('builtins.input')
    def test_configure_command_interactive(self, mock_input, mock_load_config):
        """Test interactive configure command."""
        # Mock existing config
        mock_config = Config()
        mock_load_config.return_value = mock_config
        
        # Mock user inputs
        mock_input.side_effect = [
            'new_github_token',  # GitHub token
            'new_openai_key',    # OpenAI key
            'huggingface',       # AI provider
            'y'                  # Save confirmation
        ]
        
        with patch('pr_review_agent.cli.ConfigManager.save_to_file') as mock_save:
            result = self.runner.invoke(configure, ['--interactive'])
            
            assert result.exit_code == 0
            assert 'Configuration updated successfully' in result.output
            mock_save.assert_called_once()
    
    @patch('pr_review_agent.cli.ConfigManager.load_from_file')
    def test_status_command_success(self, mock_load_config):
        """Test successful status command."""
        # Mock config with some values
        mock_config = Config(
            github_token="gh_token",
            openai_api_key="openai_key",
            ai_provider="openai"
        )
        mock_load_config.return_value = mock_config
        
        result = self.runner.invoke(status)
        
        assert result.exit_code == 0
        assert 'System Status' in result.output
        assert 'GitHub Token: ✓ Configured' in result.output
        assert 'OpenAI API Key: ✓ Configured' in result.output
        assert 'AI Provider: openai' in result.output
    
    @patch('pr_review_agent.cli.ConfigManager.load_from_file')
    def test_status_command_missing_config(self, mock_load_config):
        """Test status command with missing configuration."""
        # Mock config with missing values
        mock_config = Config()  # Default empty config
        mock_load_config.return_value = mock_config
        
        result = self.runner.invoke(status)
        
        assert result.exit_code == 0
        assert 'System Status' in result.output
        assert 'GitHub Token: ✗ Not configured' in result.output
        assert 'OpenAI API Key: ✗ Not configured' in result.output
    
    @patch('pr_review_agent.cli.ConfigManager.load_from_file')
    def test_config_loading_error(self, mock_load_config):
        """Test CLI handles config loading errors gracefully."""
        mock_load_config.side_effect = Exception("Config error")
        
        result = self.runner.invoke(status)
        
        assert result.exit_code != 0
        assert 'Error loading configuration' in result.output
    
    def test_invalid_server_option(self):
        """Test review command with invalid server option."""
        result = self.runner.invoke(review, [
            '--server', 'invalid_server',
            '--repo', 'owner/repo',
            '--pr', '123'
        ])
        
        assert result.exit_code != 0
        assert 'Invalid value' in result.output or 'not supported' in result.output.lower()
    
    def test_invalid_pr_number(self):
        """Test review command with invalid PR number."""
        result = self.runner.invoke(review, [
            '--server', 'github',
            '--repo', 'owner/repo',
            '--pr', 'invalid'
        ])
        
        assert result.exit_code != 0
        assert 'Invalid value' in result.output
    
    @patch('pr_review_agent.cli.PRReviewer')
    @patch('pr_review_agent.cli.ConfigManager.load_from_file')
    def test_review_with_config_file(self, mock_load_config, mock_reviewer_class):
        """Test review command with custom config file."""
        mock_config = Config(github_token="test_token")
        mock_load_config.return_value = mock_config
        
        mock_reviewer = Mock()
        mock_reviewer_class.return_value = mock_reviewer
        mock_reviewer.review_pr.return_value = Mock(
            overall_score=90,
            grade='A',
            feedback="Excellent!",
            file_analyses={},
            recommendations=[]
        )
        
        result = self.runner.invoke(review, [
            '--server', 'github',
            '--repo', 'owner/repo',
            '--pr', '123',
            '--config', '/custom/config.yaml'
        ])
        
        assert result.exit_code == 0
        mock_load_config.assert_called_with('/custom/config.yaml')
    
    @patch('pr_review_agent.cli.PRReviewer')
    @patch('pr_review_agent.cli.ConfigManager.load_from_file')
    def test_review_verbose_output(self, mock_load_config, mock_reviewer_class):
        """Test review command with verbose output."""
        mock_config = Config(github_token="test_token")
        mock_load_config.return_value = mock_config
        
        mock_reviewer = Mock()
        mock_reviewer_class.return_value = mock_reviewer
        
        # Mock detailed review result
        from pr_review_agent.analyzers.base import AnalysisResult
        analysis_result = AnalysisResult(
            file_path="test.py",
            issues=[{"type": "warning", "message": "Test warning"}],
            metrics={"complexity": 5},
            suggestions=["Add docstring"]
        )
        
        mock_summary = ReviewSummary(
            overall_score=75,
            grade='B-',
            feedback="Good with improvements",
            file_analyses={"test.py": analysis_result},
            recommendations=["Reduce complexity"]
        )
        mock_reviewer.review_pr.return_value = mock_summary
        
        result = self.runner.invoke(review, [
            '--server', 'github',
            '--repo', 'owner/repo',
            '--pr', '123',
            '--verbose'
        ])
        
        assert result.exit_code == 0
        assert 'File Analysis Details' in result.output
        assert 'test.py' in result.output
        assert 'Test warning' in result.output
        assert 'Add docstring' in result.output
