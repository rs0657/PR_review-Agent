# Contributing to PR Review Agent

We love your input! We want to make contributing to PR Review Agent as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

## Development Process

We use GitHub to host code, to track issues and feature requests, as well as accept pull requests.

## Pull Requests

Pull requests are the best way to propose changes to the codebase. We actively welcome your pull requests:

1. Fork the repo and create your branch from `main`.
2. If you've added code that should be tested, add tests.
3. If you've changed APIs, update the documentation.
4. Ensure the test suite passes.
5. Make sure your code lints.
6. Issue that pull request!

## Setting Up Development Environment

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/your-username/pr-review-agent.git
   cd pr-review-agent
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install development dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -e .[dev]
   ```

4. **Set up pre-commit hooks** (optional but recommended)
   ```bash
   pre-commit install
   ```

## Code Style

We use several tools to maintain code quality:

- **Black** for code formatting
- **Pylint** for linting
- **MyPy** for type checking
- **isort** for import sorting

Run these before submitting:
```bash
# Format code
black pr_review_agent/ tests/

# Sort imports
isort pr_review_agent/ tests/

# Lint code
pylint pr_review_agent/

# Type check
mypy pr_review_agent/
```

## Testing

We use pytest for testing. Please ensure all tests pass:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=pr_review_agent --cov-report=html

# Run specific test file
pytest tests/unit/test_analyzers.py

# Run with verbose output
pytest -v
```

### Writing Tests

- Write unit tests for new functionality
- Aim for high test coverage (>80%)
- Use meaningful test names that describe what's being tested
- Use fixtures in `conftest.py` for common test data
- Mock external dependencies (APIs, file system, etc.)

Example test structure:
```python
class TestNewFeature:
    def setup_method(self):
        """Set up test fixtures"""
        self.feature = NewFeature()
    
    def test_basic_functionality(self):
        """Test basic functionality works correctly"""
        result = self.feature.do_something()
        assert result == expected_value
    
    def test_error_handling(self):
        """Test error handling works correctly"""
        with pytest.raises(ExpectedError):
            self.feature.do_something_invalid()
```

## Adding New Features

### New Analyzers

To add a new code analyzer:

1. Create a new class inheriting from `BaseAnalyzer`:
   ```python
   from pr_review_agent.analyzers.base import BaseAnalyzer, AnalysisResult
   
   class MyAnalyzer(BaseAnalyzer):
       def can_analyze(self, file_path: str) -> bool:
           return file_path.endswith('.py')
       
       def analyze(self, file_path: str, content: str) -> AnalysisResult:
           # Implementation here
           pass
   ```

2. Register it in `AnalysisManager`
3. Add configuration options
4. Write comprehensive tests
5. Update documentation

### New Git Server Adapters

To add support for a new git server:

1. Create a new adapter inheriting from `GitServerAdapter`:
   ```python
   from pr_review_agent.adapters.base import GitServerAdapter, AdapterFactory
   
   class MyServerAdapter(GitServerAdapter):
       def get_pr_info(self, repository: str, pr_number: int):
           # Implementation
           pass
       # Implement other required methods...
   
   # Register the adapter
   AdapterFactory.register_adapter("myserver", MyServerAdapter)
   ```

2. Add configuration schema
3. Write integration tests
4. Update documentation

### New AI Providers

To add a new AI feedback provider:

1. Create a new provider inheriting from `BaseFeedbackProvider`:
   ```python
   from pr_review_agent.core.ai_feedback import BaseFeedbackProvider
   
   class MyAIProvider(BaseFeedbackProvider):
       def generate_feedback(self, file_changes, analysis_results):
           # Implementation
           pass
   ```

2. Register it in `FeedbackManager`
3. Add configuration options
4. Write tests with mocked AI responses

## Documentation

- Update README.md for user-facing changes
- Add docstrings to all public functions and classes
- Update configuration documentation
- Add examples for new features

### Docstring Format

We use Google-style docstrings:

```python
def analyze_code(file_path: str, content: str) -> AnalysisResult:
    """Analyze code content for issues.
    
    Args:
        file_path: Path to the file being analyzed
        content: Content of the file
        
    Returns:
        AnalysisResult containing issues and metrics
        
    Raises:
        AnalysisError: If analysis fails
    """
```

## Commit Message Format

Use conventional commit format:

```
type(scope): description

body (optional)

footer (optional)
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

Examples:
```
feat(analyzers): add support for Go language analysis
fix(github): handle rate limiting in API calls
docs(readme): update installation instructions
```

## Reporting Bugs

We use GitHub issues to track public bugs. Report a bug by opening a new issue.

**Great Bug Reports** tend to have:

- A quick summary and/or background
- Steps to reproduce
  - Be specific!
  - Give sample code if you can
- What you expected would happen
- What actually happens
- Notes (possibly including why you think this might be happening, or stuff you tried that didn't work)

## Feature Requests

We welcome feature requests! Please:

1. Check if the feature already exists or is planned
2. Open an issue with the "enhancement" label
3. Describe the feature and its use case
4. Consider contributing the implementation

## Code Review Process

All submissions require review. We use GitHub pull requests for this purpose.

### What We Look For

- **Functionality**: Does the code work as intended?
- **Tests**: Are there adequate tests?
- **Documentation**: Is the code well-documented?
- **Style**: Does it follow our coding standards?
- **Performance**: Are there any performance concerns?
- **Security**: Are there any security implications?

### Review Timeline

- Small fixes: 1-2 days
- New features: 3-7 days
- Major changes: 1-2 weeks

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Community

- Be respectful and inclusive
- Help others learn and grow
- Share knowledge and best practices
- Give constructive feedback

## Getting Help

- Check the documentation first
- Search existing issues
- Ask questions in discussions
- Join our community chat

## Recognition

Contributors will be:
- Added to the contributors list
- Mentioned in release notes
- Invited to be maintainers for significant contributions

Thank you for contributing to PR Review Agent! 🚀
