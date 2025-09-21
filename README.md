# 🤖 PR Review Agent

An AI-powered Pull Request Review Agent that works across multiple git servers (GitHub, GitLab, Bitbucket) to provide intelligent code review feedback and automated quality analysis.

## ✨ Features

- **🌐 Multi-Platform Support**: Works with GitHub, GitLab, and Bitbucket
- **🧠 AI-Powered Feedback**: Intelligent code review using OpenAI GPT-4 or local models
- **📊 Quality Scoring**: Comprehensive scoring system with category breakdowns
- **🔍 Code Analysis**: Detects security issues, performance problems, and code quality issues
- **💬 Inline Comments**: Posts detailed inline comments with suggestions
- **⚡ CI/CD Integration**: Easy integration with CI/CD pipelines
- **🎯 Modular Design**: Extensible architecture for custom analyzers and feedback providers

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/pr-review-agent.git
cd pr-review-agent

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

### Configuration

1. Initialize configuration:
```bash
pr-review init
```

2. Set up environment variables:
```bash
cp .env.template .env
# Edit .env with your API tokens
```

3. Configure git servers:
```bash
# GitHub
pr-review configure --name github --type github --url https://api.github.com --token YOUR_GITHUB_TOKEN

# GitLab
pr-review configure --name gitlab --type gitlab --url https://gitlab.com/api --token YOUR_GITLAB_TOKEN

# Bitbucket  
pr-review configure --name bitbucket --type bitbucket --url https://api.bitbucket.org --token YOUR_BITBUCKET_TOKEN
```

### Usage

#### Review a Pull Request
```bash
pr-review review --server github --repo owner/repo --pr 123
```

#### Analyze Local Files
```bash
pr-review analyze file1.py file2.py --output results.json
```

#### Check Server Status
```bash
pr-review status
```

## 📖 Detailed Usage

### Command Line Interface

The PR Review Agent provides a comprehensive CLI with the following commands:

#### `pr-review review`
Review a pull request on a git server.

**Options:**
- `--server, -s`: Git server name (required)
- `--repo, -r`: Repository in owner/repo format (required)  
- `--pr, -p`: Pull request number (required)
- `--post/--no-post`: Whether to post review (default: true)
- `--output, -o`: Save results to JSON file

**Example:**
```bash
pr-review review -s github -r microsoft/vscode -p 123 --output review_results.json
```

#### `pr-review analyze`
Analyze local files without connecting to a git server.

**Arguments:**
- `files`: One or more file paths to analyze

**Options:**
- `--output, -o`: Save results to JSON file

**Example:**
```bash
pr-review analyze src/*.py tests/*.py --output analysis.json
```

#### `pr-review configure`
Configure a git server connection.

**Options:**
- `--name, -n`: Server configuration name (required)
- `--type, -t`: Server type - github, gitlab, or bitbucket (required)
- `--url, -u`: Server base URL (required)
- `--token`: Authentication token (required)

**Example:**
```bash
pr-review configure -n my-gitlab -t gitlab -u https://gitlab.example.com/api --token glpat-xxxxxxxxxxxxxxxxxxxx
```

#### `pr-review status`
Check the connection status of configured servers.

**Options:**
- `--server, -s`: Check specific server only

**Example:**
```bash
pr-review status --server github
```

#### `pr-review init`
Initialize a new configuration file with default settings.

#### `pr-review list-servers`
List all supported git server types.

#### `pr-review version`
Show version information.

### Configuration File

The configuration file (`pr_review_config.yaml`) allows you to customize:

- **Server Settings**: API endpoints, tokens, timeouts
- **Analysis Rules**: Enabled analyzers, language-specific settings
- **AI Configuration**: Model selection, API keys, behavior
- **Scoring Weights**: Customize how different aspects affect the overall score
- **Review Behavior**: Auto-approval thresholds, comment limits

Example configuration:
```yaml
servers:
  github:
    base_url: https://api.github.com
    token: ${GITHUB_TOKEN}
    type: github

analysis:
  enabled_analyzers:
    - structure
    - security
    - performance
  languages:
    python:
      linters: [pylint, flake8, bandit]
      max_line_length: 88

ai:
  provider: openai
  model: gpt-4
  api_key: ${OPENAI_API_KEY}
  temperature: 0.3

scoring:
  weights:
    code_quality: 0.25
    security: 0.20
    test_coverage: 0.20
    documentation: 0.15
    performance: 0.10
    maintainability: 0.10
```

## 🏗️ Architecture

The PR Review Agent follows a modular architecture:

```
pr_review_agent/
├── core/                 # Core functionality
│   ├── config.py        # Configuration management
│   ├── reviewer.py      # Main reviewer class
│   ├── ai_feedback.py   # AI feedback generation
│   └── scorer.py        # Quality scoring system
├── adapters/            # Git server adapters
│   ├── base.py         # Base adapter interface
│   ├── github.py       # GitHub implementation
│   ├── gitlab.py       # GitLab implementation
│   └── bitbucket.py    # Bitbucket implementation
├── analyzers/          # Code analyzers
│   ├── base.py        # Base analyzer classes
│   └── manager.py     # Analysis coordination
└── cli.py             # Command-line interface
```

### Key Components

#### 1. Git Server Adapters
Abstracted adapters for different git platforms:
- **GitHub Adapter**: Uses PyGithub library
- **GitLab Adapter**: Uses GitLab REST API
- **Bitbucket Adapter**: Uses Bitbucket REST API

#### 2. Code Analyzers
Modular analyzers for different aspects:
- **Structure Analyzer**: Code organization, complexity, file size
- **Security Analyzer**: Security vulnerabilities, hardcoded secrets
- **Performance Analyzer**: Performance anti-patterns

#### 3. AI Feedback System
AI-powered review generation:
- **OpenAI Provider**: Uses GPT-4 for intelligent feedback
- **Hugging Face Provider**: Local transformer models
- **Fallback Provider**: Template-based feedback

#### 4. Scoring System
Comprehensive quality scoring:
- Weighted category scoring
- Configurable thresholds
- Grade assignment (A-F)

## 🛠️ Development

### Setting Up Development Environment

```bash
# Clone repository
git clone https://github.com/your-username/pr-review-agent.git
cd pr-review-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate

# Install development dependencies
pip install -r requirements.txt
pip install -e .[dev]
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=pr_review_agent

# Run specific test file
pytest tests/test_analyzers.py
```

### Code Quality

```bash
# Format code
black pr_review_agent/

# Lint code
pylint pr_review_agent/

# Type checking
mypy pr_review_agent/
```

### Adding New Analyzers

1. Create a new analyzer class inheriting from `BaseAnalyzer`:

```python
from pr_review_agent.analyzers.base import BaseAnalyzer, AnalysisResult

class CustomAnalyzer(BaseAnalyzer):
    def can_analyze(self, file_path: str) -> bool:
        return file_path.endswith('.py')
    
    def analyze(self, file_path: str, content: str) -> AnalysisResult:
        # Your analysis logic here
        pass
```

2. Register the analyzer in `AnalysisManager`:

```python
if 'custom' in enabled_analyzers:
    self.analyzers.append(CustomAnalyzer(self.config))
```

### Adding New Git Server Adapters

1. Create adapter class inheriting from `GitServerAdapter`:

```python
from pr_review_agent.adapters.base import GitServerAdapter, AdapterFactory

class CustomServerAdapter(GitServerAdapter):
    def get_pr_info(self, repository: str, pr_number: int):
        # Implementation
        pass
    
    # Implement other required methods...

# Register the adapter
AdapterFactory.register_adapter("custom", CustomServerAdapter)
```

## 🔧 CI/CD Integration

### GitHub Actions

```yaml
name: PR Review
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install PR Review Agent
        run: |
          pip install pr-review-agent
      - name: Review PR
        run: |
          pr-review review --server github --repo ${{ github.repository }} --pr ${{ github.event.number }}
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

### GitLab CI

```yaml
pr_review:
  stage: test
  script:
    - pip install pr-review-agent
    - pr-review review --server gitlab --repo $CI_PROJECT_PATH --pr $CI_MERGE_REQUEST_IID
  only:
    - merge_requests
  variables:
    GITLAB_TOKEN: $GITLAB_TOKEN
    OPENAI_API_KEY: $OPENAI_API_KEY
```

### Jenkins Pipeline

```groovy
pipeline {
    agent any
    stages {
        stage('PR Review') {
            when {
                changeRequest()
            }
            steps {
                sh '''
                    pip install pr-review-agent
                    pr-review review --server github --repo ${REPO_NAME} --pr ${CHANGE_ID}
                '''
            }
        }
    }
}
```

## 📊 Output Examples

### Review Summary
```
🎯 Quality Score: B (78.5/100)

📊 Category Breakdown:
✅ Code Quality: 85.2/100
⚠️ Security: 72.1/100  
✅ Test Coverage: 88.0/100
✅ Documentation: 79.5/100
✅ Performance: 82.3/100
⚠️ Maintainability: 65.8/100

🔍 Issues Found:
Total Issues: 12
• Errors: 2
• Warnings: 7
• Info: 3

💡 Key Suggestions:
1. Address security vulnerability in authentication module
2. Add unit tests for new utility functions
3. Consider breaking large function into smaller methods
```

### JSON Output
```json
{
  "success": true,
  "pr_info": {
    "number": 123,
    "title": "Add new feature",
    "files_changed": 8,
    "additions": 245,
    "deletions": 67
  },
  "score_breakdown": {
    "overall_score": 78.5,
    "grade": "B",
    "category_scores": {
      "code_quality": 85.2,
      "security": 72.1,
      "test_coverage": 88.0,
      "documentation": 79.5,
      "performance": 82.3,
      "maintainability": 65.8
    }
  },
  "ai_feedback": {
    "summary": "Good quality implementation with room for improvement",
    "suggestions": ["Add error handling", "Improve documentation"],
    "recommendation": "comment"
  }
}
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Types of Contributions
- 🐛 Bug fixes
- ✨ New features
- 📖 Documentation improvements
- 🧪 Test coverage
- 🎨 Code style improvements

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Update documentation
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenAI for GPT-4 API
- GitHub, GitLab, and Bitbucket for their excellent APIs
- The open-source community for inspiration and tools

## 🐛 Troubleshooting

### Common Issues

#### Authentication Errors
```bash
# Verify your tokens are set correctly
pr-review status
```

#### Connection Timeouts
```bash
# Increase timeout in configuration
# Edit pr_review_config.yaml:
servers:
  github:
    timeout: 60
```

#### Import Errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Debug Mode
```bash
# Enable verbose logging
export PR_REVIEW_DEBUG=1
pr-review review --server github --repo owner/repo --pr 123
```

### Getting Help
- 📖 Check this documentation
- 🐛 [Open an issue](https://github.com/your-username/pr-review-agent/issues)
- 💬 [Join our Discord](https://discord.gg/your-invite)
- 📧 Email: support@pr-review-agent.com

## 🗺️ Roadmap

- [ ] Visual Studio Code extension
- [ ] Slack/Teams integration
- [ ] Custom rule engine
- [ ] Machine learning-based suggestions
- [ ] Multi-language support improvements
- [ ] Performance optimizations
- [ ] Advanced security scanning
