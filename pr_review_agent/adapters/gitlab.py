"""
GitLab adapter for PR Review Agent
"""
import requests
from typing import List, Optional
from datetime import datetime
import base64

from .base import (
    GitServerAdapter, AdapterFactory, PRInfo, FileChange, 
    ReviewComment, ReviewSummary
)


class GitLabAdapter(GitServerAdapter):
    """GitLab adapter implementation"""
    
    def __init__(self, base_url: str, token: str, timeout: int = 30):
        super().__init__(base_url, token, timeout)
        self.api_url = f"{base_url}/v4"
    
    def get_pr_info(self, repository: str, pr_number: int) -> PRInfo:
        """Get merge request information from GitLab"""
        project_id = self._get_project_id(repository)
        url = f"{self.api_url}/projects/{project_id}/merge_requests/{pr_number}"
        
        response = requests.get(url, headers=self._get_headers(), timeout=self.timeout)
        self._handle_api_error(response)
        
        mr_data = response.json()
        
        return PRInfo(
            id=str(mr_data['id']),
            number=mr_data['iid'],
            title=mr_data['title'],
            description=mr_data['description'] or "",
            author=mr_data['author']['username'],
            source_branch=mr_data['source_branch'],
            target_branch=mr_data['target_branch'],
            status=mr_data['state'],
            created_at=datetime.fromisoformat(mr_data['created_at'].replace('Z', '+00:00')),
            updated_at=datetime.fromisoformat(mr_data['updated_at'].replace('Z', '+00:00')),
            url=mr_data['web_url'],
            repository=repository,
            files_changed=self._get_changed_files_list(project_id, mr_data['iid']),
            additions=0,  # GitLab doesn't provide this directly
            deletions=0,  # GitLab doesn't provide this directly
            commits=len(self._get_mr_commits(project_id, mr_data['iid']))
        )
    
    def get_pr_files(self, repository: str, pr_number: int) -> List[FileChange]:
        """Get list of changed files in a GitLab merge request"""
        project_id = self._get_project_id(repository)
        url = f"{self.api_url}/projects/{project_id}/merge_requests/{pr_number}/changes"
        
        response = requests.get(url, headers=self._get_headers(), timeout=self.timeout)
        self._handle_api_error(response)
        
        changes_data = response.json()
        files = []
        
        for change in changes_data.get('changes', []):
            # Get file content before and after changes
            content_before = None
            content_after = None
            
            if not change['new_file']:
                content_before = self._get_file_from_diff(change, 'old')
            
            if not change['deleted_file']:
                content_after = self._get_file_from_diff(change, 'new')
            
            # Determine status
            status = "modified"
            if change['new_file']:
                status = "added"
            elif change['deleted_file']:
                status = "removed"
            elif change['renamed_file']:
                status = "renamed"
            
            files.append(FileChange(
                filename=change['new_path'],
                status=status,
                additions=0,  # Would need to parse diff
                deletions=0,  # Would need to parse diff
                patch=change.get('diff', ''),
                content_before=content_before,
                content_after=content_after
            ))
        
        return files
    
    def get_file_content(self, repository: str, file_path: str, ref: str) -> str:
        """Get content of a file at a specific commit"""
        project_id = self._get_project_id(repository)
        # URL encode the file path
        encoded_path = requests.utils.quote(file_path, safe='')
        url = f"{self.api_url}/projects/{project_id}/repository/files/{encoded_path}/raw"
        
        params = {'ref': ref}
        response = requests.get(url, headers=self._get_headers(), params=params, timeout=self.timeout)
        
        if response.status_code == 404:
            return ""  # File doesn't exist
        
        self._handle_api_error(response)
        return response.text
    
    def post_review(self, repository: str, pr_number: int, review: ReviewSummary) -> bool:
        """Post a review to the GitLab merge request"""
        project_id = self._get_project_id(repository)
        
        # Post main review note
        note_body = self._format_review_body(review)
        if not self._post_mr_note(project_id, pr_number, note_body):
            return False
        
        # Post inline comments
        for comment in review.comments:
            if comment.line_number is not None:
                self.post_inline_comment(repository, pr_number, comment)
        
        # Update MR approval status if needed
        if review.recommendation == "approve":
            self._approve_mr(project_id, pr_number)
        elif review.recommendation == "request_changes":
            self._unapprove_mr(project_id, pr_number)
        
        return True
    
    def post_inline_comment(self, repository: str, pr_number: int, comment: ReviewComment) -> bool:
        """Post an inline comment to a specific line"""
        project_id = self._get_project_id(repository)
        
        if comment.line_number is None:
            # Post as general note
            return self._post_mr_note(project_id, pr_number, self._format_comment_body(comment))
        else:
            # Post as discussion note on specific line
            url = f"{self.api_url}/projects/{project_id}/merge_requests/{pr_number}/discussions"
            
            data = {
                'body': self._format_comment_body(comment),
                'position': {
                    'position_type': 'text',
                    'new_path': comment.file_path,
                    'new_line': comment.line_number
                }
            }
            
            response = requests.post(url, headers=self._get_headers(), json=data, timeout=self.timeout)
            return response.status_code == 201
    
    def update_pr_status(self, repository: str, pr_number: int, status: str, description: str) -> bool:
        """Update MR status check"""
        project_id = self._get_project_id(repository)
        
        # Get the source branch SHA
        mr_url = f"{self.api_url}/projects/{project_id}/merge_requests/{pr_number}"
        response = requests.get(mr_url, headers=self._get_headers(), timeout=self.timeout)
        
        if response.status_code != 200:
            return False
        
        mr_data = response.json()
        sha = mr_data['sha']
        
        # Create commit status
        url = f"{self.api_url}/projects/{project_id}/statuses/{sha}"
        data = {
            'state': status,
            'description': description,
            'context': 'PR Review Agent'
        }
        
        response = requests.post(url, headers=self._get_headers(), json=data, timeout=self.timeout)
        return response.status_code == 201
    
    def _test_connection(self) -> bool:
        """Test connection to GitLab"""
        url = f"{self.api_url}/user"
        response = requests.get(url, headers=self._get_headers(), timeout=self.timeout)
        return response.status_code == 200
    
    def _get_project_id(self, repository: str) -> str:
        """Get GitLab project ID from repository name"""
        # URL encode the repository path
        return requests.utils.quote(repository, safe='')
    
    def _get_changed_files_list(self, project_id: str, mr_iid: int) -> List[str]:
        """Get list of changed files"""
        url = f"{self.api_url}/projects/{project_id}/merge_requests/{mr_iid}/changes"
        response = requests.get(url, headers=self._get_headers(), timeout=self.timeout)
        
        if response.status_code != 200:
            return []
        
        changes_data = response.json()
        return [change['new_path'] for change in changes_data.get('changes', [])]
    
    def _get_mr_commits(self, project_id: str, mr_iid: int) -> List[dict]:
        """Get merge request commits"""
        url = f"{self.api_url}/projects/{project_id}/merge_requests/{mr_iid}/commits"
        response = requests.get(url, headers=self._get_headers(), timeout=self.timeout)
        
        if response.status_code != 200:
            return []
        
        return response.json()
    
    def _get_file_from_diff(self, change: dict, version: str) -> Optional[str]:
        """Extract file content from diff"""
        # This is a simplified version - in practice, you'd need to parse the diff properly
        diff = change.get('diff', '')
        if not diff:
            return None
        
        lines = diff.split('\n')
        content_lines = []
        
        for line in lines:
            if version == 'old' and line.startswith('-') and not line.startswith('---'):
                content_lines.append(line[1:])
            elif version == 'new' and line.startswith('+') and not line.startswith('+++'):
                content_lines.append(line[1:])
            elif not line.startswith(('+', '-', '@@')):
                content_lines.append(line)
        
        return '\n'.join(content_lines) if content_lines else None
    
    def _post_mr_note(self, project_id: str, mr_iid: int, body: str) -> bool:
        """Post a note to merge request"""
        url = f"{self.api_url}/projects/{project_id}/merge_requests/{mr_iid}/notes"
        data = {'body': body}
        
        response = requests.post(url, headers=self._get_headers(), json=data, timeout=self.timeout)
        return response.status_code == 201
    
    def _approve_mr(self, project_id: str, mr_iid: int) -> bool:
        """Approve merge request"""
        url = f"{self.api_url}/projects/{project_id}/merge_requests/{mr_iid}/approve"
        response = requests.post(url, headers=self._get_headers(), timeout=self.timeout)
        return response.status_code == 201
    
    def _unapprove_mr(self, project_id: str, mr_iid: int) -> bool:
        """Unapprove merge request"""
        url = f"{self.api_url}/projects/{project_id}/merge_requests/{mr_iid}/unapprove"
        response = requests.post(url, headers=self._get_headers(), timeout=self.timeout)
        return response.status_code == 201
    
    def _format_review_body(self, review: ReviewSummary) -> str:
        """Format review summary body"""
        body = f"## MR Review Summary\n\n"
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
        """Get headers for GitLab API"""
        return {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }


# Register the GitLab adapter
AdapterFactory.register_adapter("gitlab", GitLabAdapter)
