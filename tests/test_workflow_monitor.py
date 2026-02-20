"""
Tests for Workflow Monitor
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from src.genesis.core.workflow_monitor import (
    WorkflowMonitor,
    WorkflowRun,
    WorkflowFailure,
    get_workflow_monitor
)


@pytest.fixture
def mock_github():
    """Create mock GitHub instance."""
    with patch('src.genesis.core.workflow_monitor.Github') as mock:
        yield mock


@pytest.fixture
def workflow_monitor(mock_github):
    """Create WorkflowMonitor instance with mocked GitHub."""
    mock_github.return_value.get_repo.return_value = Mock()
    return WorkflowMonitor("test-owner", "test-repo", "fake-token")


def test_workflow_monitor_initialization(workflow_monitor):
    """Test workflow monitor initialization."""
    assert workflow_monitor.owner == "test-owner"
    assert workflow_monitor.repo == "test-repo"
    assert workflow_monitor.github_token == "fake-token"


def test_get_workflows(workflow_monitor):
    """Test getting workflows."""
    mock_workflow = Mock()
    mock_workflow.id = 12345
    mock_workflow.name = "CI"
    mock_workflow.path = ".github/workflows/ci.yml"
    mock_workflow.state = "active"
    
    workflow_monitor.repository.get_workflows.return_value = [mock_workflow]
    
    workflows = workflow_monitor.get_workflows()
    
    assert len(workflows) == 1
    assert workflows[0]["id"] == 12345
    assert workflows[0]["name"] == "CI"
    assert workflows[0]["path"] == ".github/workflows/ci.yml"


def test_get_recent_workflow_runs(workflow_monitor):
    """Test getting recent workflow runs."""
    mock_run = Mock()
    mock_run.id = 67890
    mock_run.name = "CI"
    mock_run.status = "completed"
    mock_run.conclusion = "success"
    mock_run.created_at = datetime.utcnow()
    mock_run.workflow_id = 12345
    mock_run.html_url = "https://github.com/test/test/actions/runs/67890"
    mock_run.head_branch = "main"
    mock_run.head_sha = "abc123"
    
    workflow_monitor.repository.get_workflow_runs.return_value = [mock_run]
    
    runs = workflow_monitor.get_recent_workflow_runs(hours=24)
    
    assert len(runs) == 1
    assert runs[0].id == 67890
    assert runs[0].name == "CI"
    assert runs[0].status == "completed"
    assert runs[0].conclusion == "success"


def test_get_failed_runs(workflow_monitor):
    """Test getting failed workflow runs."""
    # Create mock runs with different conclusions
    success_run = Mock()
    success_run.id = 1
    success_run.name = "CI"
    success_run.status = "completed"
    success_run.conclusion = "success"
    success_run.created_at = datetime.utcnow()
    success_run.workflow_id = 12345
    success_run.html_url = "https://github.com/test/test/actions/runs/1"
    success_run.head_branch = "main"
    success_run.head_sha = "abc123"
    
    failed_run = Mock()
    failed_run.id = 2
    failed_run.name = "CI"
    failed_run.status = "completed"
    failed_run.conclusion = "failure"
    failed_run.created_at = datetime.utcnow()
    failed_run.workflow_id = 12345
    failed_run.html_url = "https://github.com/test/test/actions/runs/2"
    failed_run.head_branch = "main"
    failed_run.head_sha = "def456"
    
    workflow_monitor.repository.get_workflow_runs.return_value = [success_run, failed_run]
    
    failed_runs = workflow_monitor.get_failed_runs(hours=24)
    
    assert len(failed_runs) == 1
    assert failed_runs[0].id == 2
    assert failed_runs[0].conclusion == "failure"


def test_categorize_failure_test(workflow_monitor):
    """Test categorizing test failures."""
    run = WorkflowRun(
        id=1,
        name="Tests",
        status="completed",
        conclusion="failure",
        created_at=datetime.utcnow().isoformat(),
        workflow_id=12345,
        html_url="https://github.com/test/test/actions/runs/1",
        head_branch="main",
        head_sha="abc123"
    )
    
    logs = "pytest tests/ failed with 3 errors"
    failure_type = workflow_monitor._categorize_failure(run, logs)
    
    assert failure_type == "test_failure"


def test_categorize_failure_lint(workflow_monitor):
    """Test categorizing lint failures."""
    run = WorkflowRun(
        id=1,
        name="Lint",
        status="completed",
        conclusion="failure",
        created_at=datetime.utcnow().isoformat(),
        workflow_id=12345,
        html_url="https://github.com/test/test/actions/runs/1",
        head_branch="main",
        head_sha="abc123"
    )
    
    logs = "black formatter found formatting issues"
    failure_type = workflow_monitor._categorize_failure(run, logs)
    
    assert failure_type == "lint_failure"


def test_categorize_failure_dependency(workflow_monitor):
    """Test categorizing dependency failures."""
    run = WorkflowRun(
        id=1,
        name="CI",
        status="completed",
        conclusion="failure",
        created_at=datetime.utcnow().isoformat(),
        workflow_id=12345,
        html_url="https://github.com/test/test/actions/runs/1",
        head_branch="main",
        head_sha="abc123"
    )
    
    logs = "ERROR: pip install failed with dependency conflict"
    failure_type = workflow_monitor._categorize_failure(run, logs)
    
    assert failure_type == "dependency_failure"


def test_categorize_failure_security(workflow_monitor):
    """Test categorizing security failures."""
    run = WorkflowRun(
        id=1,
        name="Security Scan",
        status="completed",
        conclusion="failure",
        created_at=datetime.utcnow().isoformat(),
        workflow_id=12345,
        html_url="https://github.com/test/test/actions/runs/1",
        head_branch="main",
        head_sha="abc123"
    )
    
    logs = "Found vulnerability CVE-2023-1234"
    failure_type = workflow_monitor._categorize_failure(run, logs)
    
    assert failure_type == "security_failure"


def test_suggest_fix_test_failure(workflow_monitor):
    """Test suggesting fix for test failures."""
    suggestion = workflow_monitor._suggest_fix("test_failure", "")
    
    assert "test" in suggestion.lower()
    assert "fix" in suggestion.lower()


def test_suggest_fix_lint_failure(workflow_monitor):
    """Test suggesting fix for lint failures."""
    suggestion = workflow_monitor._suggest_fix("lint_failure", "")
    
    assert "format" in suggestion.lower() or "lint" in suggestion.lower()


def test_get_workflow_health_status(workflow_monitor):
    """Test getting workflow health status."""
    # Mock successful runs
    mock_workflow = Mock()
    mock_workflow.id = 12345
    mock_workflow.name = "CI"
    mock_workflow.path = ".github/workflows/ci.yml"
    mock_workflow.state = "active"
    
    success_run = Mock()
    success_run.id = 1
    success_run.name = "CI"
    success_run.status = "completed"
    success_run.conclusion = "success"
    success_run.created_at = datetime.utcnow()
    success_run.workflow_id = 12345
    success_run.html_url = "https://github.com/test/test/actions/runs/1"
    success_run.head_branch = "main"
    success_run.head_sha = "abc123"
    
    workflow_monitor.repository.get_workflows.return_value = [mock_workflow]
    workflow_monitor.repository.get_workflow_runs.return_value = [success_run]
    
    health_status = workflow_monitor.get_workflow_health_status()
    
    assert health_status["total_workflows"] == 1
    assert health_status["total_runs_24h"] == 1
    assert health_status["failed_runs_24h"] == 0
    assert health_status["success_rate"] == 100.0
    assert health_status["health_status"] == "healthy"


def test_get_workflow_monitor_singleton():
    """Test that get_workflow_monitor returns singleton instance."""
    with patch('src.genesis.core.workflow_monitor.WorkflowMonitor') as mock:
        monitor1 = get_workflow_monitor()
        monitor2 = get_workflow_monitor()
        
        # Should only create one instance
        assert mock.call_count == 1
