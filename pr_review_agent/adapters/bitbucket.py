"""
Bitbucket adapter for PR Review Agent
"""
import requests
from typing import List, Optional
from datetime import datetime
import base64

from .base import (
    GitServerAdapter, AdapterFactory, PRInfo, FileChange, 
    ReviewComment, ReviewSummary
)


class BitbucketAdapter(GitServerAdapter):
    """Bitbucket adapter implementation"""
    
    def __init__(self, base_url: str, token: str, timeout: int = 30):
        super().__init__(base_url, token, timeout)
        self.api_url = f"{base_url}/2.0"
    
    def get_pr_info(self, repository: str, pr_number: int) -> PRInfo:
        """Get pull request information from Bitbucket"""
        url = f"{self.api_url}/repositories/{repository}/pullrequests/{pr_number}"
        
        response = requests.get(url, headers=self._get_headers(), timeout=self.timeout)
        self._handle_api_error(response)
        
        pr_data = response.json()
        
        return PRInfo(
            id=str(pr_data['id']),
            number=pr_data['id'],
            title=pr_data['title'],
            description=pr_data['description'] or "",
            author=pr_data['author']['username'],
            source_branch=pr_data['source']['branch']['name'],
            target_branch=pr_data['destination']['branch']['name'],
            status=pr_data['state'],
            created_at=datetime.fromisoformat(pr_data['created_on'].replace('Z', '+00:00')),
            updated_at=datetime.fromisoformat(pr_data['updated_on'].replace('Z', '+00:00')),
            url=pr_data['links']['html']['href'],
            repository=repository,
            files_changed=self._get_changed_files_list(repository, pr_number),
            additions=0,  # Would need to calculate from diff
            deletions=0,  # Would need to calculate from diff
            commits=len(self._get_pr_commits(repository, pr_number))
        )
    
    def get_pr_files(self, repository: str, pr_number: int) -> List[FileChange]:
        """Get list of changed files in a Bitbucket pull request"""
        url = f"{self.api_url}/repositories/{repository}/pullrequests/{pr_number}/diffstat"
        
        response = requests.get(url, headers=self._get_headers(), timeout=self.timeout)
        self._handle_api_error(response)
        
        diffstat_data = response.json()
        files = []
        
        for file_stat in diffstat_data.get('values', []):
            # Get the actual diff for this file
            diff_content = self._get_file_diff(repository, pr_number, file_stat['new']['name'])
            
            # Get file content before and after changes
            content_before = None
            content_after = None
            
            if file_stat['status'] != 'added':
                try:
                    content_before = self.get_file_content(
                        repository, 
                        file_stat['old']['name'], 
                        self._get_pr_base_commit(repository, pr_number)
                    )
                except:
                    content_before = None
            
            if file_stat['status'] != 'removed':
                try:
                    content_after = self.get_file_content(
                        repository, 
                        file_stat['new']['name'], 
                        self._get_pr_head_commit(repository, pr_number)
                    )
                except:
                    content_after = None
            
            files.append(FileChange(
                filename=file_stat['new']['name'],
                status=file_stat['status'],
                additions=file_stat.get('lines_added', 0),
                deletions=file_stat.get('lines_removed', 0),
                patch=diff_content,
                content_before=content_before,
                content_after=content_after
            ))
        
        return files
    
    def get_file_content(self, repository: str, file_path: str, ref: str) -> str:
        """Get content of a file at a specific commit"""
        url = f"{self.api_url}/repositories/{repository}/src/{ref}/{file_path}"
        
        response = requests.get(url, headers=self._get_headers(), timeout=self.timeout)
        
        if response.status_code == 404:
            return ""  # File doesn't exist
        
        self._handle_api_error(response)
        return response.text
    
    def post_review(self, repository: str, pr_number: int, review: ReviewSummary) -> bool:
        """Post a review to the Bitbucket pull request"""
        # Post main review comment
        if not self._post_pr_comment(repository, pr_number, self._format_review_body(review)):
            return False
        
        # Post inline comments
        for comment in review.comments:
            if comment.line_number is not None:
                self.post_inline_comment(repository, pr_number, comment)
        
        # Update approval status if needed
        if review.recommendation == "approve":
            self._approve_pr(repository, pr_number)
        elif review.recommendation == "request_changes":
            self._request_changes_pr(repository, pr_number)
        
        return True
    
    def post_inline_comment(self, repository: str, pr_number: int, comment: ReviewComment) -> bool:
        """Post an inline comment to a specific line"""
        if comment.line_number is None:
            # Post as general comment
            return self._post_pr_comment(repository, pr_number, self._format_comment_body(comment))
        else:
            # Post as inline comment
            url = f"{self.api_url}/repositories/{repository}/pullrequests/{pr_number}/comments"
            
            data = {
                'content': {
                    'raw': self._format_comment_body(comment)
                },
                'inline': {
                    'path': comment.file_path,
                    'to': comment.line_number
                }
            }
            
            response = requests.post(url, headers=self._get_headers(), json=data, timeout=self.timeout)
            return response.status_code == 201
    
    def update_pr_status(self, repository: str, pr_number: int, status: str, description: str) -> bool:
        """Update PR status check"""
        # Get the head commit SHA
        head_commit = self._get_pr_head_commit(repository, pr_number)
        if not head_commit:
            return False
        
        # Create commit status
        url = f"{self.api_url}/repositories/{repository}/commit/{head_commit}/statuses/build"
        
        # Map status to Bitbucket format
        state_map = {
            "pending": "INPROGRESS",
            "success": "SUCCESSFUL",
            "error": "FAILED",
            "failure": "FAILED"
        }
        
        data = {
            'state': state_map.get(status, "INPROGRESS"),
            'description': description,
            'key': 'pr-review-agent',
            'name': 'PR Review Agent'
        }
        
        response = requests.post(url, headers=self._get_headers(), json=data, timeout=self.timeout)
        return response.status_code == 201
    
    def _test_connection(self) -> bool:
        """Test connection to Bitbucket"""
        url = f"{self.api_url}/user"
        response = requests.get(url, headers=self._get_headers(), timeout=self.timeout)
        return response.status_code == 200
    
    def _get_changed_files_list(self, repository: str, pr_number: int) -> List[str]:
        """Get list of changed files"""
        url = f"{self.api_url}/repositories/{repository}/pullrequests/{pr_number}/diffstat"
        response = requests.get(url, headers=self._get_headers(), timeout=self.timeout)
        
        if response.status_code != 200:
            return []
        
        diffstat_data = response.json()
        return [file_stat['new']['name'] for file_stat in diffstat_data.get('values', [])]
    
    def _get_pr_commits(self, repository: str, pr_number: int) -> List[dict]:
        """Get pull request commits"""
        url = f"{self.api_url}/repositories/{repository}/pullrequests/{pr_number}/commits"
        response = requests.get(url, headers=self._get_headers(), timeout=self.timeout)
        
        if response.status_code != 200:
            return []
        
        return response.json().get('values', [])
    
    def _get_file_diff(self, repository: str, pr_number: int, file_path: str) -> str:
        """Get diff for a specific file"""
        url = f"{self.api_url}/repositories/{repository}/pullrequests/{pr_number}/diff"
        params = {'path': file_path}
        
        response = requests.get(url, headers=self._get_headers(), params=params, timeout=self.timeout)
        
        if response.status_code != 200:
            return ""
        
        return response.text
    
    def _get_pr_base_commit(self, repository: str, pr_number: int) -> str:
        """Get base commit SHA for PR"""
        url = f"{self.api_url}/repositories/{repository}/pullrequests/{pr_number}"
        response = requests.get(url, headers=self._get_headers(), timeout=self.timeout)
        
        if response.status_code != 200:
            return ""
        
        pr_data = response.json()
        return pr_data['destination']['commit']['hash']
    
    def _get_pr_head_commit(self, repository: str, pr_number: int) -> str:
        """Get head commit SHA for PR"""
        url = f"{self.api_url}/repositories/{repository}/pullrequests/{pr_number}"
        response = requests.get(url, headers=self._get_headers(), timeout=self.timeout)
        
        if response.status_code != 200:
            return ""
        
        pr_data = response.json()
        return pr_data['source']['commit']['hash']
    
    def _post_pr_comment(self, repository: str, pr_number: int, content: str) -> bool:
        """Post a general comment to PR"""
        url = f"{self.api_url}/repositories/{repository}/pullrequests/{pr_number}/comments"
        
        data = {
            'content': {
                'raw': content
            }
        }
        
        response = requests.post(url, headers=self._get_headers(), json=data, timeout=self.timeout)
        return response.status_code == 201
    
    def _approve_pr(self, repository: str, pr_number: int) -> bool:
        """Approve pull request"""
        url = f"{self.api_url}/repositories/{repository}/pullrequests/{pr_number}/approve"
        response = requests.post(url, headers=self._get_headers(), timeout=self.timeout)
        return response.status_code == 200
    
    def _request_changes_pr(self, repository: str, pr_number: int) -> bool:
        """Request changes for pull request"""
        url = f"{self.api_url}/repositories/{repository}/pullrequests/{pr_number}/request-changes"
        response = requests.post(url, headers=self._get_headers(), timeout=self.timeout)
        return response.status_code == 200
    
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
    
    def _get_headers(self) -> dict:
        """Get headers for Bitbucket API"""
        return {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }


# Register the Bitbucket adapter
AdapterFactory.register_adapter("bitbucket", BitbucketAdapter)
