"""
Unit tests for PR scoring system
"""
import pytest
from unittest.mock import Mock
from datetime import datetime
from pr_review_agent.core.scorer import PRScorer, ScoreBreakdown
from pr_review_agent.adapters.base import PRInfo, FileChange
from pr_review_agent.analyzers.base import AnalysisResult, CodeIssue


class TestPRScorer:
    """Test PR scoring functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.scorer = PRScorer()
    
    def create_mock_pr_info(self, **kwargs):
        """Create mock PR info for testing"""
        defaults = {
            'id': '123',
            'number': 1,
            'title': 'Test PR',
            'description': 'Test description',
            'author': 'testuser',
            'source_branch': 'feature',
            'target_branch': 'main',
            'status': 'open',
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'url': 'https://example.com/pr/1',
            'repository': 'owner/repo',
            'files_changed': ['test.py'],
            'additions': 10,
            'deletions': 5,
            'commits': 1
        }
        defaults.update(kwargs)
        return PRInfo(**defaults)
    
    def create_mock_file_change(self, **kwargs):
        """Create mock file change for testing"""
        defaults = {
            'filename': 'test.py',
            'status': 'modified',
            'additions': 5,
            'deletions': 2,
            'patch': '@@ -1,3 +1,3 @@',
            'content_before': 'old content',
            'content_after': 'new content'
        }
        defaults.update(kwargs)
        return FileChange(**defaults)
    
    def create_mock_analysis_result(self, issues=None, **kwargs):
        """Create mock analysis result for testing"""
        if issues is None:
            issues = []
        
        defaults = {
            'file_path': 'test.py',
            'issues': issues,
            'metrics': {'lines_of_code': 100, 'functions': 5, 'classes': 1},
            'language': 'python'
        }
        defaults.update(kwargs)
        return AnalysisResult(**defaults)
    
    def create_code_issue(self, **kwargs):
        """Create code issue for testing"""
        defaults = {
            'line_number': 10,
            'column': 5,
            'severity': 'warning',
            'category': 'style',
            'message': 'Test issue',
            'rule_id': 'test_rule'
        }
        defaults.update(kwargs)
        return CodeIssue(**defaults)
    
    def test_calculate_score_perfect_code(self):
        """Test scoring perfect code with no issues"""
        pr_info = self.create_mock_pr_info()
        file_changes = [self.create_mock_file_change()]
        analysis_results = {
            'test.py': [self.create_mock_analysis_result()]
        }
        
        score_breakdown = self.scorer.calculate_score(pr_info, file_changes, analysis_results)
        
        assert isinstance(score_breakdown, ScoreBreakdown)
        assert score_breakdown.overall_score >= 90  # Should be high for perfect code
        assert score_breakdown.grade == 'A'
        assert len(score_breakdown.category_scores) == 6  # All categories
    
    def test_calculate_score_with_security_issues(self):
        """Test scoring code with security issues"""
        security_issue = self.create_code_issue(
            severity='error',
            category='security',
            rule_id='hardcoded_password'
        )
        
        pr_info = self.create_mock_pr_info()
        file_changes = [self.create_mock_file_change()]
        analysis_results = {
            'test.py': [self.create_mock_analysis_result(issues=[security_issue])]
        }
        
        score_breakdown = self.scorer.calculate_score(pr_info, file_changes, analysis_results)
        
        # Security score should be lower
        assert score_breakdown.category_scores['security'] < 90
        assert score_breakdown.overall_score < 90
    
    def test_calculate_score_large_pr(self):
        """Test scoring large PR with many changes"""
        pr_info = self.create_mock_pr_info(
            additions=1000,
            deletions=500,
            commits=20
        )
        
        # Create many file changes
        file_changes = [
            self.create_mock_file_change(filename=f'file{i}.py')
            for i in range(25)  # More than 20 files
        ]
        
        analysis_results = {
            f'file{i}.py': [self.create_mock_analysis_result()]
            for i in range(25)
        }
        
        score_breakdown = self.scorer.calculate_score(pr_info, file_changes, analysis_results)
        
        # Maintainability score should be lower for large PRs
        assert score_breakdown.category_scores['maintainability'] < 90
    
    def test_calculate_test_coverage_score(self):
        """Test test coverage scoring"""
        # Create mix of source and test files
        file_changes = [
            self.create_mock_file_change(filename='src/main.py'),
            self.create_mock_file_change(filename='src/utils.py'),
            self.create_mock_file_change(filename='tests/test_main.py'),
            self.create_mock_file_change(filename='tests/test_utils.py')
        ]
        
        score = self.scorer._calculate_test_coverage_score(file_changes)
        
        # Should have good test coverage (2 test files for 2 source files)
        assert score >= 90
    
    def test_calculate_test_coverage_score_no_tests(self):
        """Test test coverage scoring with no test files"""
        file_changes = [
            self.create_mock_file_change(filename='src/main.py'),
            self.create_mock_file_change(filename='src/utils.py')
        ]
        
        score = self.scorer._calculate_test_coverage_score(file_changes)
        
        # Should have low test coverage (no test files)
        assert score < 50
    
    def test_calculate_documentation_score(self):
        """Test documentation scoring"""
        file_changes = [
            self.create_mock_file_change(filename='README.md'),
            self.create_mock_file_change(filename='docs/api.md'),
            self.create_mock_file_change(filename='src/main.py')
        ]
        
        # No missing docstring issues
        analysis_results = {
            'src/main.py': [self.create_mock_analysis_result()]
        }
        
        score = self.scorer._calculate_documentation_score(file_changes, analysis_results)
        
        # Should have good documentation score
        assert score >= 70
    
    def test_assign_grade(self):
        """Test grade assignment"""
        assert self.scorer._assign_grade(95) == 'A'
        assert self.scorer._assign_grade(85) == 'B'
        assert self.scorer._assign_grade(70) == 'C'
        assert self.scorer._assign_grade(50) == 'D'
        assert self.scorer._assign_grade(30) == 'F'
    
    def test_generate_metrics(self):
        """Test metrics generation"""
        issues = [
            self.create_code_issue(severity='error'),
            self.create_code_issue(severity='warning'),
            self.create_code_issue(severity='info')
        ]
        
        pr_info = self.create_mock_pr_info()
        file_changes = [self.create_mock_file_change()]
        analysis_results = {
            'test.py': [self.create_mock_analysis_result(issues=issues)]
        }
        
        metrics = self.scorer._generate_metrics(pr_info, file_changes, analysis_results)
        
        assert metrics['total_files_changed'] == 1
        assert metrics['total_additions'] == 10
        assert metrics['total_deletions'] == 5
        assert metrics['total_issues'] == 3
        assert metrics['issues_by_severity']['error'] == 1
        assert metrics['issues_by_severity']['warning'] == 1
        assert metrics['issues_by_severity']['info'] == 1
    
    def test_generate_summary(self):
        """Test summary generation"""
        category_scores = {
            'code_quality': 85.0,
            'security': 90.0,
            'test_coverage': 70.0,
            'documentation': 80.0,
            'performance': 75.0,
            'maintainability': 88.0
        }
        
        metrics = {
            'total_files_changed': 5,
            'total_additions': 100,
            'total_deletions': 50,
            'total_issues': 10,
            'issues_by_severity': {'error': 2, 'warning': 5, 'info': 3}
        }
        
        summary = self.scorer._generate_summary(82.0, category_scores, metrics)
        
        assert 'Grade: B (82.0/100)' in summary
        assert 'Good quality PR' in summary
        assert 'Strengths: Security (90.0/100)' in summary
        assert 'Areas for improvement: Test Coverage (70.0/100)' in summary
        assert '5 files changed' in summary
        assert '2 critical issues' in summary
    
    def test_custom_weights(self):
        """Test scorer with custom weights"""
        custom_weights = {
            'code_quality': 0.5,  # Give more weight to code quality
            'security': 0.3,
            'test_coverage': 0.1,
            'documentation': 0.05,
            'performance': 0.03,
            'maintainability': 0.02
        }
        
        custom_scorer = PRScorer({'weights': custom_weights})
        
        pr_info = self.create_mock_pr_info()
        file_changes = [self.create_mock_file_change()]
        analysis_results = {'test.py': [self.create_mock_analysis_result()]}
        
        score_breakdown = custom_scorer.calculate_score(pr_info, file_changes, analysis_results)
        
        # Weights should be applied correctly
        assert custom_scorer.weights['code_quality'] == 0.5
        assert isinstance(score_breakdown.overall_score, float)
    
    def test_score_breakdown_fields(self):
        """Test that ScoreBreakdown has all required fields"""
        pr_info = self.create_mock_pr_info()
        file_changes = [self.create_mock_file_change()]
        analysis_results = {'test.py': [self.create_mock_analysis_result()]}
        
        score_breakdown = self.scorer.calculate_score(pr_info, file_changes, analysis_results)
        
        assert hasattr(score_breakdown, 'overall_score')
        assert hasattr(score_breakdown, 'category_scores')
        assert hasattr(score_breakdown, 'metrics')
        assert hasattr(score_breakdown, 'grade')
        assert hasattr(score_breakdown, 'summary')
        
        assert isinstance(score_breakdown.overall_score, float)
        assert isinstance(score_breakdown.category_scores, dict)
        assert isinstance(score_breakdown.metrics, dict)
        assert isinstance(score_breakdown.grade, str)
        assert isinstance(score_breakdown.summary, str)


if __name__ == "__main__":
    pytest.main([__file__])
