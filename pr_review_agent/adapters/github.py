"""
GitHub adapter for PR Review Agent
"""
import requests
from typing import List, Optional
from datetime import datetime
from github import Github, GithubException
import base64

from .base import (
    GitServerAdapter, AdapterFactory, PRInfo, FileChange, 
    ReviewComment, ReviewSummary
)


class GitHubAdapter(GitServerAdapter):
    """GitHub adapter implementation"""
    
    def __init__(self, base_url: str, token: str, timeout: int = 30):
        super().__init__(base_url, token, timeout)
        self.github = Github(token, base_url=base_url if base_url != "https://api.github.com" else None)
    
    def get_pr_info(self, repository: str, pr_number: int) -> PRInfo:
        """Get pull request information from GitHub"""
        try:
            repo = self.github.get_repo(repository)
            pr = repo.get_pull(pr_number)
            
            return PRInfo(
                id=str(pr.id),
                number=pr.number,
                title=pr.title,
                description=pr.body or "",
                author=pr.user.login,
                source_branch=pr.head.ref,
                target_branch=pr.base.ref,
                status="open" if pr.state == "open" else "closed",
                created_at=pr.created_at,
                updated_at=pr.updated_at,
                url=pr.html_url,
                repository=repository,
                files_changed=[f.filename for f in pr.get_files()],
                additions=pr.additions,
                deletions=pr.deletions,
                commits=pr.commits
            )
        except GithubException as e:
            raise Exception(f"GitHub API error: {e}")
    
    def get_pr_files(self, repository: str, pr_number: int) -> List[FileChange]:
        """Get list of changed files in a GitHub pull request"""
        try:
            repo = self.github.get_repo(repository)
            pr = repo.get_pull(pr_number)
            files = []
            
            for file in pr.get_files():
                # Get file content before and after changes
                content_before = None
                content_after = None
                
                if file.status != "added":
                    try:
                        content_before = self.get_file_content(repository, file.filename, pr.base.sha)
                    except:
                        content_before = None
                
                if file.status != "removed":
                    try:
                        content_after = self.get_file_content(repository, file.filename, pr.head.sha)
                    except:
                        content_after = None
                
                files.append(FileChange(
                    filename=file.filename,
                    status=file.status,
                    additions=file.additions,
                    deletions=file.deletions,
                    patch=file.patch or "",
                    content_before=content_before,
                    content_after=content_after
                ))
            
            return files
        except GithubException as e:
            raise Exception(f"GitHub API error: {e}")
    
    def get_file_content(self, repository: str, file_path: str, ref: str) -> str:
        """Get content of a file at a specific commit"""
        try:
            repo = self.github.get_repo(repository)
            file_content = repo.get_contents(file_path, ref=ref)
            
            if isinstance(file_content, list):
                # If it's a directory, return empty string
                return ""
            
            # Decode base64 content
            return base64.b64decode(file_content.content).decode('utf-8')
        except GithubException as e:
            if e.status == 404:
                return ""  # File doesn't exist
            raise Exception(f"GitHub API error: {e}")
    
    def post_review(self, repository: str, pr_number: int, review: ReviewSummary) -> bool:
        """Post a review to the GitHub pull request"""
        try:
            repo = self.github.get_repo(repository)
            pr = repo.get_pull(pr_number)
            
            # Map recommendation to GitHub review event
            event_map = {
                "approve": "APPROVE",
                "request_changes": "REQUEST_CHANGES",
                "comment": "COMMENT"
            }
            event = event_map.get(review.recommendation, "COMMENT")
            
            # Create review comments for inline comments
            review_comments = []
            for comment in review.comments:
                if comment.line_number is not None:
                    review_comments.append({
                        "path": comment.file_path,
                        "line": comment.line_number,
                        "body": self._format_comment_body(comment)
                    })
            
            # Create the review
            pr.create_review(
                body=self._format_review_body(review),
                event=event,
                comments=review_comments
            )
            
            return True
        except GithubException as e:
            print(f"Error posting review: {e}")
            return False
    
    def post_inline_comment(self, repository: str, pr_number: int, comment: ReviewComment) -> bool:
        """Post an inline comment to a specific line"""
        try:
            repo = self.github.get_repo(repository)
            pr = repo.get_pull(pr_number)
            
            if comment.line_number is None:
                # Post as general comment
                pr.create_issue_comment(self._format_comment_body(comment))
            else:
                # Post as review comment
                pr.create_review_comment(
                    body=self._format_comment_body(comment),
                    path=comment.file_path,
                    line=comment.line_number
                )
            
            return True
        except GithubException as e:
            print(f"Error posting inline comment: {e}")
            return False
    
    def update_pr_status(self, repository: str, pr_number: int, status: str, description: str) -> bool:
        """Update PR status check"""
        try:
            repo = self.github.get_repo(repository)
            pr = repo.get_pull(pr_number)
            
            # Create a status check on the head commit
            commit = repo.get_commit(pr.head.sha)
            commit.create_status(
                state=status,  # pending, success, error, failure
                description=description,
                context="PR Review Agent"
            )
            
            return True
        except GithubException as e:
            print(f"Error updating PR status: {e}")
            return False
    
    def _test_connection(self) -> bool:
        """Test connection to GitHub"""
        try:
            user = self.github.get_user()
            return user is not None
        except:
            return False
    
    def _format_review_body(self, review: ReviewSummary) -> str:
        """Format review summary body"""
        body = f"## PR Review Summary\n\n"
        body += f"**Overall Score:** {review.overall_score:.1f}/100\n\n"
        body += f"**Recommendation:** {review.recommendation.replace('_', ' ').title()}\n\n"
        body += f"{review.summary_message}\n\n"
        
        # Add category summary
        categories = {}
        for comment in review.comments:
            if comment.category not in categories:
                categories[comment.category] = []
            categories[comment.category].append(comment)
        
        if categories:
            body += "### Issues by Category\n\n"
            for category, comments in categories.items():
                body += f"- **{category.title()}:** {len(comments)} issue(s)\n"
        
        body += "\n---\n*Generated by PR Review Agent*"
        return body
    
    def _format_comment_body(self, comment: ReviewComment) -> str:
        """Format individual comment body"""
        severity_icons = {
            "error": "🚨",
            "warning": "⚠️",
            "info": "ℹ️"
        }
        
        icon = severity_icons.get(comment.severity, "💡")
        body = f"{icon} **{comment.severity.upper()}** ({comment.category})\n\n"
        body += f"{comment.message}\n"
        
        if comment.suggestion:
            body += f"\n**Suggestion:**\n```\n{comment.suggestion}\n```"
        
        return body


# Register the GitHub adapter
AdapterFactory.register_adapter("github", GitHubAdapter)
