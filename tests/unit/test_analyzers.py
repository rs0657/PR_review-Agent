"""
Unit tests for code analyzers
"""
import pytest
from pr_review_agent.analyzers.base import (
    StructureAnalyzer, SecurityAnalyzer, PerformanceAnalyzer, CodeIssue
)


class TestStructureAnalyzer:
    """Test structure analyzer functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.analyzer = StructureAnalyzer()
    
    def test_can_analyze_python_file(self):
        """Test that analyzer can handle Python files"""
        assert self.analyzer.can_analyze("test.py")
        assert self.analyzer.can_analyze("module/test.py")
    
    def test_can_analyze_javascript_file(self):
        """Test that analyzer can handle JavaScript files"""
        assert self.analyzer.can_analyze("test.js")
        assert self.analyzer.can_analyze("src/test.ts")
    
    def test_cannot_analyze_unsupported_file(self):
        """Test that analyzer rejects unsupported files"""
        assert not self.analyzer.can_analyze("test.txt")
        assert not self.analyzer.can_analyze("image.png")
    
    def test_analyze_python_code(self):
        """Test analysis of Python code"""
        code = '''
def test_function():
    """Test function docstring"""
    x = 1
    y = 2
    return x + y

class TestClass:
    """Test class docstring"""
    pass
'''
        result = self.analyzer.analyze("test.py", code)
        
        assert result.file_path == "test.py"
        assert result.language == "python"
        assert "functions" in result.metrics
        assert "classes" in result.metrics
        assert result.metrics["functions"] == 1
        assert result.metrics["classes"] == 1
    
    def test_detect_missing_docstring(self):
        """Test detection of missing docstrings"""
        code = '''
def function_without_docstring():
    return "hello"

class ClassWithoutDocstring:
    pass
'''
        result = self.analyzer.analyze("test.py", code)
        
        # Should detect missing docstrings
        missing_docstring_issues = [
            issue for issue in result.issues 
            if issue.rule_id == "missing_docstring"
        ]
        assert len(missing_docstring_issues) == 2
    
    def test_detect_long_lines(self):
        """Test detection of long lines"""
        long_line = "x = " + "1" * 200  # Very long line
        code = f'''
def test():
    {long_line}
    return x
'''
        result = self.analyzer.analyze("test.py", code)
        
        # Should detect long line
        long_line_issues = [
            issue for issue in result.issues 
            if issue.rule_id == "line_too_long"
        ]
        assert len(long_line_issues) >= 1
    
    def test_detect_high_complexity(self):
        """Test detection of high complexity functions"""
        # Create a function with high cyclomatic complexity
        code = '''
def complex_function(x):
    if x > 0:
        if x > 10:
            if x > 20:
                if x > 30:
                    if x > 40:
                        if x > 50:
                            return "very high"
                        return "high"
                    return "medium-high"
                return "medium"
            return "low-medium"
        return "low"
    return "negative"
'''
        result = self.analyzer.analyze("test.py", code)
        
        # Should detect high complexity
        complexity_issues = [
            issue for issue in result.issues 
            if issue.rule_id == "high_complexity"
        ]
        assert len(complexity_issues) >= 1


class TestSecurityAnalyzer:
    """Test security analyzer functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.analyzer = SecurityAnalyzer()
    
    def test_can_analyze_any_file(self):
        """Test that security analyzer can analyze any file"""
        assert self.analyzer.can_analyze("test.py")
        assert self.analyzer.can_analyze("test.js")
        assert self.analyzer.can_analyze("test.java")
    
    def test_detect_hardcoded_password(self):
        """Test detection of hardcoded passwords"""
        code = '''
def connect():
    password = "PLACEHOLDER_PASSWORD"
    return connect_to_db(password)
'''
        result = self.analyzer.analyze("test.py", code)
        
        # Should detect hardcoded password
        password_issues = [
            issue for issue in result.issues 
            if issue.rule_id == "hardcoded_password"
        ]
        assert len(password_issues) >= 1
        assert password_issues[0].severity == "error"
    
    def test_detect_hardcoded_api_key(self):
        """Test detection of hardcoded API keys"""
        code = '''
API_KEY = "PLACEHOLDER_API_KEY"
'''
        result = self.analyzer.analyze("config.py", code)
        
        # Should detect hardcoded API key
        api_key_issues = [
            issue for issue in result.issues 
            if issue.rule_id == "hardcoded_api_key"
        ]
        assert len(api_key_issues) >= 1
    
    def test_detect_sql_injection(self):
        """Test detection of SQL injection vulnerabilities"""
        code = '''
def get_user(user_id):
    query = "SELECT * FROM users WHERE id = " + user_id
    return execute_query(query)
'''
        result = self.analyzer.analyze("database.py", code)
        
        # Should detect potential SQL injection
        sql_issues = [
            issue for issue in result.issues 
            if issue.rule_id == "sql_injection"
        ]
        assert len(sql_issues) >= 1
    
    def test_detect_dangerous_eval(self):
        """Test detection of dangerous eval usage"""
        code = '''
def process_input(user_input):
    result = eval(user_input)
    return result
'''
        result = self.analyzer.analyze("processor.py", code)
        
        # Should detect dangerous eval usage
        eval_issues = [
            issue for issue in result.issues 
            if issue.rule_id == "dangerous_eval"
        ]
        assert len(eval_issues) >= 1
        assert eval_issues[0].severity == "error"


class TestPerformanceAnalyzer:
    """Test performance analyzer functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.analyzer = PerformanceAnalyzer()
    
    def test_can_analyze_any_file(self):
        """Test that performance analyzer can analyze any file"""
        assert self.analyzer.can_analyze("test.py")
        assert self.analyzer.can_analyze("test.js")
    
    def test_detect_string_concatenation_in_loop(self):
        """Test detection of inefficient string concatenation"""
        code = '''
def build_string(items):
    result = ""
    for item in items:
        result += str(item) + ", "
    return result
'''
        result = self.analyzer.analyze("utils.py", code)
        
        # Should detect inefficient string concatenation
        concat_issues = [
            issue for issue in result.issues 
            if issue.rule_id == "string_concat_loop"
        ]
        assert len(concat_issues) >= 1
    
    def test_no_issues_for_good_code(self):
        """Test that good code doesn't trigger false positives"""
        code = '''
def efficient_function(items):
    """Well-written function with no performance issues"""
    return [item.upper() for item in items if item]
'''
        result = self.analyzer.analyze("good_code.py", code)
        
        # Should not detect any performance issues
        performance_issues = [
            issue for issue in result.issues 
            if issue.category == "performance"
        ]
        assert len(performance_issues) == 0


def test_code_issue_creation():
    """Test CodeIssue dataclass creation"""
    issue = CodeIssue(
        line_number=10,
        column=5,
        severity="warning",
        category="style",
        message="Test issue",
        rule_id="test_rule",
        suggestion="Fix this"
    )
    
    assert issue.line_number == 10
    assert issue.column == 5
    assert issue.severity == "warning"
    assert issue.category == "style"
    assert issue.message == "Test issue"
    assert issue.rule_id == "test_rule"
    assert issue.suggestion == "Fix this"


if __name__ == "__main__":
    pytest.main([__file__])
