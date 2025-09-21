"""
Integration tests for the complete PR review workflow
"""
import pytest
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from pr_review_agent.core.reviewer import PRReviewer


class TestPRReviewerIntegration:
    """Integration tests for PR Reviewer"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Create temporary config file
        self.config_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        config_content = """
servers:
  test_github:
    base_url: https://api.github.com
    token: test_token
    type: github
    timeout: 30

analysis:
  enabled_analyzers:
    - structure
    - security
  max_file_size: 1048576
  exclude_patterns:
    - "*.min.js"

ai:
  provider: openai
  model: gpt-4
  api_key: test_api_key
  temperature: 0.3

scoring:
  weights:
    code_quality: 0.3
    security: 0.3
    test_coverage: 0.2
    documentation: 0.1
    performance: 0.05
    maintainability: 0.05
"""
        self.config_file.write(config_content)
        self.config_file.close()
    
    def teardown_method(self):
        """Clean up test fixtures"""
        os.unlink(self.config_file.name)
    
    @patch('pr_review_agent.adapters.github.Github')
    @patch('pr_review_agent.core.ai_feedback.openai.OpenAI')
    def test_complete_review_workflow(self, mock_openai, mock_github):
        """Test complete PR review workflow"""
        # Mock GitHub API
        mock_pr = Mock()
        mock_pr.id = 123
        mock_pr.number = 1
        mock_pr.title = "Test PR"
        mock_pr.body = "Test description"
        mock_pr.user.login = "testuser"
        mock_pr.head.ref = "feature"
        mock_pr.base.ref = "main"
        mock_pr.state = "open"
        mock_pr.created_at = "2023-01-01T00:00:00Z"
        mock_pr.updated_at = "2023-01-01T00:00:00Z"
        mock_pr.html_url = "https://github.com/test/repo/pull/1"
        mock_pr.additions = 50
        mock_pr.deletions = 10
        mock_pr.commits = 3
        mock_pr.get_files.return_value = []
        
        mock_file = Mock()
        mock_file.filename = "test.py"
        mock_file.status = "modified"
        mock_file.additions = 20
        mock_file.deletions = 5
        mock_file.patch = "@@ -1,5 +1,5 @@\n def test():\n-    pass\n+    return True"
        
        mock_repo = Mock()
        mock_repo.get_pull.return_value = mock_pr
        mock_repo.get_contents.return_value.content = "ZGVmIHRlc3QoKToKICAgIHJldHVybiBUcnVl"  # base64 encoded
        
        mock_github_instance = Mock()
        mock_github_instance.get_repo.return_value = mock_repo
        mock_github_instance.get_user.return_value = Mock()
        mock_github.return_value = mock_github_instance
        
        # Mock OpenAI API
        mock_openai_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '''
        {
            "summary": "Good code quality with minor improvements needed",
            "suggestions": ["Add error handling", "Include more tests"],
            "overall_assessment": "The code is well-structured but could benefit from additional testing.",
            "recommendation": "comment"
        }
        '''
        mock_openai_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_openai_client
        
        # Create reviewer and test
        reviewer = PRReviewer(self.config_file.name)
        
        # Mock file changes
        with patch.object(reviewer, '_analyze_code') as mock_analyze:
            mock_analyze.return_value = {
                'test.py': [Mock(
                    file_path='test.py',
                    issues=[],
                    metrics={'lines_of_code': 10, 'functions': 1},
                    language='python'
                )]
            }
            
            with patch.object(reviewer._get_server_adapter('test_github'), 'get_pr_files') as mock_get_files:
                mock_get_files.return_value = [mock_file]
                
                with patch.object(reviewer._get_server_adapter('test_github'), 'post_review') as mock_post:
                    mock_post.return_value = True
                    
                    with patch.object(reviewer._get_server_adapter('test_github'), 'update_pr_status') as mock_status:
                        mock_status.return_value = True
                        
                        result = reviewer.review_pr("test_github", "test/repo", 1)
        
        # Verify result
        assert result['success'] is True
        assert 'pr_info' in result
        assert 'score_breakdown' in result
        assert 'ai_feedback' in result
        assert result['posted'] is True
    
    def test_analyze_files_workflow(self):
        """Test file analysis workflow"""
        reviewer = PRReviewer(self.config_file.name)
        
        # Test files with various issues
        test_files = {
            'good_code.py': '''
def hello_world():
    """Print hello world message."""
    print("Hello, World!")
    return True
''',
            'bad_code.py': '''
def bad_function():
    password = "secret123"
    x = eval(user_input)
    result = ""
    for i in range(1000):
        result += str(i) + ", "
    return result
'''
        }
        
        result = reviewer.analyze_files(test_files)
        
        assert result['success'] is True
        assert 'analysis_results' in result
        assert 'summary_metrics' in result
        
        # Should find issues in bad_code.py
        assert len(result['analysis_results']) == 2
        assert result['summary_metrics']['total_issues'] > 0
    
    def test_server_status_check(self):
        """Test server status checking"""
        with patch('pr_review_agent.adapters.github.Github') as mock_github:
            mock_github_instance = Mock()
            mock_github_instance.get_user.return_value = Mock()
            mock_github.return_value = mock_github_instance
            
            reviewer = PRReviewer(self.config_file.name)
            status = reviewer.get_server_status("test_github")
            
            assert 'server_name' in status
            assert 'connected' in status
            assert status['server_name'] == "test_github"
    
    def test_configuration_management(self):
        """Test configuration management"""
        reviewer = PRReviewer(self.config_file.name)
        
        # Test adding new server
        success = reviewer.configure_server(
            "new_server",
            "gitlab",
            "https://gitlab.example.com/api",
            "test_token"
        )
        
        assert success is True
        assert "new_server" in reviewer.config.servers
    
    def test_error_handling(self):
        """Test error handling in review workflow"""
        reviewer = PRReviewer(self.config_file.name)
        
        # Test with non-existent server
        result = reviewer.review_pr("nonexistent_server", "test/repo", 1)
        
        assert result['success'] is False
        assert 'error' in result
    
    @patch('pr_review_agent.adapters.github.Github')
    def test_github_connection_failure(self, mock_github):
        """Test handling of GitHub connection failure"""
        mock_github.side_effect = Exception("Connection failed")
        
        reviewer = PRReviewer(self.config_file.name)
        status = reviewer.get_server_status("test_github")
        
        assert status['connected'] is False
        assert 'error' in status
    
    def test_analysis_with_large_files(self):
        """Test analysis with files that exceed size limits"""
        reviewer = PRReviewer(self.config_file.name)
        
        # Create a large file that exceeds the limit
        large_content = "# Large file\n" + "x = 1\n" * 100000
        
        test_files = {
            'large_file.py': large_content,
            'normal_file.py': 'def test(): pass'
        }
        
        result = reviewer.analyze_files(test_files)
        
        # Should still succeed but may skip large file
        assert result['success'] is True
    
    def test_unsupported_file_types(self):
        """Test handling of unsupported file types"""
        reviewer = PRReviewer(self.config_file.name)
        
        test_files = {
            'image.png': 'binary content',
            'data.csv': 'name,age\nJohn,25',
            'script.py': 'print("Hello")'
        }
        
        result = reviewer.analyze_files(test_files)
        
        # Should succeed and analyze supported files
        assert result['success'] is True
        # Only Python file should be analyzed
        assert len(result['analysis_results']) <= 1


class TestConfigurationIntegration:
    """Integration tests for configuration system"""
    
    def test_config_creation_and_loading(self):
        """Test configuration file creation and loading"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_path = f.name
        
        try:
            # This should create a default config
            from pr_review_agent.core.config import Config
            config = Config(config_path)
            
            # Verify default servers are present
            assert 'github' in config.servers
            assert 'gitlab' in config.servers
            assert 'bitbucket' in config.servers
            
            # Verify analysis config
            assert len(config.analysis.enabled_analyzers) > 0
            assert 'python' in config.analysis.languages
            
            # Verify AI config
            assert config.ai.provider == 'openai'
            assert config.ai.model == 'gpt-4'
            
            # Verify scoring config
            assert len(config.scoring.weights) == 6
            assert sum(config.scoring.weights.values()) == 1.0
            
        finally:
            os.unlink(config_path)
    
    def test_environment_variable_substitution(self):
        """Test environment variable substitution in config"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
servers:
  test:
    base_url: https://api.github.com
    token: ${TEST_TOKEN}
    type: github
""")
            config_path = f.name
        
        try:
            # Set environment variable
            os.environ['TEST_TOKEN'] = 'test_value'
            
            from pr_review_agent.core.config import Config
            config = Config(config_path)
            
            # Token should not be substituted automatically (manual process)
            # This is a design choice for security
            assert '${TEST_TOKEN}' in config.servers['test'].token
            
        finally:
            os.unlink(config_path)
            if 'TEST_TOKEN' in os.environ:
                del os.environ['TEST_TOKEN']


if __name__ == "__main__":
    pytest.main([__file__])
