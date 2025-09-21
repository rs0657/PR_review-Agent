"""
Main PR Reviewer class that coordinates all components
"""
from typing import Dict, List, Any, Optional
import logging

from .config import Config
from .ai_feedback import FeedbackManager, AIFeedback
from .scorer import PRScorer, ScoreBreakdown
from ..adapters.base import GitServerAdapter, AdapterFactory, ReviewSummary, ReviewComment
from ..analyzers.manager import AnalysisManager


class PRReviewer:
    """Main PR Review Agent that coordinates all components"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the PR Reviewer"""
        self.config = Config(config_path)
        self.analysis_manager = AnalysisManager(self.config.analysis.__dict__)
        self.feedback_manager = FeedbackManager(self.config.ai.__dict__)
        self.scorer = PRScorer(self.config.scoring.__dict__)
        self.logger = self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def review_pr(
        self,
        server_name: str,
        repository: str,
        pr_number: int,
        post_review: bool = True
    ) -> Dict[str, Any]:
        """
        Review a pull request
        
        Args:
            server_name: Name of the git server configuration
            repository: Repository name (e.g., 'owner/repo')
            pr_number: Pull request number
            post_review: Whether to post the review back to the server
            
        Returns:
            Dictionary containing review results
        """
        self.logger.info(f"Starting review of {repository}#{pr_number} on {server_name}")
        
        try:
            # Get server adapter
            adapter = self._get_server_adapter(server_name)
            
            # Get PR information
            self.logger.info("Fetching PR information...")
            pr_info = adapter.get_pr_info(repository, pr_number)
            
            # Get file changes
            self.logger.info("Fetching file changes...")
            file_changes = adapter.get_pr_files(repository, pr_number)
            
            # Analyze code
            self.logger.info("Analyzing code...")
            analysis_results = self._analyze_code(file_changes)
            
            # Generate AI feedback
            self.logger.info("Generating AI feedback...")
            ai_feedback = self.feedback_manager.generate_review_feedback(
                file_changes, analysis_results
            )
            
            # Calculate score
            self.logger.info("Calculating quality score...")
            score_breakdown = self.scorer.calculate_score(
                pr_info, file_changes, analysis_results
            )
            
            # Create review summary
            review_summary = self._create_review_summary(
                ai_feedback, score_breakdown, analysis_results
            )
            
            # Post review if requested
            if post_review:
                self.logger.info("Posting review...")
                success = adapter.post_review(repository, pr_number, review_summary)
                if success:
                    self.logger.info("Review posted successfully")
                else:
                    self.logger.error("Failed to post review")
            
            # Update PR status
            status = self._determine_status(score_breakdown, ai_feedback)
            adapter.update_pr_status(
                repository, 
                pr_number, 
                status, 
                f"PR Review Agent: {score_breakdown.grade} ({score_breakdown.overall_score:.1f}/100)"
            )
            
            return {
                'success': True,
                'pr_info': pr_info,
                'file_changes': file_changes,
                'analysis_results': analysis_results,
                'ai_feedback': ai_feedback,
                'score_breakdown': score_breakdown,
                'review_summary': review_summary,
                'posted': post_review
            }
            
        except Exception as e:
            self.logger.error(f"Error reviewing PR: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def analyze_files(self, files: Dict[str, str]) -> Dict[str, Any]:
        """
        Analyze a set of files without posting to a server
        
        Args:
            files: Dictionary mapping file paths to file contents
            
        Returns:
            Analysis results
        """
        self.logger.info(f"Analyzing {len(files)} files...")
        
        try:
            # Analyze code
            analysis_results = self.analysis_manager.analyze_files(files)
            
            # Generate summary metrics
            summary_metrics = self.analysis_manager.get_summary_metrics(analysis_results)
            
            return {
                'success': True,
                'analysis_results': analysis_results,
                'summary_metrics': summary_metrics
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing files: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_server_status(self, server_name: str) -> Dict[str, Any]:
        """
        Check the status of a git server connection
        
        Args:
            server_name: Name of the server configuration
            
        Returns:
            Status information
        """
        try:
            adapter = self._get_server_adapter(server_name)
            is_connected = adapter.validate_connection()
            
            return {
                'server_name': server_name,
                'connected': is_connected,
                'config': self.config.get_server_config(server_name)
            }
            
        except Exception as e:
            return {
                'server_name': server_name,
                'connected': False,
                'error': str(e)
            }
    
    def list_supported_servers(self) -> List[str]:
        """Get list of supported git server types"""
        return AdapterFactory.get_supported_servers()
    
    def _get_server_adapter(self, server_name: str) -> GitServerAdapter:
        """Get server adapter instance"""
        server_config = self.config.get_server_config(server_name)
        if not server_config:
            raise ValueError(f"No configuration found for server: {server_name}")
        
        return AdapterFactory.create_adapter(
            server_config.type,
            server_config.base_url,
            server_config.token,
            timeout=server_config.timeout
        )
    
    def _analyze_code(self, file_changes: List[Any]) -> Dict[str, List[Any]]:
        """Analyze code in file changes"""
        files_to_analyze = {}
        
        for change in file_changes:
            if change.content_after:  # Only analyze files that have content
                files_to_analyze[change.filename] = change.content_after
        
        return self.analysis_manager.analyze_files(files_to_analyze)
    
    def _create_review_summary(
        self,
        ai_feedback: AIFeedback,
        score_breakdown: ScoreBreakdown,
        analysis_results: Dict[str, List[Any]]
    ) -> ReviewSummary:
        """Create a comprehensive review summary"""
        
        # Combine AI feedback comments with analysis issues
        all_comments = list(ai_feedback.inline_comments)
        
        # Add comments for high-priority issues not covered by AI
        for file_path, results in analysis_results.items():
            for result in results:
                for issue in result.issues:
                    if issue.severity == 'error':
                        # Check if this issue is already covered by AI feedback
                        existing_comment = any(
                            comment.file_path == file_path and 
                            comment.line_number == issue.line_number
                            for comment in all_comments
                        )
                        
                        if not existing_comment:
                            all_comments.append(ReviewComment(
                                file_path=file_path,
                                line_number=issue.line_number,
                                message=issue.message,
                                severity=issue.severity,
                                suggestion=issue.suggestion,
                                category=issue.category
                            ))
        
        # Create comprehensive summary message
        summary_message = f"""## 🤖 PR Review Agent Analysis

{ai_feedback.summary}

### 📊 Quality Score: {score_breakdown.overall_score:.1f}/100 (Grade: {score_breakdown.grade})

{score_breakdown.summary}

### 🎯 Category Breakdown:
"""
        
        for category, score in score_breakdown.category_scores.items():
            emoji = "✅" if score >= 80 else "⚠️" if score >= 60 else "❌"
            summary_message += f"- {emoji} **{category.replace('_', ' ').title()}**: {score:.1f}/100\n"
        
        if ai_feedback.suggestions:
            summary_message += "\n### 💡 Key Suggestions:\n"
            for i, suggestion in enumerate(ai_feedback.suggestions, 1):
                summary_message += f"{i}. {suggestion}\n"
        
        summary_message += f"\n### 📈 Detailed Assessment:\n{ai_feedback.overall_assessment}"
        
        # Determine recommendation based on score and AI feedback
        if score_breakdown.overall_score >= 85 and ai_feedback.recommendation != 'request_changes':
            recommendation = 'approve'
        elif score_breakdown.overall_score < 60 or score_breakdown.category_scores.get('security', 100) < 70:
            recommendation = 'request_changes'
        else:
            recommendation = 'comment'
        
        return ReviewSummary(
            overall_score=score_breakdown.overall_score,
            comments=all_comments,
            summary_message=summary_message,
            recommendation=recommendation
        )
    
    def _determine_status(self, score_breakdown: ScoreBreakdown, ai_feedback: AIFeedback) -> str:
        """Determine PR status based on score and feedback"""
        if score_breakdown.overall_score >= 85:
            return 'success'
        elif score_breakdown.overall_score >= 70:
            return 'pending'
        else:
            return 'failure'
    
    def configure_server(
        self,
        name: str,
        server_type: str,
        base_url: str,
        token: str,
        **kwargs
    ) -> bool:
        """
        Add or update server configuration
        
        Args:
            name: Server configuration name
            server_type: Type of server (github, gitlab, bitbucket)
            base_url: Base URL for the server API
            token: Authentication token
            **kwargs: Additional configuration options
            
        Returns:
            True if successful, False otherwise
        """
        try:
            from .config import ServerConfig
            
            server_config = ServerConfig(
                base_url=base_url,
                token=token,
                type=server_type,
                **kwargs
            )
            
            self.config.add_server(name, server_config)
            self.config.save_config()
            
            self.logger.info(f"Added server configuration: {name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error configuring server: {e}")
            return False
    
    def update_analysis_config(self, **kwargs) -> bool:
        """Update analysis configuration"""
        try:
            for key, value in kwargs.items():
                if hasattr(self.config.analysis, key):
                    setattr(self.config.analysis, key, value)
            
            self.config.save_config()
            
            # Recreate analysis manager with new config
            self.analysis_manager = AnalysisManager(self.config.analysis.__dict__)
            
            self.logger.info("Updated analysis configuration")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating analysis config: {e}")
            return False
    
    def update_ai_config(self, **kwargs) -> bool:
        """Update AI configuration"""
        try:
            for key, value in kwargs.items():
                if hasattr(self.config.ai, key):
                    setattr(self.config.ai, key, value)
            
            self.config.save_config()
            
            # Recreate feedback manager with new config
            self.feedback_manager = FeedbackManager(self.config.ai.__dict__)
            
            self.logger.info("Updated AI configuration")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating AI config: {e}")
            return False
