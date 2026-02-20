"""
Tests for Genesis OrgSync module
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import timezone

from genesis.core.org_sync import (
    OrgSync,
    OrgSyncReport,
    RepoSyncResult,
    SyncStatus,
    ORG_NAME,
    MIRROR_REPO,
    SHARED_WORKFLOW_FILES,
    org_sync,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def syncer():
    """Return an OrgSync instance with a fake token."""
    return OrgSync(github_token="fake-token-for-tests")


@pytest.fixture()
def mock_github(syncer):
    """
    Patch the Github class inside org_sync and return the mock org/repo
    objects for convenient test configuration.
    """
    mock_repo = MagicMock()
    mock_repo.full_name = "InfinityXOneSystems/test-repo"
    mock_repo.default_branch = "main"
    pushed = MagicMock()
    pushed.isoformat.return_value = "2024-01-01T00:00:00+00:00"
    mock_repo.pushed_at = pushed

    mock_org = MagicMock()
    mock_org.get_repos.return_value = [mock_repo]

    mock_auth = MagicMock()
    mock_gh_instance = MagicMock()
    mock_gh_instance.get_organization.return_value = mock_org
    mock_gh_instance.get_repo.return_value = mock_repo

    with patch("genesis.core.org_sync.Github", return_value=mock_gh_instance), \
         patch("genesis.core.org_sync.Auth", mock_auth):
        # Reset the cached client so our patch is picked up
        syncer._github = None
        yield {
            "gh": mock_gh_instance,
            "org": mock_org,
            "repo": mock_repo,
        }


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------

class TestOrgSyncInit:
    def test_token_set(self):
        s = OrgSync(github_token="abc123")
        assert s.github_token == "abc123"

    def test_token_from_env(self, monkeypatch):
        monkeypatch.setenv("GITHUB_TOKEN", "env-token")
        s = OrgSync()
        assert s.github_token == "env-token"

    def test_no_token_warns(self, monkeypatch, caplog):
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        import logging
        with caplog.at_level(logging.WARNING, logger="genesis.core.org_sync"):
            OrgSync()
        assert "GITHUB_TOKEN not set" in caplog.text

    def test_module_singleton_exists(self):
        assert org_sync is not None
        assert isinstance(org_sync, OrgSync)


# ---------------------------------------------------------------------------
# list_org_repos
# ---------------------------------------------------------------------------

class TestListOrgRepos:
    def test_returns_sorted_full_names(self, syncer, mock_github):
        repos = syncer.list_org_repos()
        assert repos == ["InfinityXOneSystems/test-repo"]

    def test_empty_on_no_token(self, caplog):
        import logging
        s = OrgSync(github_token="")
        # Force token to falsy without env var
        s.github_token = None
        with caplog.at_level(logging.WARNING, logger="genesis.core.org_sync"):
            repos = s.list_org_repos()
        assert repos == []

    def test_empty_on_api_error(self, syncer, mock_github):
        mock_github["gh"].get_organization.side_effect = Exception("API down")
        syncer._github = None
        repos = syncer.list_org_repos()
        assert repos == []


# ---------------------------------------------------------------------------
# sync_workflow_to_repo
# ---------------------------------------------------------------------------

class TestSyncWorkflowToRepo:
    TARGET = "InfinityXOneSystems/test-repo"
    WF_PATH = ".github/workflows/genesis-loop.yml"
    CONTENT = "name: Genesis\non: push\n"

    def test_creates_new_file(self, syncer, mock_github):
        repo = mock_github["repo"]
        # Simulate file not existing
        repo.get_contents.side_effect = Exception("Not Found")

        result = syncer.sync_workflow_to_repo(self.TARGET, self.WF_PATH, self.CONTENT)

        assert result.status == SyncStatus.SUCCESS
        assert self.WF_PATH in result.files_synced
        repo.create_file.assert_called_once()

    def test_updates_changed_file(self, syncer, mock_github):
        repo = mock_github["repo"]
        existing = MagicMock()
        existing.decoded_content = b"old content"
        existing.sha = "abc123"
        repo.get_contents.return_value = existing

        result = syncer.sync_workflow_to_repo(self.TARGET, self.WF_PATH, self.CONTENT)

        assert result.status == SyncStatus.SUCCESS
        repo.update_file.assert_called_once()

    def test_skips_unchanged_file(self, syncer, mock_github):
        repo = mock_github["repo"]
        existing = MagicMock()
        existing.decoded_content = self.CONTENT.encode("utf-8")
        existing.sha = "abc123"
        repo.get_contents.return_value = existing

        result = syncer.sync_workflow_to_repo(self.TARGET, self.WF_PATH, self.CONTENT)

        assert result.status == SyncStatus.SKIPPED
        repo.update_file.assert_not_called()
        repo.create_file.assert_not_called()

    def test_returns_failed_on_api_error(self, syncer, mock_github):
        mock_github["gh"].get_repo.side_effect = Exception("Forbidden")
        syncer._github = None

        result = syncer.sync_workflow_to_repo(self.TARGET, self.WF_PATH, self.CONTENT)

        assert result.status == SyncStatus.FAILED
        assert result.message  # error type name is recorded


# ---------------------------------------------------------------------------
# sync_workflows_to_all_repos
# ---------------------------------------------------------------------------

class TestSyncWorkflowsToAllRepos:
    WF = {".github/workflows/genesis-loop.yml": "name: Genesis\n"}

    def test_propagates_to_all_repos(self, syncer, mock_github):
        repo = mock_github["repo"]
        repo.get_contents.side_effect = Exception("Not Found")

        report = syncer.sync_workflows_to_all_repos(self.WF)

        assert report.total == 1
        assert report.succeeded == 1
        assert report.failed == 0

    def test_skips_excluded_repos(self, syncer, mock_github):
        report = syncer.sync_workflows_to_all_repos(
            self.WF, skip_repos=["InfinityXOneSystems/test-repo"]
        )
        assert report.skipped == 1
        assert report.succeeded == 0

    def test_report_finished(self, syncer, mock_github):
        mock_github["repo"].get_contents.side_effect = Exception("Not Found")
        report = syncer.sync_workflows_to_all_repos(self.WF)
        assert report.completed_at is not None
        assert report.total == len(report.results)


# ---------------------------------------------------------------------------
# get_mirror_sync_status
# ---------------------------------------------------------------------------

class TestGetMirrorSyncStatus:
    def test_reachable_mirror(self, syncer, mock_github):
        status = syncer.get_mirror_sync_status()
        assert status["reachable"] is True
        assert status["source"] == f"{ORG_NAME}/genesis"
        assert status["mirror"] == f"{ORG_NAME}/{MIRROR_REPO}"

    def test_unreachable_mirror(self, syncer, mock_github):
        mock_github["gh"].get_repo.side_effect = Exception("Not Found")
        syncer._github = None

        status = syncer.get_mirror_sync_status()
        assert status["reachable"] is False
        assert "error" in status


# ---------------------------------------------------------------------------
# OrgSyncReport dataclass
# ---------------------------------------------------------------------------

class TestOrgSyncReport:
    def test_finish_computes_counts(self):
        r = OrgSyncReport(org=ORG_NAME, mirror_repo=MIRROR_REPO)
        r.results = [
            RepoSyncResult("a/repo1", SyncStatus.SUCCESS),
            RepoSyncResult("a/repo2", SyncStatus.FAILED),
            RepoSyncResult("a/repo3", SyncStatus.SKIPPED),
        ]
        r.finish()
        assert r.total == 3
        assert r.succeeded == 1
        assert r.failed == 1
        assert r.skipped == 1
        assert r.completed_at is not None

    def test_to_dict_serializes(self):
        r = OrgSyncReport(org=ORG_NAME, mirror_repo=MIRROR_REPO)
        r.results = [RepoSyncResult("a/repo", SyncStatus.SUCCESS)]
        r.finish()
        d = r.to_dict()
        assert d["org"] == ORG_NAME
        assert len(d["results"]) == 1
        assert d["results"][0]["status"] == "success"


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

class TestConstants:
    def test_org_name(self):
        assert ORG_NAME == "InfinityXOneSystems"

    def test_mirror_repo(self):
        assert MIRROR_REPO == "infinity-factory"

    def test_shared_workflow_files_not_empty(self):
        assert len(SHARED_WORKFLOW_FILES) > 0
        for f in SHARED_WORKFLOW_FILES:
            assert f.startswith(".github/workflows/")
