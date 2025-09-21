"""
Code analysis manager that coordinates different analyzers
"""
from typing import List, Dict, Any, Optional
import fnmatch
from .base import BaseAnalyzer, AnalysisResult, StructureAnalyzer, SecurityAnalyzer, PerformanceAnalyzer


class AnalysisManager:
    """Manages and coordinates different code analyzers"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.analyzers: List[BaseAnalyzer] = []
        self._register_default_analyzers()
    
    def _register_default_analyzers(self):
        """Register the default set of analyzers"""
        enabled_analyzers = self.config.get('enabled_analyzers', [
            'structure', 'security', 'performance'
        ])
        
        if 'structure' in enabled_analyzers:
            self.analyzers.append(StructureAnalyzer(self.config))
        
        if 'security' in enabled_analyzers:
            self.analyzers.append(SecurityAnalyzer(self.config))
        
        if 'performance' in enabled_analyzers:
            self.analyzers.append(PerformanceAnalyzer(self.config))
    
    def add_analyzer(self, analyzer: BaseAnalyzer):
        """Add a custom analyzer"""
        self.analyzers.append(analyzer)
    
    def should_analyze_file(self, file_path: str) -> bool:
        """Check if file should be analyzed based on filters"""
        # Check file size limit
        max_size = self.config.get('max_file_size', 1024 * 1024)  # 1MB default
        
        # Check exclude patterns
        exclude_patterns = self.config.get('exclude_patterns', [])
        for pattern in exclude_patterns:
            if fnmatch.fnmatch(file_path, pattern):
                return False
        
        return True
    
    def analyze_file(self, file_path: str, content: str) -> List[AnalysisResult]:
        """Analyze a single file with all applicable analyzers"""
        if not self.should_analyze_file(file_path):
            return []
        
        results = []
        
        for analyzer in self.analyzers:
            if analyzer.can_analyze(file_path):
                try:
                    result = analyzer.analyze(file_path, content)
                    results.append(result)
                except Exception as e:
                    print(f"Error analyzing {file_path} with {type(analyzer).__name__}: {e}")
        
        return results
    
    def analyze_files(self, files: Dict[str, str]) -> Dict[str, List[AnalysisResult]]:
        """Analyze multiple files"""
        all_results = {}
        
        for file_path, content in files.items():
            results = self.analyze_file(file_path, content)
            if results:
                all_results[file_path] = results
        
        return all_results
    
    def get_summary_metrics(self, results: Dict[str, List[AnalysisResult]]) -> Dict[str, Any]:
        """Generate summary metrics from analysis results"""
        total_issues = 0
        issues_by_severity = {'error': 0, 'warning': 0, 'info': 0}
        issues_by_category = {}
        files_analyzed = len(results)
        
        for file_results in results.values():
            for result in file_results:
                for issue in result.issues:
                    total_issues += 1
                    issues_by_severity[issue.severity] += 1
                    
                    if issue.category not in issues_by_category:
                        issues_by_category[issue.category] = 0
                    issues_by_category[issue.category] += 1
        
        return {
            'total_issues': total_issues,
            'files_analyzed': files_analyzed,
            'issues_by_severity': issues_by_severity,
            'issues_by_category': issues_by_category,
            'quality_score': self._calculate_quality_score(total_issues, files_analyzed)
        }
    
    def _calculate_quality_score(self, total_issues: int, files_analyzed: int) -> float:
        """Calculate an overall quality score"""
        if files_analyzed == 0:
            return 100.0
        
        # Base score starts at 100
        base_score = 100.0
        
        # Deduct points based on issues per file
        issues_per_file = total_issues / files_analyzed
        
        # More aggressive deduction for more issues
        if issues_per_file > 10:
            deduction = 50 + (issues_per_file - 10) * 2
        elif issues_per_file > 5:
            deduction = 30 + (issues_per_file - 5) * 4
        elif issues_per_file > 2:
            deduction = 15 + (issues_per_file - 2) * 5
        else:
            deduction = issues_per_file * 7.5
        
        score = max(0, base_score - deduction)
        return round(score, 1)
