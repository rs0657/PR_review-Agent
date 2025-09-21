"""
Test configuration for pytest
"""
import pytest
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

@pytest.fixture(scope="session")
def sample_python_code():
    """Sample Python code for testing analyzers"""
    return '''
def example_function(x, y):
    """Example function with good practices."""
    if x > 0:
        return x + y
    return 0

class ExampleClass:
    """Example class with docstring."""
    
    def method(self):
        """Example method."""
        pass
'''

@pytest.fixture(scope="session") 
def sample_bad_python_code():
    """Sample Python code with issues for testing"""
    return '''
def bad_function():
    password = "secret123"
    result = eval(user_input)
    x = ""
    for i in range(1000):
        x += str(i)
    return x

def function_without_docstring():
    return "no docstring"

class ClassWithoutDocstring:
    pass
'''

@pytest.fixture(scope="session")
def sample_javascript_code():
    """Sample JavaScript code for testing"""
    return '''
function goodFunction() {
    const data = getData();
    return data.map(item => item.value);
}

// Modern ES6+ code
const processData = async (items) => {
    return items.filter(item => item.active);
};
'''

@pytest.fixture(scope="session")
def sample_bad_javascript_code():
    """Sample JavaScript code with issues"""
    return '''
function badFunction() {
    var oldStyleVar = "use let or const";
    document.getElementById("element").innerHTML = userInput;
    
    for (var i = 0; i < 1000; i++) {
        document.getElementById("list").appendChild(element);
    }
}
'''

@pytest.fixture
def mock_pr_info():
    """Mock PR info for testing"""
    from datetime import datetime
    from pr_review_agent.adapters.base import PRInfo
    
    return PRInfo(
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
        commits=2
    )

@pytest.fixture
def mock_file_change():
    """Mock file change for testing"""
    from pr_review_agent.adapters.base import FileChange
    
    return FileChange(
        filename="test.py",
        status="modified",
        additions=10,
        deletions=5,
        patch="@@ -1,3 +1,3 @@",
        content_before="old content",
        content_after="new content"
    )

@pytest.fixture
def temp_config_file():
    """Create temporary configuration file"""
    import tempfile
    
    config_content = """
servers:
  test_github:
    base_url: https://api.github.com
    token: test_token
    type: github

analysis:
  enabled_analyzers:
    - structure
    - security
    - performance
  max_file_size: 1048576

ai:
  provider: openai
  model: gpt-4
  api_key: test_key

scoring:
  weights:
    code_quality: 0.25
    security: 0.20
    test_coverage: 0.20
    documentation: 0.15
    performance: 0.10
    maintainability: 0.10
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(config_content)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    os.unlink(temp_path)
