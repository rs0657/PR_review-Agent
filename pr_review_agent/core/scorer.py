"""
PR scoring system for evaluating code quality
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import math

from ..analyzers.base import AnalysisResult, CodeIssue
from ..adapters.base import FileChange, PRInfo


@dataclass
class ScoreBreakdown:
    """Detailed breakdown of PR score"""
    overall_score: float
    category_scores: Dict[str, float]
    metrics: Dict[str, Any]
    grade: str
    summary: str


class PRScorer:
    """Calculates quality scores for pull requests"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.weights = self.config.get('weights', {
            'code_quality': 0.25,
            'test_coverage': 0.20,
            'documentation': 0.15,
            'security': 0.20,
            'performance': 0.10,
            'maintainability': 0.10
        })
        self.thresholds = self.config.get('thresholds', {
            'excellent': 90,
            'good': 75,
            'fair': 60,
            'poor': 40
        })
    
    def calculate_score(
        self,
        pr_info: PRInfo,
        file_changes: List[FileChange],
        analysis_results: Dict[str, List[AnalysisResult]]
    ) -> ScoreBreakdown:
        """Calculate comprehensive PR score"""
        
        # Calculate individual category scores
        category_scores = {
            'code_quality': self._calculate_code_quality_score(analysis_results),
            'test_coverage': self._calculate_test_coverage_score(file_changes),
            'documentation': self._calculate_documentation_score(file_changes, analysis_results),
            'security': self._calculate_security_score(analysis_results),
            'performance': self._calculate_performance_score(analysis_results),
            'maintainability': self._calculate_maintainability_score(pr_info, file_changes, analysis_results)
        }
        
        # Calculate weighted overall score
        overall_score = sum(
            score * self.weights.get(category, 0)
            for category, score in category_scores.items()
        )
        
        # Generate metrics
        metrics = self._generate_metrics(pr_info, file_changes, analysis_results)
        
        # Assign grade
        grade = self._assign_grade(overall_score)
        
        # Generate summary
        summary = self._generate_summary(overall_score, category_scores, metrics)
        
        return ScoreBreakdown(
            overall_score=round(overall_score, 1),
            category_scores={k: round(v, 1) for k, v in category_scores.items()},
            metrics=metrics,
            grade=grade,
            summary=summary
        )
    
    def _calculate_code_quality_score(self, analysis_results: Dict[str, List[AnalysisResult]]) -> float:
        """Calculate code quality score based on analysis results"""
        total_issues = 0
        total_lines = 0
        severity_weights = {'error': 3, 'warning': 2, 'info': 1}
        
        for file_results in analysis_results.values():
            for result in file_results:
                total_lines += result.metrics.get('lines_of_code', 100)
                
                for issue in result.issues:
                    # Weight issues by severity
                    weight = severity_weights.get(issue.severity, 1)
                    total_issues += weight
        
        if total_lines == 0:
            return 100.0
        
        # Calculate issues per 100 lines of code
        issues_per_100_lines = (total_issues / total_lines) * 100
        
        # Score decreases with more issues
        if issues_per_100_lines == 0:
            return 100.0
        elif issues_per_100_lines <= 1:
            return 95.0 - (issues_per_100_lines * 5)
        elif issues_per_100_lines <= 5:
            return 85.0 - ((issues_per_100_lines - 1) * 10)
        elif issues_per_100_lines <= 10:
            return 50.0 - ((issues_per_100_lines - 5) * 5)
        else:
            return max(0, 25.0 - ((issues_per_100_lines - 10) * 2))
    
    def _calculate_test_coverage_score(self, file_changes: List[FileChange]) -> float:
        """Calculate test coverage score based on test files"""
        total_files = len(file_changes)
        test_files = 0
        source_files = 0
        
        for change in file_changes:
            filename = change.filename.lower()
            
            # Count test files
            if any(pattern in filename for pattern in ['test_', '_test.', '/test/', '/tests/', '.test.', '.spec.']):
                test_files += 1
            # Count source files (excluding configs, docs, etc.)
            elif any(filename.endswith(ext) for ext in ['.py', '.js', '.ts', '.java', '.cpp', '.go']):
                if not any(pattern in filename for pattern in ['config', 'setup', '__init__']):
                    source_files += 1
        
        if source_files == 0:
            return 100.0  # No source files to test
        
        # Calculate test file ratio
        test_ratio = test_files / source_files if source_files > 0 else 0
        
        if test_ratio >= 1.0:
            return 100.0
        elif test_ratio >= 0.8:
            return 90.0 + (test_ratio - 0.8) * 50
        elif test_ratio >= 0.5:
            return 70.0 + (test_ratio - 0.5) * 66.7
        elif test_ratio >= 0.2:
            return 40.0 + (test_ratio - 0.2) * 100
        else:
            return test_ratio * 200  # Max 40 points for very low coverage
    
    def _calculate_documentation_score(
        self, 
        file_changes: List[FileChange], 
        analysis_results: Dict[str, List[AnalysisResult]]
    ) -> float:
        """Calculate documentation score"""
        doc_files = 0
        source_files = 0
        missing_docstrings = 0
        total_functions_classes = 0
        
        for change in file_changes:
            filename = change.filename.lower()
            
            # Count documentation files
            if any(pattern in filename for pattern in ['readme', '.md', '.rst', 'docs/', 'doc/']):
                doc_files += 1
            elif any(filename.endswith(ext) for ext in ['.py', '.js', '.ts', '.java']):
                source_files += 1
        
        # Count missing docstrings from analysis results
        for file_results in analysis_results.values():
            for result in file_results:
                total_functions_classes += result.metrics.get('functions', 0) + result.metrics.get('classes', 0)
                
                for issue in result.issues:
                    if issue.rule_id == 'missing_docstring':
                        missing_docstrings += 1
        
        # Base score from documentation files
        doc_score = min(100, doc_files * 25)
        
        # Deduct for missing docstrings
        if total_functions_classes > 0:
            docstring_ratio = 1 - (missing_docstrings / total_functions_classes)
            doc_score = doc_score * 0.7 + (docstring_ratio * 100 * 0.3)
        
        return min(100, doc_score)
    
    def _calculate_security_score(self, analysis_results: Dict[str, List[AnalysisResult]]) -> float:
        """Calculate security score based on security issues"""
        security_issues = 0
        total_files = len(analysis_results)
        
        for file_results in analysis_results.values():
            for result in file_results:
                for issue in result.issues:
                    if issue.category == 'security':
                        # Weight by severity
                        if issue.severity == 'error':
                            security_issues += 3
                        elif issue.severity == 'warning':
                            security_issues += 2
                        else:
                            security_issues += 1
        
        if total_files == 0:
            return 100.0
        
        # Calculate security issues per file
        issues_per_file = security_issues / total_files
        
        if issues_per_file == 0:
            return 100.0
        elif issues_per_file <= 0.5:
            return 90.0 - (issues_per_file * 20)
        elif issues_per_file <= 2:
            return 80.0 - ((issues_per_file - 0.5) * 30)
        else:
            return max(0, 35.0 - ((issues_per_file - 2) * 10))
    
    def _calculate_performance_score(self, analysis_results: Dict[str, List[AnalysisResult]]) -> float:
        """Calculate performance score based on performance issues"""
        performance_issues = 0
        total_files = len(analysis_results)
        
        for file_results in analysis_results.values():
            for result in file_results:
                for issue in result.issues:
                    if issue.category == 'performance':
                        if issue.severity == 'error':
                            performance_issues += 2
                        else:
                            performance_issues += 1
        
        if total_files == 0:
            return 100.0
        
        issues_per_file = performance_issues / total_files
        
        if issues_per_file == 0:
            return 100.0
        elif issues_per_file <= 1:
            return 85.0 - (issues_per_file * 15)
        elif issues_per_file <= 3:
            return 70.0 - ((issues_per_file - 1) * 20)
        else:
            return max(30, 30.0 - ((issues_per_file - 3) * 10))
    
    def _calculate_maintainability_score(
        self,
        pr_info: PRInfo,
        file_changes: List[FileChange],
        analysis_results: Dict[str, List[AnalysisResult]]
    ) -> float:
        """Calculate maintainability score"""
        score = 100.0
        
        # Factor 1: PR size (smaller is better)
        total_changes = pr_info.additions + pr_info.deletions
        if total_changes > 1000:
            score -= 30
        elif total_changes > 500:
            score -= 20
        elif total_changes > 200:
            score -= 10
        
        # Factor 2: Number of files changed
        if len(file_changes) > 20:
            score -= 20
        elif len(file_changes) > 10:
            score -= 10
        
        # Factor 3: Complexity issues
        complexity_issues = 0
        for file_results in analysis_results.values():
            for result in file_results:
                for issue in result.issues:
                    if issue.rule_id in ['high_complexity', 'too_many_arguments', 'nested_loops']:
                        complexity_issues += 1
        
        score -= complexity_issues * 5
        
        # Factor 4: Code structure issues
        structure_issues = 0
        for file_results in analysis_results.values():
            for result in file_results:
                for issue in result.issues:
                    if issue.category == 'maintainability':
                        structure_issues += 1
        
        score -= structure_issues * 3
        
        return max(0, score)
    
    def _generate_metrics(
        self,
        pr_info: PRInfo,
        file_changes: List[FileChange],
        analysis_results: Dict[str, List[AnalysisResult]]
    ) -> Dict[str, Any]:
        """Generate detailed metrics"""
        total_issues = sum(
            len(result.issues)
            for file_results in analysis_results.values()
            for result in file_results
        )
        
        issues_by_severity = {'error': 0, 'warning': 0, 'info': 0}
        issues_by_category = {}
        
        for file_results in analysis_results.values():
            for result in file_results:
                for issue in result.issues:
                    issues_by_severity[issue.severity] += 1
                    if issue.category not in issues_by_category:
                        issues_by_category[issue.category] = 0
                    issues_by_category[issue.category] += 1
        
        return {
            'total_files_changed': len(file_changes),
            'total_additions': pr_info.additions,
            'total_deletions': pr_info.deletions,
            'total_commits': pr_info.commits,
            'total_issues': total_issues,
            'issues_by_severity': issues_by_severity,
            'issues_by_category': issues_by_category,
            'files_analyzed': len(analysis_results)
        }
    
    def _assign_grade(self, score: float) -> str:
        """Assign letter grade based on score"""
        if score >= self.thresholds['excellent']:
            return 'A'
        elif score >= self.thresholds['good']:
            return 'B'
        elif score >= self.thresholds['fair']:
            return 'C'
        elif score >= self.thresholds['poor']:
            return 'D'
        else:
            return 'F'
    
    def _generate_summary(
        self,
        overall_score: float,
        category_scores: Dict[str, float],
        metrics: Dict[str, Any]
    ) -> str:
        """Generate a summary of the scoring"""
        grade = self._assign_grade(overall_score)
        
        # Find best and worst categories
        best_category = max(category_scores.items(), key=lambda x: x[1])
        worst_category = min(category_scores.items(), key=lambda x: x[1])
        
        summary = f"Grade: {grade} ({overall_score:.1f}/100)\n\n"
        
        if overall_score >= 90:
            summary += "Excellent work! This PR demonstrates high code quality standards."
        elif overall_score >= 75:
            summary += "Good quality PR with room for minor improvements."
        elif overall_score >= 60:
            summary += "Fair quality PR that needs some attention in key areas."
        else:
            summary += "This PR needs significant improvements before merging."
        
        summary += f"\n\nStrengths: {best_category[0].replace('_', ' ').title()} ({best_category[1]:.1f}/100)"
        summary += f"\nAreas for improvement: {worst_category[0].replace('_', ' ').title()} ({worst_category[1]:.1f}/100)"
        
        # Add key metrics
        summary += f"\n\nKey metrics:"
        summary += f"\n• {metrics['total_files_changed']} files changed"
        summary += f"\n• +{metrics['total_additions']}/-{metrics['total_deletions']} lines"
        summary += f"\n• {metrics['total_issues']} issues found"
        
        if metrics['issues_by_severity']['error'] > 0:
            summary += f"\n• {metrics['issues_by_severity']['error']} critical issues require attention"
        
        return summary
