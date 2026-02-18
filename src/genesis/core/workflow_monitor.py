"""
Workflow Monitor - Monitors GitHub Actions workflow health and detects failures

This module continuously monitors GitHub Actions workflows for failures and
provides diagnostic information for the healing agent.
"""

import logging
import os
import urllib.request
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from github import Github, GithubException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class WorkflowRun:
    """Represents a GitHub Actions workflow run."""
    id: int
    name: str
    status: str
    conclusion: Optional[str]
    created_at: str
    workflow_id: int
    html_url: str
    head_branch: str
    head_sha: str


@dataclass
class WorkflowFailure:
    """Represents a workflow failure with diagnostic information."""
    run: WorkflowRun
    failure_type: str
    error_logs: str
    suggested_fix: str
    retry_count: int = 0


class WorkflowMonitor:
    """
    Monitors GitHub Actions workflows and detects failures.
    
    This class provides capabilities to:
    - Check workflow health across all workflows
    - Identify failed workflow runs
    - Retrieve detailed failure logs
    - Categorize failure types for targeted healing
    """
    
    def __init__(self, owner: str, repo: str, github_token: Optional[str] = None):
        """
        Initialize the workflow monitor.
        
        Args:
            owner: GitHub repository owner
            repo: GitHub repository name
            github_token: GitHub token for API access (defaults to GITHUB_TOKEN env var)
        """
        self.owner = owner
        self.repo = repo
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.github = Github(self.github_token) if self.github_token else Github()
        self.repository = self.github.get_repo(f"{owner}/{repo}")
        
    def get_workflows(self) -> List[Dict[str, Any]]:
        """
        Get all workflows in the repository.
        
        Returns:
            List of workflow definitions
        """
        try:
            workflows = self.repository.get_workflows()
            return [
                {
                    "id": wf.id,
                    "name": wf.name,
                    "path": wf.path,
                    "state": wf.state
                }
                for wf in workflows
            ]
        except GithubException as e:
            logger.error(f"Failed to fetch workflows: {e}")
            return []
    
    def get_recent_workflow_runs(self, hours: int = 24) -> List[WorkflowRun]:
        """
        Get recent workflow runs within the specified time window.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            List of WorkflowRun objects
        """
        try:
            runs = []
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            # Get workflow runs
            workflow_runs = self.repository.get_workflow_runs()
            
            for run in workflow_runs[:50]:  # Limit to 50 most recent
                if run.created_at.replace(tzinfo=None) >= cutoff_time:
                    runs.append(WorkflowRun(
                        id=run.id,
                        name=run.name,
                        status=run.status,
                        conclusion=run.conclusion,
                        created_at=run.created_at.isoformat(),
                        workflow_id=run.workflow_id,
                        html_url=run.html_url,
                        head_branch=run.head_branch,
                        head_sha=run.head_sha
                    ))
            
            return runs
        except GithubException as e:
            logger.error(f"Failed to fetch workflow runs: {e}")
            return []
    
    def get_failed_runs(self, hours: int = 24) -> List[WorkflowRun]:
        """
        Get all failed workflow runs within the specified time window.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            List of failed WorkflowRun objects
        """
        runs = self.get_recent_workflow_runs(hours)
        failed_runs = [
            run for run in runs
            if run.status == "completed" and run.conclusion in ["failure", "action_required", "cancelled", "timed_out"]
        ]
        
        logger.info(f"Found {len(failed_runs)} failed workflow runs in the last {hours} hours")
        return failed_runs
    
    def get_workflow_run_jobs(self, run_id: int) -> List[Dict[str, Any]]:
        """
        Get all jobs for a specific workflow run.
        
        Args:
            run_id: Workflow run ID
            
        Returns:
            List of job objects
        """
        try:
            run = self.repository.get_workflow_run(run_id)
            jobs = run.jobs()
            return [
                {
                    "id": job.id,
                    "name": job.name,
                    "status": job.status,
                    "conclusion": job.conclusion,
                    "started_at": job.started_at.isoformat() if job.started_at else None,
                    "completed_at": job.completed_at.isoformat() if job.completed_at else None
                }
                for job in jobs
            ]
        except GithubException as e:
            logger.error(f"Failed to fetch jobs for run {run_id}: {e}")
            return []
    
    def get_job_logs(self, job_id: int) -> str:
        """
        Get logs for a specific job.
        
        Args:
            job_id: Job ID
            
        Returns:
            Job logs as string
        """
        try:
            url = f"https://api.github.com/repos/{self.owner}/{self.repo}/actions/jobs/{job_id}/logs"
            headers = {
                "Authorization": f"Bearer {self.github_token}",
                "Accept": "application/vnd.github+json"
            }
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as response:
                return response.read().decode('utf-8')
        except urllib.error.HTTPError as e:
            logger.error(f"HTTP error fetching logs for job {job_id}: {e.code} {e.reason}")
            return ""
        except urllib.error.URLError as e:
            logger.error(f"Network error fetching logs for job {job_id}: {e.reason}")
            return ""
        except Exception as e:
            logger.error(f"Unexpected error fetching logs for job {job_id}: {e}")
            return ""
    
    def analyze_failure(self, run: WorkflowRun) -> WorkflowFailure:
        """
        Analyze a failed workflow run to determine the failure type and suggest fixes.
        
        Args:
            run: Failed WorkflowRun object
            
        Returns:
            WorkflowFailure object with diagnostic information
        """
        jobs = self.get_workflow_run_jobs(run.id)
        failed_jobs = [job for job in jobs if job.get("conclusion") in ["failure", "action_required"]]
        
        # Collect error logs from failed jobs
        error_logs = []
        for job in failed_jobs[:3]:  # Limit to first 3 failed jobs
            logs = self.get_job_logs(job["id"])
            if logs:
                # Extract last 50 lines for context
                log_lines = logs.split("\n")
                error_logs.append(f"Job: {job['name']}\n" + "\n".join(log_lines[-50:]))
        
        combined_logs = "\n\n".join(error_logs)
        
        # Categorize failure type based on logs and workflow name
        failure_type = self._categorize_failure(run, combined_logs)
        suggested_fix = self._suggest_fix(failure_type, combined_logs)
        
        return WorkflowFailure(
            run=run,
            failure_type=failure_type,
            error_logs=combined_logs,
            suggested_fix=suggested_fix
        )
    
    def _categorize_failure(self, run: WorkflowRun, logs: str) -> str:
        """
        Categorize the type of failure based on workflow name and logs.
        
        Args:
            run: WorkflowRun object
            logs: Error logs
            
        Returns:
            Failure type string
        """
        logs_lower = logs.lower()
        
        # Test failures
        if "test" in run.name.lower() or "failed" in logs_lower or "error" in logs_lower:
            if "pytest" in logs_lower or "test_" in logs_lower:
                return "test_failure"
            
        # Linting/formatting issues
        if "lint" in run.name.lower() or "format" in logs_lower or "flake8" in logs_lower or "black" in logs_lower:
            return "lint_failure"
        
        # Build failures
        if "build" in run.name.lower() or "compilation" in logs_lower or "npm run build" in logs_lower:
            return "build_failure"
        
        # Dependency issues
        if "pip install" in logs_lower or "npm install" in logs_lower or "requirements" in logs_lower:
            return "dependency_failure"
        
        # Security issues
        if "security" in run.name.lower() or "vulnerability" in logs_lower or "cve" in logs_lower:
            return "security_failure"
        
        # Type checking
        if "mypy" in logs_lower or "type" in logs_lower:
            return "type_failure"
        
        return "unknown_failure"
    
    def _suggest_fix(self, failure_type: str, logs: str) -> str:
        """
        Suggest a fix based on the failure type.
        
        Args:
            failure_type: Type of failure
            logs: Error logs
            
        Returns:
            Suggested fix as string
        """
        suggestions = {
            "test_failure": "Analyze test failures and fix failing tests. Consider updating test fixtures or fixing regression bugs.",
            "lint_failure": "Run auto-formatters (black, isort) to fix linting issues. Update code to pass linting rules.",
            "build_failure": "Check build configuration and fix compilation errors. Verify dependencies are correctly specified.",
            "dependency_failure": "Update requirements.txt or package.json. Resolve dependency conflicts. Clear cache and reinstall.",
            "security_failure": "Update vulnerable dependencies to patched versions. Review and fix security vulnerabilities.",
            "type_failure": "Fix type annotations. Run mypy and address type errors.",
            "unknown_failure": "Review logs carefully to identify root cause. May require manual investigation."
        }
        
        return suggestions.get(failure_type, suggestions["unknown_failure"])
    
    def get_workflow_health_status(self) -> Dict[str, Any]:
        """
        Get overall workflow health status.
        
        Returns:
            Dictionary with health metrics
        """
        workflows = self.get_workflows()
        recent_runs = self.get_recent_workflow_runs(hours=24)
        failed_runs = self.get_failed_runs(hours=24)
        
        total_runs = len(recent_runs)
        failed_count = len(failed_runs)
        success_rate = ((total_runs - failed_count) / total_runs * 100) if total_runs > 0 else 100.0
        
        return {
            "total_workflows": len(workflows),
            "total_runs_24h": total_runs,
            "failed_runs_24h": failed_count,
            "success_rate": success_rate,
            "health_status": "healthy" if success_rate >= 80 else "degraded" if success_rate >= 50 else "critical",
            "timestamp": datetime.utcnow().isoformat()
        }


# Global instance for easy access
workflow_monitor = None


def get_workflow_monitor(owner: str = "InfinityXOneSystems", repo: str = "genesis") -> WorkflowMonitor:
    """
    Get or create the global workflow monitor instance.
    
    Args:
        owner: GitHub repository owner
        repo: GitHub repository name
        
    Returns:
        WorkflowMonitor instance
    """
    global workflow_monitor
    if workflow_monitor is None:
        workflow_monitor = WorkflowMonitor(owner, repo)
    return workflow_monitor
