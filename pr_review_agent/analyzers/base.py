"""
Base analyzer interface for code analysis
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import re
import ast


@dataclass
class AnalysisResult:
    """Result of code analysis"""
    file_path: str
    issues: List['CodeIssue']
    metrics: Dict[str, Any]
    language: str


@dataclass
class CodeIssue:
    """Represents a code issue found during analysis"""
    line_number: int
    column: int
    severity: str  # error, warning, info
    category: str  # security, performance, style, maintainability, etc.
    message: str
    rule_id: str
    suggestion: Optional[str] = None


class BaseAnalyzer(ABC):
    """Base class for code analyzers"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
    
    @abstractmethod
    def can_analyze(self, file_path: str) -> bool:
        """Check if this analyzer can analyze the given file"""
        pass
    
    @abstractmethod
    def analyze(self, file_path: str, content: str) -> AnalysisResult:
        """Analyze the code content"""
        pass
    
    def get_language(self, file_path: str) -> str:
        """Determine the programming language from file extension"""
        extension_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.cc': 'cpp',
            '.cxx': 'cpp',
            '.c': 'c',
            '.h': 'c',
            '.hpp': 'cpp',
            '.go': 'go',
            '.rs': 'rust',
            '.rb': 'ruby',
            '.php': 'php',
            '.cs': 'csharp',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala',
            '.sh': 'shell',
            '.bash': 'shell',
            '.zsh': 'shell',
            '.yml': 'yaml',
            '.yaml': 'yaml',
            '.json': 'json',
            '.xml': 'xml',
            '.html': 'html',
            '.css': 'css',
            '.scss': 'scss',
            '.sql': 'sql'
        }
        
        for ext, lang in extension_map.items():
            if file_path.lower().endswith(ext):
                return lang
        
        return 'text'


class StructureAnalyzer(BaseAnalyzer):
    """Analyzes code structure and organization"""
    
    def can_analyze(self, file_path: str) -> bool:
        """Can analyze most programming languages"""
        language = self.get_language(file_path)
        return language in ['python', 'javascript', 'typescript', 'java', 'cpp', 'go']
    
    def analyze(self, file_path: str, content: str) -> AnalysisResult:
        """Analyze code structure"""
        language = self.get_language(file_path)
        issues = []
        metrics = {}
        
        lines = content.split('\n')
        
        # Common structure analysis
        issues.extend(self._check_file_length(lines))
        issues.extend(self._check_line_length(lines))
        issues.extend(self._check_complexity(content, language))
        
        # Language-specific analysis
        if language == 'python':
            issues.extend(self._analyze_python_structure(content))
            metrics.update(self._get_python_metrics(content))
        elif language in ['javascript', 'typescript']:
            issues.extend(self._analyze_js_structure(content))
        
        return AnalysisResult(
            file_path=file_path,
            issues=issues,
            metrics=metrics,
            language=language
        )
    
    def _check_file_length(self, lines: List[str]) -> List[CodeIssue]:
        """Check if file is too long"""
        issues = []
        max_lines = self.config.get('max_file_lines', 500)
        
        if len(lines) > max_lines:
            issues.append(CodeIssue(
                line_number=len(lines),
                column=0,
                severity='warning',
                category='maintainability',
                message=f'File is too long ({len(lines)} lines). Consider breaking it into smaller modules.',
                rule_id='file_too_long',
                suggestion=f'Split file into smaller modules (recommended max: {max_lines} lines)'
            ))
        
        return issues
    
    def _check_line_length(self, lines: List[str]) -> List[CodeIssue]:
        """Check for lines that are too long"""
        issues = []
        max_length = self.config.get('max_line_length', 100)
        
        for i, line in enumerate(lines, 1):
            if len(line) > max_length:
                issues.append(CodeIssue(
                    line_number=i,
                    column=max_length,
                    severity='info',
                    category='style',
                    message=f'Line too long ({len(line)} > {max_length} characters)',
                    rule_id='line_too_long',
                    suggestion='Break long line into multiple lines'
                ))
        
        return issues
    
    def _check_complexity(self, content: str, language: str) -> List[CodeIssue]:
        """Check cyclomatic complexity"""
        issues = []
        
        if language == 'python':
            try:
                tree = ast.parse(content)
                complexity_visitor = ComplexityVisitor()
                complexity_visitor.visit(tree)
                
                for func_name, complexity, line_no in complexity_visitor.complexities:
                    if complexity > 10:
                        issues.append(CodeIssue(
                            line_number=line_no,
                            column=0,
                            severity='warning',
                            category='maintainability',
                            message=f'Function "{func_name}" has high complexity ({complexity})',
                            rule_id='high_complexity',
                            suggestion='Consider breaking this function into smaller functions'
                        ))
            except SyntaxError:
                pass  # Skip if syntax error
        
        return issues
    
    def _analyze_python_structure(self, content: str) -> List[CodeIssue]:
        """Analyze Python-specific structure"""
        issues = []
        
        try:
            tree = ast.parse(content)
            
            # Check for missing docstrings
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    if not ast.get_docstring(node):
                        issues.append(CodeIssue(
                            line_number=node.lineno,
                            column=node.col_offset,
                            severity='info',
                            category='documentation',
                            message=f'{type(node).__name__} "{node.name}" missing docstring',
                            rule_id='missing_docstring',
                            suggestion='Add docstring to describe the purpose and parameters'
                        ))
            
            # Check for too many arguments
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    arg_count = len(node.args.args)
                    if arg_count > 5:
                        issues.append(CodeIssue(
                            line_number=node.lineno,
                            column=node.col_offset,
                            severity='warning',
                            category='maintainability',
                            message=f'Function "{node.name}" has too many arguments ({arg_count})',
                            rule_id='too_many_arguments',
                            suggestion='Consider using a configuration object or reducing parameters'
                        ))
        
        except SyntaxError:
            issues.append(CodeIssue(
                line_number=1,
                column=0,
                severity='error',
                category='syntax',
                message='Syntax error in Python code',
                rule_id='syntax_error'
            ))
        
        return issues
    
    def _analyze_js_structure(self, content: str) -> List[CodeIssue]:
        """Analyze JavaScript/TypeScript structure"""
        issues = []
        lines = content.split('\n')
        
        # Check for var usage (should use let/const)
        for i, line in enumerate(lines, 1):
            if re.search(r'\bvar\s+', line):
                issues.append(CodeIssue(
                    line_number=i,
                    column=line.find('var'),
                    severity='warning',
                    category='style',
                    message='Use "let" or "const" instead of "var"',
                    rule_id='no_var',
                    suggestion='Replace "var" with "let" or "const"'
                ))
        
        return issues
    
    def _get_python_metrics(self, content: str) -> Dict[str, Any]:
        """Get Python code metrics"""
        metrics = {
            'lines_of_code': len(content.split('\n')),
            'functions': 0,
            'classes': 0,
            'imports': 0
        }
        
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    metrics['functions'] += 1
                elif isinstance(node, ast.ClassDef):
                    metrics['classes'] += 1
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    metrics['imports'] += 1
        
        except SyntaxError:
            pass
        
        return metrics


class ComplexityVisitor(ast.NodeVisitor):
    """AST visitor to calculate cyclomatic complexity"""
    
    def __init__(self):
        self.complexities = []
        self.current_function = None
        self.current_complexity = 0
    
    def visit_FunctionDef(self, node):
        old_function = self.current_function
        old_complexity = self.current_complexity
        
        self.current_function = node.name
        self.current_complexity = 1  # Base complexity
        
        self.generic_visit(node)
        
        self.complexities.append((self.current_function, self.current_complexity, node.lineno))
        
        self.current_function = old_function
        self.current_complexity = old_complexity
    
    def visit_If(self, node):
        self.current_complexity += 1
        self.generic_visit(node)
    
    def visit_While(self, node):
        self.current_complexity += 1
        self.generic_visit(node)
    
    def visit_For(self, node):
        self.current_complexity += 1
        self.generic_visit(node)
    
    def visit_ExceptHandler(self, node):
        self.current_complexity += 1
        self.generic_visit(node)
    
    def visit_With(self, node):
        self.current_complexity += 1
        self.generic_visit(node)


class SecurityAnalyzer(BaseAnalyzer):
    """Analyzes code for security issues"""
    
    def can_analyze(self, file_path: str) -> bool:
        """Can analyze most programming languages"""
        return True
    
    def analyze(self, file_path: str, content: str) -> AnalysisResult:
        """Analyze code for security issues"""
        language = self.get_language(file_path)
        issues = []
        
        # Common security checks
        issues.extend(self._check_hardcoded_secrets(content))
        issues.extend(self._check_sql_injection(content))
        issues.extend(self._check_xss_vulnerabilities(content))
        
        # Language-specific checks
        if language == 'python':
            issues.extend(self._check_python_security(content))
        elif language in ['javascript', 'typescript']:
            issues.extend(self._check_js_security(content))
        
        return AnalysisResult(
            file_path=file_path,
            issues=issues,
            metrics={'security_issues': len(issues)},
            language=language
        )
    
    def _check_hardcoded_secrets(self, content: str) -> List[CodeIssue]:
        """Check for hardcoded secrets"""
        issues = []
        lines = content.split('\n')
        
        # Patterns for common secrets
        patterns = [
            (r'password\s*=\s*["\'][^"\']+["\']', 'hardcoded_password'),
            (r'api_key\s*=\s*["\'][^"\']+["\']', 'hardcoded_api_key'),
            (r'secret\s*=\s*["\'][^"\']+["\']', 'hardcoded_secret'),
            (r'token\s*=\s*["\'][^"\']+["\']', 'hardcoded_token'),
        ]
        
        for i, line in enumerate(lines, 1):
            for pattern, rule_id in patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(CodeIssue(
                        line_number=i,
                        column=0,
                        severity='error',
                        category='security',
                        message='Hardcoded secret detected',
                        rule_id=rule_id,
                        suggestion='Use environment variables or secure configuration'
                    ))
        
        return issues
    
    def _check_sql_injection(self, content: str) -> List[CodeIssue]:
        """Check for potential SQL injection vulnerabilities"""
        issues = []
        lines = content.split('\n')
        
        # Simple pattern matching for string concatenation in SQL
        sql_patterns = [
            r'SELECT.*\+.*',
            r'INSERT.*\+.*',
            r'UPDATE.*\+.*',
            r'DELETE.*\+.*',
        ]
        
        for i, line in enumerate(lines, 1):
            for pattern in sql_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(CodeIssue(
                        line_number=i,
                        column=0,
                        severity='error',
                        category='security',
                        message='Potential SQL injection vulnerability',
                        rule_id='sql_injection',
                        suggestion='Use parameterized queries or prepared statements'
                    ))
        
        return issues
    
    def _check_xss_vulnerabilities(self, content: str) -> List[CodeIssue]:
        """Check for XSS vulnerabilities"""
        issues = []
        lines = content.split('\n')
        
        # Look for innerHTML usage
        if re.search(r'innerHTML\s*=', content):
            for i, line in enumerate(lines, 1):
                if 'innerHTML' in line:
                    issues.append(CodeIssue(
                        line_number=i,
                        column=0,
                        severity='warning',
                        category='security',
                        message='Potential XSS vulnerability with innerHTML',
                        rule_id='xss_innerHTML',
                        suggestion='Use textContent or properly sanitize input'
                    ))
        
        return issues
    
    def _check_python_security(self, content: str) -> List[CodeIssue]:
        """Check Python-specific security issues"""
        issues = []
        lines = content.split('\n')
        
        # Check for eval usage
        for i, line in enumerate(lines, 1):
            if re.search(r'\beval\s*\(', line):
                issues.append(CodeIssue(
                    line_number=i,
                    column=0,
                    severity='error',
                    category='security',
                    message='Use of eval() is dangerous',
                    rule_id='dangerous_eval',
                    suggestion='Use ast.literal_eval() for safe evaluation or avoid eval()'
                ))
        
        return issues
    
    def _check_js_security(self, content: str) -> List[CodeIssue]:
        """Check JavaScript-specific security issues"""
        issues = []
        lines = content.split('\n')
        
        # Check for eval usage
        for i, line in enumerate(lines, 1):
            if re.search(r'\beval\s*\(', line):
                issues.append(CodeIssue(
                    line_number=i,
                    column=0,
                    severity='error',
                    category='security',
                    message='Use of eval() is dangerous',
                    rule_id='dangerous_eval',
                    suggestion='Avoid eval() or use safer alternatives'
                ))
        
        return issues


class PerformanceAnalyzer(BaseAnalyzer):
    """Analyzes code for performance issues"""
    
    def can_analyze(self, file_path: str) -> bool:
        """Can analyze most programming languages"""
        return True
    
    def analyze(self, file_path: str, content: str) -> AnalysisResult:
        """Analyze code for performance issues"""
        language = self.get_language(file_path)
        issues = []
        
        # Common performance checks
        issues.extend(self._check_inefficient_loops(content))
        
        # Language-specific checks
        if language == 'python':
            issues.extend(self._check_python_performance(content))
        elif language in ['javascript', 'typescript']:
            issues.extend(self._check_js_performance(content))
        
        return AnalysisResult(
            file_path=file_path,
            issues=issues,
            metrics={'performance_issues': len(issues)},
            language=language
        )
    
    def _check_inefficient_loops(self, content: str) -> List[CodeIssue]:
        """Check for inefficient loop patterns"""
        issues = []
        lines = content.split('\n')
        
        # Check for nested loops that might be inefficient
        nested_loop_count = 0
        for i, line in enumerate(lines, 1):
            if re.search(r'\bfor\b.*\bfor\b', line):
                issues.append(CodeIssue(
                    line_number=i,
                    column=0,
                    severity='warning',
                    category='performance',
                    message='Nested loops detected - consider optimization',
                    rule_id='nested_loops',
                    suggestion='Consider using more efficient algorithms or data structures'
                ))
        
        return issues
    
    def _check_python_performance(self, content: str) -> List[CodeIssue]:
        """Check Python-specific performance issues"""
        issues = []
        lines = content.split('\n')
        
        # Check for string concatenation in loops
        for i, line in enumerate(lines, 1):
            if 'for' in line and '+=' in line and any(quote in line for quote in ['"', "'"]):
                issues.append(CodeIssue(
                    line_number=i,
                    column=0,
                    severity='warning',
                    category='performance',
                    message='String concatenation in loop is inefficient',
                    rule_id='string_concat_loop',
                    suggestion='Use list.join() or f-strings for better performance'
                ))
        
        return issues
    
    def _check_js_performance(self, content: str) -> List[CodeIssue]:
        """Check JavaScript-specific performance issues"""
        issues = []
        lines = content.split('\n')
        
        # Check for document.getElementById in loops
        for i, line in enumerate(lines, 1):
            if 'for' in line and 'document.getElementById' in line:
                issues.append(CodeIssue(
                    line_number=i,
                    column=0,
                    severity='warning',
                    category='performance',
                    message='DOM queries in loops are inefficient',
                    rule_id='dom_query_loop',
                    suggestion='Cache DOM elements outside the loop'
                ))
        
        return issues
