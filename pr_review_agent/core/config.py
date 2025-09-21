"""
Configuration management for PR Review Agent
"""
import os
import yaml
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ServerConfig:
    """Configuration for a specific git server"""
    base_url: str
    token: str
    type: str  # github, gitlab, bitbucket
    api_version: str = "v1"
    timeout: int = 30
    max_retries: int = 3


@dataclass
class AnalysisConfig:
    """Configuration for code analysis"""
    enabled_analyzers: list = field(default_factory=lambda: [
        "structure", "standards", "security", "performance", "bugs"
    ])
    languages: dict = field(default_factory=lambda: {
        "python": {"linters": ["pylint", "flake8", "bandit"]},
        "javascript": {"linters": ["eslint"]},
        "typescript": {"linters": ["tslint", "eslint"]},
        "java": {"linters": ["checkstyle", "spotbugs"]},
        "go": {"linters": ["golint", "go vet"]},
        "cpp": {"linters": ["cppcheck"]},
    })
    max_file_size: int = 1024 * 1024  # 1MB
    exclude_patterns: list = field(default_factory=lambda: [
        "*.min.js", "*.bundle.js", "node_modules/*", "vendor/*", 
        "*.generated.*", "dist/*", "build/*"
    ])


@dataclass
class AIConfig:
    """Configuration for AI-powered feedback"""
    provider: str = "openai"  # openai, huggingface, local
    model: str = "gpt-4"
    api_key: Optional[str] = None
    max_tokens: int = 1500
    temperature: float = 0.3
    enable_suggestions: bool = True
    enable_inline_comments: bool = True


@dataclass
class ScoringConfig:
    """Configuration for PR scoring system"""
    weights: dict = field(default_factory=lambda: {
        "code_quality": 0.25,
        "test_coverage": 0.20,
        "documentation": 0.15,
        "security": 0.20,
        "performance": 0.10,
        "maintainability": 0.10
    })
    min_score: float = 0.0
    max_score: float = 100.0
    thresholds: dict = field(default_factory=lambda: {
        "excellent": 90,
        "good": 75,
        "fair": 60,
        "poor": 40
    })


class Config:
    """Main configuration class for PR Review Agent"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._find_config_file()
        self.servers: Dict[str, ServerConfig] = {}
        self.analysis = AnalysisConfig()
        self.ai = AIConfig()
        self.scoring = ScoringConfig()
        self.load_config()
    
    def _find_config_file(self) -> str:
        """Find configuration file in various locations"""
        possible_paths = [
            "pr_review_config.yaml",
            "config/pr_review_config.yaml",
            os.path.expanduser("~/.pr_review_agent/config.yaml"),
            "/etc/pr_review_agent/config.yaml"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        # Create default config in current directory
        return "pr_review_config.yaml"
    
    def load_config(self):
        """Load configuration from YAML file"""
        if not os.path.exists(self.config_path):
            self.create_default_config()
            return
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            if not config_data:
                self.create_default_config()
                return
            
            self._load_servers(config_data.get('servers', {}))
            self._load_analysis_config(config_data.get('analysis', {}))
            self._load_ai_config(config_data.get('ai', {}))
            self._load_scoring_config(config_data.get('scoring', {}))
            
        except Exception as e:
            print(f"Error loading config: {e}")
            self.create_default_config()
    
    def _load_servers(self, servers_data: Dict[str, Any]):
        """Load server configurations"""
        for name, server_data in servers_data.items():
            self.servers[name] = ServerConfig(**server_data)
    
    def _load_analysis_config(self, analysis_data: Dict[str, Any]):
        """Load analysis configuration"""
        if analysis_data:
            self.analysis = AnalysisConfig(**analysis_data)
    
    def _load_ai_config(self, ai_data: Dict[str, Any]):
        """Load AI configuration"""
        if ai_data:
            # Load API key from environment if not in config
            if 'api_key' not in ai_data:
                ai_data['api_key'] = os.getenv('OPENAI_API_KEY')
            self.ai = AIConfig(**ai_data)
    
    def _load_scoring_config(self, scoring_data: Dict[str, Any]):
        """Load scoring configuration"""
        if scoring_data:
            self.scoring = ScoringConfig(**scoring_data)
    
    def create_default_config(self):
        """Create a default configuration file"""
        default_config = {
            'servers': {
                'github': {
                    'base_url': 'https://api.github.com',
                    'token': '${GITHUB_TOKEN}',
                    'type': 'github',
                    'api_version': 'v3'
                },
                'gitlab': {
                    'base_url': 'https://gitlab.com/api',
                    'token': '${GITLAB_TOKEN}',
                    'type': 'gitlab',
                    'api_version': 'v4'
                },
                'bitbucket': {
                    'base_url': 'https://api.bitbucket.org',
                    'token': '${BITBUCKET_TOKEN}',
                    'type': 'bitbucket',
                    'api_version': '2.0'
                }
            },
            'analysis': {
                'enabled_analyzers': [
                    'structure', 'standards', 'security', 'performance', 'bugs'
                ],
                'languages': {
                    'python': {'linters': ['pylint', 'flake8', 'bandit']},
                    'javascript': {'linters': ['eslint']},
                    'typescript': {'linters': ['tslint', 'eslint']},
                    'java': {'linters': ['checkstyle', 'spotbugs']},
                    'go': {'linters': ['golint', 'go vet']},
                    'cpp': {'linters': ['cppcheck']}
                },
                'max_file_size': 1048576,
                'exclude_patterns': [
                    '*.min.js', '*.bundle.js', 'node_modules/*', 'vendor/*',
                    '*.generated.*', 'dist/*', 'build/*'
                ]
            },
            'ai': {
                'provider': 'openai',
                'model': 'gpt-4',
                'api_key': '${OPENAI_API_KEY}',
                'max_tokens': 1500,
                'temperature': 0.3,
                'enable_suggestions': True,
                'enable_inline_comments': True
            },
            'scoring': {
                'weights': {
                    'code_quality': 0.25,
                    'test_coverage': 0.20,
                    'documentation': 0.15,
                    'security': 0.20,
                    'performance': 0.10,
                    'maintainability': 0.10
                },
                'min_score': 0.0,
                'max_score': 100.0,
                'thresholds': {
                    'excellent': 90,
                    'good': 75,
                    'fair': 60,
                    'poor': 40
                }
            }
        }
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.config_path) or '.', exist_ok=True)
        
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(default_config, f, default_flow_style=False, indent=2)
        
        print(f"Created default configuration at: {self.config_path}")
        print("Please update the configuration with your API tokens.")
    
    def get_server_config(self, server_name: str) -> Optional[ServerConfig]:
        """Get configuration for a specific server"""
        return self.servers.get(server_name)
    
    def add_server(self, name: str, config: ServerConfig):
        """Add a new server configuration"""
        self.servers[name] = config
    
    def save_config(self):
        """Save current configuration to file"""
        config_data = {
            'servers': {
                name: {
                    'base_url': server.base_url,
                    'token': server.token,
                    'type': server.type,
                    'api_version': server.api_version,
                    'timeout': server.timeout,
                    'max_retries': server.max_retries
                }
                for name, server in self.servers.items()
            },
            'analysis': {
                'enabled_analyzers': self.analysis.enabled_analyzers,
                'languages': self.analysis.languages,
                'max_file_size': self.analysis.max_file_size,
                'exclude_patterns': self.analysis.exclude_patterns
            },
            'ai': {
                'provider': self.ai.provider,
                'model': self.ai.model,
                'api_key': self.ai.api_key,
                'max_tokens': self.ai.max_tokens,
                'temperature': self.ai.temperature,
                'enable_suggestions': self.ai.enable_suggestions,
                'enable_inline_comments': self.ai.enable_inline_comments
            },
            'scoring': {
                'weights': self.scoring.weights,
                'min_score': self.scoring.min_score,
                'max_score': self.scoring.max_score,
                'thresholds': self.scoring.thresholds
            }
        }
        
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f, default_flow_style=False, indent=2)
