"""
AI-powered feedback system for generating intelligent code review comments
"""
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import re

from ..adapters.base import ReviewComment, FileChange
from ..analyzers.base import AnalysisResult, CodeIssue


@dataclass
class AIFeedback:
    """AI-generated feedback for code review"""
    summary: str
    suggestions: List[str]
    inline_comments: List[ReviewComment]
    overall_assessment: str
    recommendation: str  # approve, request_changes, comment


class BaseFeedbackProvider:
    """Base class for AI feedback providers"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
    
    def generate_feedback(
        self, 
        file_changes: List[FileChange], 
        analysis_results: Dict[str, List[AnalysisResult]]
    ) -> AIFeedback:
        """Generate AI feedback based on file changes and analysis results"""
        raise NotImplementedError
    
    def generate_inline_comment(self, issue: CodeIssue, context: str) -> ReviewComment:
        """Generate an inline comment for a specific issue"""
        raise NotImplementedError


class OpenAIFeedbackProvider(BaseFeedbackProvider):
    """OpenAI-based feedback provider"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.api_key = config.get('api_key') if config else None
        self.model = config.get('model', 'gpt-4') if config else 'gpt-4'
        self.max_tokens = config.get('max_tokens', 1500) if config else 1500
        self.temperature = config.get('temperature', 0.3) if config else 0.3
        
        if self.api_key:
            try:
                import openai
                self.client = openai.OpenAI(api_key=self.api_key)
            except ImportError:
                # Silently handle missing OpenAI - let CLI provide better error messages
                self.client = None
        else:
            self.client = None
    
    def generate_feedback(
        self, 
        file_changes: List[FileChange], 
        analysis_results: Dict[str, List[AnalysisResult]]
    ) -> AIFeedback:
        """Generate comprehensive AI feedback"""
        
        if not self.client:
            return self._generate_fallback_feedback(file_changes, analysis_results)
        
        # Prepare context for AI
        context = self._prepare_context(file_changes, analysis_results)
        
        try:
            # Generate main feedback
            main_feedback = self._generate_main_feedback(context)
            
            # Generate inline comments
            inline_comments = self._generate_inline_comments(analysis_results)
            
            # Parse AI response
            feedback = self._parse_ai_response(main_feedback, inline_comments)
            
            return feedback
            
        except Exception as e:
            print(f"Error generating AI feedback: {e}")
            return self._generate_fallback_feedback(file_changes, analysis_results)
    
    def _prepare_context(
        self, 
        file_changes: List[FileChange], 
        analysis_results: Dict[str, List[AnalysisResult]]
    ) -> str:
        """Prepare context string for AI analysis"""
        context = "# Pull Request Analysis\n\n"
        
        # File changes summary
        context += "## Changed Files:\n"
        for change in file_changes:
            context += f"- {change.filename} ({change.status}): +{change.additions}/-{change.deletions}\n"
        
        context += "\n## Code Analysis Results:\n"
        
        # Analysis results summary
        total_issues = 0
        for file_path, results in analysis_results.items():
            file_issues = []
            for result in results:
                file_issues.extend(result.issues)
            
            if file_issues:
                context += f"\n### {file_path}:\n"
                for issue in file_issues[:5]:  # Limit to top 5 issues per file
                    context += f"- Line {issue.line_number}: {issue.severity.upper()} - {issue.message}\n"
                
                if len(file_issues) > 5:
                    context += f"- ... and {len(file_issues) - 5} more issues\n"
                
                total_issues += len(file_issues)
        
        context += f"\n**Total Issues Found:** {total_issues}\n"
        
        # Add relevant code snippets for high-severity issues
        context += "\n## Key Code Snippets:\n"
        snippet_count = 0
        for file_path, results in analysis_results.items():
            for result in results:
                for issue in result.issues:
                    if issue.severity == 'error' and snippet_count < 3:
                        # Find the corresponding file change
                        file_change = next((fc for fc in file_changes if fc.filename == file_path), None)
                        if file_change and file_change.content_after:
                            lines = file_change.content_after.split('\n')
                            if issue.line_number <= len(lines):
                                start_line = max(0, issue.line_number - 3)
                                end_line = min(len(lines), issue.line_number + 2)
                                snippet = '\n'.join(lines[start_line:end_line])
                                context += f"\n### {file_path} (Line {issue.line_number}):\n```\n{snippet}\n```\n"
                                snippet_count += 1
        
        return context
    
    def _generate_main_feedback(self, context: str) -> str:
        """Generate main feedback using OpenAI"""
        
        prompt = f"""You are an expert code reviewer. Analyze the following pull request and provide constructive feedback.

{context}

Please provide a comprehensive review in the following JSON format:
{{
    "summary": "Brief summary of the changes and overall quality",
    "suggestions": ["List of specific suggestions for improvement"],
    "overall_assessment": "Detailed assessment of code quality, design, and implementation",
    "recommendation": "approve/request_changes/comment"
}}

Focus on:
1. Code quality and best practices
2. Security vulnerabilities
3. Performance implications
4. Maintainability and readability
5. Architecture and design patterns

Be constructive and specific in your feedback."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert code reviewer providing constructive feedback."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            return self._generate_template_feedback(context)
    
    def _generate_inline_comments(self, analysis_results: Dict[str, List[AnalysisResult]]) -> List[ReviewComment]:
        """Generate inline comments for specific issues"""
        comments = []
        
        for file_path, results in analysis_results.items():
            for result in results:
                for issue in result.issues:
                    if issue.severity in ['error', 'warning']:
                        # Generate enhanced comment with AI if available
                        comment = self.generate_inline_comment(issue, "")
                        comments.append(comment)
        
        return comments
    
    def generate_inline_comment(self, issue: CodeIssue, context: str) -> ReviewComment:
        """Generate an AI-enhanced inline comment"""
        
        if not self.client:
            return self._generate_basic_comment(issue)
        
        try:
            prompt = f"""Improve this code review comment to be more helpful and constructive:

Issue: {issue.message}
Severity: {issue.severity}
Category: {issue.category}
Rule: {issue.rule_id}

Provide a better explanation and specific suggestion for fixing this issue. Be concise but helpful."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are helping improve code review comments to be more constructive and helpful."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.3
            )
            
            enhanced_message = response.choices[0].message.content.strip()
            
            return ReviewComment(
                file_path=issue.file_path if hasattr(issue, 'file_path') else '',
                line_number=issue.line_number,
                message=enhanced_message,
                severity=issue.severity,
                suggestion=issue.suggestion,
                category=issue.category
            )
            
        except Exception:
            return self._generate_basic_comment(issue)
    
    def _generate_basic_comment(self, issue: CodeIssue) -> ReviewComment:
        """Generate a basic comment without AI enhancement"""
        return ReviewComment(
            file_path=issue.file_path if hasattr(issue, 'file_path') else '',
            line_number=issue.line_number,
            message=issue.message,
            severity=issue.severity,
            suggestion=issue.suggestion,
            category=issue.category
        )
    
    def _parse_ai_response(self, ai_response: str, inline_comments: List[ReviewComment]) -> AIFeedback:
        """Parse AI response into structured feedback"""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                feedback_data = json.loads(json_match.group())
                
                return AIFeedback(
                    summary=feedback_data.get('summary', 'AI analysis completed'),
                    suggestions=feedback_data.get('suggestions', []),
                    inline_comments=inline_comments,
                    overall_assessment=feedback_data.get('overall_assessment', ''),
                    recommendation=feedback_data.get('recommendation', 'comment')
                )
        except json.JSONDecodeError:
            pass
        
        # Fallback parsing
        return AIFeedback(
            summary="AI-powered code review completed",
            suggestions=["Review the highlighted issues", "Consider the security implications"],
            inline_comments=inline_comments,
            overall_assessment=ai_response,
            recommendation="comment"
        )
    
    def _generate_template_feedback(self, context: str) -> str:
        """Generate template feedback when AI is not available"""
        return json.dumps({
            "summary": "Automated code analysis completed",
            "suggestions": [
                "Address high-severity security issues",
                "Review code structure and complexity",
                "Ensure proper error handling"
            ],
            "overall_assessment": "The code has been analyzed for common issues. Please review the inline comments for specific improvements.",
            "recommendation": "comment"
        })
    
    def _generate_fallback_feedback(
        self, 
        file_changes: List[FileChange], 
        analysis_results: Dict[str, List[AnalysisResult]]
    ) -> AIFeedback:
        """Generate fallback feedback when AI is not available"""
        
        total_issues = sum(len(issues) for results in analysis_results.values() for result in results for issues in [result.issues])
        
        # Count issues by severity
        severity_counts = {'error': 0, 'warning': 0, 'info': 0}
        for results in analysis_results.values():
            for result in results:
                for issue in result.issues:
                    severity_counts[issue.severity] += 1
        
        # Generate basic suggestions
        suggestions = []
        if severity_counts['error'] > 0:
            suggestions.append(f"Address {severity_counts['error']} critical error(s)")
        if severity_counts['warning'] > 0:
            suggestions.append(f"Review {severity_counts['warning']} warning(s)")
        if len(file_changes) > 10:
            suggestions.append("Consider breaking large changes into smaller PRs")
        
        # Generate inline comments
        inline_comments = []
        for results in analysis_results.values():
            for result in results:
                for issue in result.issues:
                    inline_comments.append(self._generate_basic_comment(issue))
        
        return AIFeedback(
            summary=f"Found {total_issues} issues across {len(file_changes)} files",
            suggestions=suggestions,
            inline_comments=inline_comments,
            overall_assessment="Automated analysis completed. Please review the identified issues.",
            recommendation="request_changes" if severity_counts['error'] > 0 else "comment"
        )


class HuggingFaceFeedbackProvider(BaseFeedbackProvider):
    """Hugging Face transformer-based feedback provider"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.model_name = config.get('model', 'microsoft/DialoGPT-large') if config else 'microsoft/DialoGPT-large'
        
        try:
            from transformers import pipeline
            self.generator = pipeline('text-generation', model=self.model_name)
        except ImportError:
            print("Transformers library not available. Install with: pip install transformers torch")
            self.generator = None
    
    def generate_feedback(
        self, 
        file_changes: List[FileChange], 
        analysis_results: Dict[str, List[AnalysisResult]]
    ) -> AIFeedback:
        """Generate feedback using Hugging Face transformers"""
        
        if not self.generator:
            return self._generate_fallback_feedback(file_changes, analysis_results)
        
        # Create a simplified prompt for the model
        context = self._create_simple_context(file_changes, analysis_results)
        
        try:
            prompt = f"Code review for changes: {context}\n\nReview summary:"
            
            response = self.generator(
                prompt,
                max_length=200,
                num_return_sequences=1,
                temperature=0.7
            )
            
            generated_text = response[0]['generated_text']
            summary = generated_text.replace(prompt, '').strip()
            
            # Generate inline comments
            inline_comments = []
            for results in analysis_results.values():
                for result in results:
                    for issue in result.issues:
                        inline_comments.append(self._generate_basic_comment(issue))
            
            return AIFeedback(
                summary=summary or "Code analysis completed",
                suggestions=["Review highlighted issues", "Consider best practices"],
                inline_comments=inline_comments,
                overall_assessment="Automated review using local AI model",
                recommendation="comment"
            )
            
        except Exception as e:
            print(f"Error with Hugging Face model: {e}")
            return self._generate_fallback_feedback(file_changes, analysis_results)
    
    def _create_simple_context(
        self, 
        file_changes: List[FileChange], 
        analysis_results: Dict[str, List[AnalysisResult]]
    ) -> str:
        """Create a simple context for the model"""
        files = [change.filename for change in file_changes]
        total_issues = sum(len(issues) for results in analysis_results.values() for result in results for issues in [result.issues])
        
        return f"{len(files)} files changed, {total_issues} issues found"


class FeedbackManager:
    """Manages AI feedback generation"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.provider = self._create_provider()
    
    def _create_provider(self) -> BaseFeedbackProvider:
        """Create appropriate feedback provider based on configuration"""
        provider_type = self.config.get('provider', 'openai')
        
        if provider_type == 'openai':
            return OpenAIFeedbackProvider(self.config)
        elif provider_type == 'huggingface':
            return HuggingFaceFeedbackProvider(self.config)
        else:
            print(f"Unknown provider: {provider_type}, using OpenAI")
            return OpenAIFeedbackProvider(self.config)
    
    def generate_review_feedback(
        self, 
        file_changes: List[FileChange], 
        analysis_results: Dict[str, List[AnalysisResult]]
    ) -> AIFeedback:
        """Generate comprehensive review feedback"""
        return self.provider.generate_feedback(file_changes, analysis_results)
    
    def enhance_comment(self, issue: CodeIssue, context: str = "") -> ReviewComment:
        """Enhance a single comment with AI"""
        return self.provider.generate_inline_comment(issue, context)
