"""Tests for core configuration module."""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, mock_open

from pr_review_agent.core.config import Config, ConfigManager


class TestConfig:
    """Test Config dataclass."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = Config()
        
        assert config.github_token == ""
        assert config.gitlab_token == ""
        assert config.bitbucket_token == ""
        assert config.openai_api_key == ""
        assert config.ai_provider == "openai"
        assert config.enable_security_analysis is True
        assert config.enable_performance_analysis is True
        assert config.enable_structure_analysis is True
        assert config.max_file_size == 1024 * 1024  # 1MB
        assert config.supported_extensions == ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs']
    
    def test_scoring_weights(self):
        """Test scoring configuration."""
        config = Config()
        
        expected_weights = {
            'security': 0.3,
            'performance': 0.25,
            'structure': 0.25,
            'style': 0.2
        }
        assert config.scoring_weights == expected_weights
    
    def test_scoring_thresholds(self):
        """Test scoring thresholds."""
        config = Config()
        
        expected_thresholds = {
            'A+': 95, 'A': 90, 'A-': 85,
            'B+': 80, 'B': 75, 'B-': 70,
            'C+': 65, 'C': 60, 'C-': 55,
            'D': 50, 'F': 0
        }
        assert config.scoring_thresholds == expected_thresholds
    
    def test_security_rules(self):
        """Test security rules configuration."""
        config = Config()
        
        assert 'hardcoded_secrets' in config.security_rules
        assert 'sql_injection' in config.security_rules
        assert 'xss_vulnerabilities' in config.security_rules
        assert 'unsafe_deserialization' in config.security_rules
        assert 'weak_crypto' in config.security_rules


class TestConfigManager:
    """Test ConfigManager class."""
    
    def test_load_from_file_yaml(self):
        """Test loading configuration from YAML file."""
        yaml_content = """
ai_provider: "huggingface"
max_file_size: 2097152
enable_security_analysis: false
scoring_weights:
  security: 0.4
  performance: 0.3
  structure: 0.2
  style: 0.1
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            f.flush()
            
            try:
                config = ConfigManager.load_from_file(f.name)
                
                assert config.ai_provider == "huggingface"
                assert config.max_file_size == 2097152
                assert config.enable_security_analysis is False
                assert config.scoring_weights['security'] == 0.4
                assert config.scoring_weights['performance'] == 0.3
                
            finally:
                os.unlink(f.name)
    
    def test_load_from_file_not_found(self):
        """Test loading from non-existent file returns default config."""
        config = ConfigManager.load_from_file("/non/existent/file.yaml")
        
        # Should return default config
        assert isinstance(config, Config)
        assert config.ai_provider == "openai"  # default value
    
    def test_load_from_env(self):
        """Test loading configuration from environment variables."""
        env_vars = {
            'GITHUB_TOKEN': 'gh_test_token',
            'GITLAB_TOKEN': 'gl_test_token',
            'OPENAI_API_KEY': 'openai_test_key',
            'AI_PROVIDER': 'huggingface',
            'ENABLE_SECURITY_ANALYSIS': 'false',
            'MAX_FILE_SIZE': '512000'
        }
        
        with patch.dict(os.environ, env_vars):
            config = ConfigManager.load_from_env()
            
            assert config.github_token == 'gh_test_token'
            assert config.gitlab_token == 'gl_test_token'
            assert config.openai_api_key == 'openai_test_key'
            assert config.ai_provider == 'huggingface'
            assert config.enable_security_analysis is False
            assert config.max_file_size == 512000
    
    def test_load_from_env_boolean_conversion(self):
        """Test boolean environment variable conversion."""
        test_cases = [
            ('true', True),
            ('True', True),
            ('TRUE', True),
            ('1', True),
            ('yes', True),
            ('false', False),
            ('False', False),
            ('FALSE', False),
            ('0', False),
            ('no', False),
            ('', False),
        ]
        
        for env_value, expected in test_cases:
            with patch.dict(os.environ, {'ENABLE_SECURITY_ANALYSIS': env_value}):
                config = ConfigManager.load_from_env()
                assert config.enable_security_analysis is expected
    
    def test_merge_configs(self):
        """Test merging multiple configurations."""
        base_config = Config(
            github_token="base_token",
            ai_provider="openai",
            max_file_size=1024
        )
        
        override_config = Config(
            github_token="override_token",
            gitlab_token="new_gitlab_token",
            max_file_size=2048
        )
        
        merged = ConfigManager.merge_configs(base_config, override_config)
        
        # Overridden values
        assert merged.github_token == "override_token"
        assert merged.max_file_size == 2048
        
        # New values
        assert merged.gitlab_token == "new_gitlab_token"
        
        # Preserved values
        assert merged.ai_provider == "openai"
    
    def test_validate_config_valid(self):
        """Test validation of valid configuration."""
        config = Config(
            ai_provider="openai",
            openai_api_key="sk-test123",
            github_token="gh_test"
        )
        
        # Should not raise any exception
        ConfigManager.validate_config(config)
    
    def test_validate_config_invalid_ai_provider(self):
        """Test validation fails for invalid AI provider."""
        config = Config(ai_provider="invalid_provider")
        
        with pytest.raises(ValueError, match="Invalid AI provider"):
            ConfigManager.validate_config(config)
    
    def test_validate_config_missing_openai_key(self):
        """Test validation fails when OpenAI provider has no API key."""
        config = Config(
            ai_provider="openai",
            openai_api_key=""
        )
        
        with pytest.raises(ValueError, match="OpenAI API key is required"):
            ConfigManager.validate_config(config)
    
    def test_validate_config_missing_git_tokens(self):
        """Test validation fails when no git server tokens provided."""
        config = Config(
            github_token="",
            gitlab_token="",
            bitbucket_token=""
        )
        
        with pytest.raises(ValueError, match="At least one git server token"):
            ConfigManager.validate_config(config)
    
    def test_save_to_file(self):
        """Test saving configuration to file."""
        config = Config(
            github_token="test_token",
            ai_provider="huggingface",
            max_file_size=2048
        )
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            try:
                ConfigManager.save_to_file(config, f.name)
                
                # Load it back and verify
                loaded_config = ConfigManager.load_from_file(f.name)
                assert loaded_config.github_token == "test_token"
                assert loaded_config.ai_provider == "huggingface"
                assert loaded_config.max_file_size == 2048
                
            finally:
                os.unlink(f.name)
    
    def test_get_default_config_path(self):
        """Test getting default configuration path."""
        path = ConfigManager.get_default_config_path()
        
        assert isinstance(path, Path)
        assert str(path).endswith('pr_review_config.yaml')
    
    @patch('builtins.open', new_callable=mock_open, read_data="invalid: yaml: content:")
    def test_load_invalid_yaml(self, mock_file):
        """Test loading invalid YAML returns default config."""
        config = ConfigManager.load_from_file("test.yaml")
        
        # Should return default config on invalid YAML
        assert isinstance(config, Config)
        assert config.ai_provider == "openai"  # default value
