"""
OrgSync - Organization-Wide Repository Synchronization

Mirrors the Genesis repo to infinity-factory and syncs standards,
workflows, and configuration across all InfinityXOneSystems repositories.
Integrates with the Infinity Orchestrator GitHub App for autonomous control.
"""

import os
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any

try:
    from github import Github, Auth  # type: ignore
    _PYGITHUB_AVAILABLE = True
except ImportError:  # pragma: no cover
    _PYGITHUB_AVAILABLE = False

logger = logging.getLogger(__name__)

ORG_NAME = "InfinityXOneSystems"
MIRROR_REPO = "infinity-factory"


class SyncStatus(Enum):
    """Status of a repository sync operation."""
    PENDING = "pending"
    SYNCING = "syncing"
    SUCCESS = "success"
    SKIPPED = "skipped"
    FAILED = "failed"


@dataclass
class RepoSyncResult:
    """Result of syncing a single repository."""
    repo_name: str
    status: SyncStatus
    synced_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    message: str = ""
    files_synced: List[str] = field(default_factory=list)


@dataclass
class OrgSyncReport:
    """Aggregated report for a full organization sync run."""
    org: str
    mirror_repo: str
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None
    results: List[RepoSyncResult] = field(default_factory=list)
    total: int = 0
    succeeded: int = 0
    failed: int = 0
    skipped: int = 0

    def finish(self) -> None:
        """Mark the report as complete and compute counters."""
        self.completed_at = datetime.now(timezone.utc).isoformat()
        self.total = len(self.results)
        self.succeeded = sum(1 for r in self.results if r.status == SyncStatus.SUCCESS)
        self.failed = sum(1 for r in self.results if r.status == SyncStatus.FAILED)
        self.skipped = sum(1 for r in self.results if r.status == SyncStatus.SKIPPED)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a plain dictionary."""
        return {
            "org": self.org,
            "mirror_repo": self.mirror_repo,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "total": self.total,
            "succeeded": self.succeeded,
            "failed": self.failed,
            "skipped": self.skipped,
            "results": [
                {
                    "repo_name": r.repo_name,
                    "status": r.status.value,
                    "synced_at": r.synced_at,
                    "message": r.message,
                    "files_synced": r.files_synced,
                }
                for r in self.results
            ],
        }


# Files that Genesis pushes to every org repo to enforce enterprise standards.
SHARED_WORKFLOW_FILES = [
    ".github/workflows/genesis-loop.yml",
    ".github/workflows/devops-team.yml",
    ".github/workflows/auto-merge.yml",
]


class OrgSync:
    """
    Synchronizes Genesis artifacts across the InfinityXOneSystems organization.

    Capabilities:
    - Mirror genesis → infinity-factory (bare-push semantics via GitHub API)
    - Push standard workflows to every repo in the org
    - Report sync status back to the Infinity Orchestrator GitHub App
    """

    def __init__(self, github_token: Optional[str] = None) -> None:
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self._github: Optional[Any] = None  # PyGithub Github instance, lazy-loaded

        if not self.github_token:
            logger.warning("GITHUB_TOKEN not set — org sync will be limited")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_github(self) -> Any:
        """Return a cached PyGithub client, creating it on first call."""
        if self._github is None:
            if not _PYGITHUB_AVAILABLE:
                raise ImportError("PyGithub is not installed — install with: pip install PyGithub")
            if self.github_token:
                self._github = Github(auth=Auth.Token(self.github_token))
            else:
                self._github = Github()
        return self._github

    def _get_org(self) -> Any:
        """Return the GitHub org object for ORG_NAME."""
        gh = self._get_github()
        return gh.get_organization(ORG_NAME)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def list_org_repos(self) -> List[str]:
        """
        Return all repository names in the organization.

        Returns:
            Sorted list of repository full names (e.g. "InfinityXOneSystems/genesis").
        """
        if not self.github_token:
            logger.warning("No token — cannot list org repos")
            return []
        try:
            org = self._get_org()
            repos = [r.full_name for r in org.get_repos(type="all")]
            logger.info("Found %d repos in %s", len(repos), ORG_NAME)
            return sorted(repos)
        except Exception as exc:  # pragma: no cover
            logger.error("Failed to list org repos: %s", type(exc).__name__)
            return []

    def sync_workflow_to_repo(
        self,
        target_full_name: str,
        workflow_path: str,
        source_content: str,
        commit_message: str = "chore: sync enterprise workflow from genesis",
    ) -> RepoSyncResult:
        """
        Upsert a single workflow file into a target repository.

        Args:
            target_full_name: e.g. "InfinityXOneSystems/infinity-factory"
            workflow_path: path inside the target repo, e.g. ".github/workflows/genesis-loop.yml"
            source_content: file content (UTF-8 string)
            commit_message: commit message to use

        Returns:
            RepoSyncResult describing the outcome.
        """
        result = RepoSyncResult(repo_name=target_full_name, status=SyncStatus.PENDING)
        try:
            gh = self._get_github()
            repo = gh.get_repo(target_full_name)
            result.status = SyncStatus.SYNCING

            encoded = source_content.encode("utf-8")
            try:
                existing = repo.get_contents(workflow_path)
                # Only update when content has changed to avoid noise
                if existing.decoded_content == encoded:
                    result.status = SyncStatus.SKIPPED
                    result.message = "already up-to-date"
                    logger.info("[%s] %s — skipped (no changes)", target_full_name, workflow_path)
                    return result
                repo.update_file(
                    workflow_path,
                    commit_message,
                    source_content,
                    existing.sha,
                )
                action = "updated"
            except Exception:
                # File does not exist yet — create it
                repo.create_file(workflow_path, commit_message, source_content)
                action = "created"

            result.status = SyncStatus.SUCCESS
            result.files_synced.append(workflow_path)
            result.message = action
            logger.info("[%s] %s — %s", target_full_name, workflow_path, action)
        except Exception as exc:
            result.status = SyncStatus.FAILED
            result.message = type(exc).__name__
            logger.error("[%s] %s — failed: %s", target_full_name, workflow_path, type(exc).__name__)
        return result

    def sync_workflows_to_all_repos(
        self,
        workflow_contents: Dict[str, str],
        skip_repos: Optional[List[str]] = None,
    ) -> OrgSyncReport:
        """
        Push standard workflow files to every repository in the org.

        Args:
            workflow_contents: mapping of workflow_path → file_content
            skip_repos: full repo names to exclude from the sync

        Returns:
            OrgSyncReport with per-repo results.
        """
        skip = set(skip_repos or [])
        report = OrgSyncReport(org=ORG_NAME, mirror_repo=MIRROR_REPO)

        all_repos = self.list_org_repos()
        for full_name in all_repos:
            if full_name in skip:
                report.results.append(
                    RepoSyncResult(
                        repo_name=full_name,
                        status=SyncStatus.SKIPPED,
                        message="excluded by caller",
                    )
                )
                continue

            aggregated = RepoSyncResult(repo_name=full_name, status=SyncStatus.SUCCESS)
            for wf_path, content in workflow_contents.items():
                r = self.sync_workflow_to_repo(full_name, wf_path, content)
                if r.status == SyncStatus.FAILED:
                    aggregated.status = SyncStatus.FAILED
                    aggregated.message = r.message
                elif r.status == SyncStatus.SUCCESS:
                    aggregated.files_synced.extend(r.files_synced)
            report.results.append(aggregated)

        report.finish()
        logger.info(
            "Org sync complete — total=%d succeeded=%d failed=%d skipped=%d",
            report.total,
            report.succeeded,
            report.failed,
            report.skipped,
        )
        return report

    def get_mirror_sync_status(self) -> Dict[str, Any]:
        """
        Return a status snapshot for the genesis → infinity-factory mirror.

        Returns:
            Dictionary with mirror target info and last-checked timestamp.
        """
        mirror_full = f"{ORG_NAME}/{MIRROR_REPO}"
        status: Dict[str, Any] = {
            "source": f"{ORG_NAME}/genesis",
            "mirror": mirror_full,
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "reachable": False,
        }
        try:
            gh = self._get_github()
            repo = gh.get_repo(mirror_full)
            status["reachable"] = True
            status["default_branch"] = repo.default_branch
            status["last_push"] = repo.pushed_at.isoformat() if repo.pushed_at else None
            logger.info("Mirror %s is reachable (branch=%s)", mirror_full, repo.default_branch)
        except Exception as exc:
            status["error"] = type(exc).__name__
            logger.warning("Mirror %s not reachable: %s", mirror_full, type(exc).__name__)
        return status


# Module-level singleton
org_sync = OrgSync()
