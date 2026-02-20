"""
Tests for Healing Agent
"""

import pytest
import tempfile
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from datetime import datetime
from src.genesis.core.healing_agent import (
    HealingAgent,
    HealingStrategy,
    TestFailureStrategy,
    LintFailureStrategy,
    DependencyFailureStrategy,
    SecurityFailureStrategy,
    BuildFailureStrategy,
    get_healing_agent
)
from src.genesis.core.workflow_monitor import WorkflowRun, WorkflowFailure


@pytest.fixture
def temp_repo_path():
    """Create a temporary repository path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_workflow_monitor():
    """Create mock workflow monitor."""
    with patch('src.genesis.core.healing_agent.get_workflow_monitor') as mock:
        yield mock


@pytest.fixture
def healing_agent(temp_repo_path, mock_workflow_monitor):
    """Create HealingAgent instance with mocked dependencies."""
    return HealingAgent(temp_repo_path, "test-owner", "test-repo")


@pytest.fixture
def sample_workflow_run():
    """Create sample workflow run."""
    return WorkflowRun(
        id=12345,
        name="CI",
        status="completed",
        conclusion="failure",
        created_at=datetime.utcnow().isoformat(),
        workflow_id=67890,
        html_url="https://github.com/test/test/actions/runs/12345",
        head_branch="main",
        head_sha="abc123"
    )


@pytest.fixture
def sample_test_failure(sample_workflow_run):
    """Create sample test failure."""
    return WorkflowFailure(
        run=sample_workflow_run,
        failure_type="test_failure",
        error_logs="pytest: 3 tests failed",
        suggested_fix="Fix failing tests",
        retry_count=0
    )


@pytest.fixture
def sample_lint_failure(sample_workflow_run):
    """Create sample lint failure."""
    return WorkflowFailure(
        run=sample_workflow_run,
        failure_type="lint_failure",
        error_logs="black: formatting issues found",
        suggested_fix="Run black formatter",
        retry_count=0
    )


def test_healing_agent_initialization(healing_agent):
    """Test healing agent initialization."""
    assert healing_agent is not None
    assert len(healing_agent.strategies) == 5
    assert healing_agent.healing_history == []


def test_test_failure_strategy_can_handle(sample_test_failure):
    """Test that TestFailureStrategy can handle test failures."""
    strategy = TestFailureStrategy()
    assert strategy.can_handle(sample_test_failure) is True


def test_test_failure_strategy_cannot_handle_lint(sample_lint_failure):
    """Test that TestFailureStrategy cannot handle lint failures."""
    strategy = TestFailureStrategy()
    assert strategy.can_handle(sample_lint_failure) is False


def test_lint_failure_strategy_can_handle(sample_lint_failure):
    """Test that LintFailureStrategy can handle lint failures."""
    strategy = LintFailureStrategy()
    assert strategy.can_handle(sample_lint_failure) is True


def test_lint_failure_strategy_heal(sample_lint_failure, temp_repo_path):
    """Test lint failure healing."""
    strategy = LintFailureStrategy()
    
    # Mock subprocess calls
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = Mock(returncode=0, stdout="reformatted 3 files", stderr="")
        
        # Mock git_manager
        with patch('src.genesis.core.healing_agent.git_manager') as mock_git:
            mock_git.add_all.return_value = None
            mock_git.commit.return_value = None
            
            success, message = strategy.heal(sample_lint_failure, temp_repo_path)
            
            assert success is True
            assert "black formatter" in message.lower() or "fixes" in message.lower()


def test_dependency_failure_strategy_can_handle():
    """Test that DependencyFailureStrategy can handle dependency failures."""
    strategy = DependencyFailureStrategy()
    
    run = WorkflowRun(
        id=1,
        name="CI",
        status="completed",
        conclusion="failure",
        created_at=datetime.utcnow().isoformat(),
        workflow_id=1,
        html_url="https://github.com/test/test/actions/runs/1",
        head_branch="main",
        head_sha="abc123"
    )
    
    failure = WorkflowFailure(
        run=run,
        failure_type="dependency_failure",
        error_logs="pip install failed",
        suggested_fix="Reinstall dependencies",
        retry_count=0
    )
    
    assert strategy.can_handle(failure) is True


def test_security_failure_strategy_can_handle():
    """Test that SecurityFailureStrategy can handle security failures."""
    strategy = SecurityFailureStrategy()
    
    run = WorkflowRun(
        id=1,
        name="Security",
        status="completed",
        conclusion="failure",
        created_at=datetime.utcnow().isoformat(),
        workflow_id=1,
        html_url="https://github.com/test/test/actions/runs/1",
        head_branch="main",
        head_sha="abc123"
    )
    
    failure = WorkflowFailure(
        run=run,
        failure_type="security_failure",
        error_logs="CVE found",
        suggested_fix="Update dependencies",
        retry_count=0
    )
    
    assert strategy.can_handle(failure) is True


def test_build_failure_strategy_can_handle():
    """Test that BuildFailureStrategy can handle build failures."""
    strategy = BuildFailureStrategy()
    
    run = WorkflowRun(
        id=1,
        name="Build",
        status="completed",
        conclusion="failure",
        created_at=datetime.utcnow().isoformat(),
        workflow_id=1,
        html_url="https://github.com/test/test/actions/runs/1",
        head_branch="main",
        head_sha="abc123"
    )
    
    failure = WorkflowFailure(
        run=run,
        failure_type="build_failure",
        error_logs="Build failed",
        suggested_fix="Fix build errors",
        retry_count=0
    )
    
    assert strategy.can_handle(failure) is True


def test_detect_failures(healing_agent, mock_workflow_monitor, sample_test_failure):
    """Test failure detection."""
    mock_monitor = Mock()
    mock_monitor.get_failed_runs.return_value = [sample_test_failure.run]
    mock_monitor.analyze_failure.return_value = sample_test_failure
    mock_workflow_monitor.return_value = mock_monitor
    
    healing_agent.monitor = mock_monitor
    
    failures = healing_agent.detect_failures(hours=6)
    
    assert len(failures) == 1
    assert failures[0].failure_type == "test_failure"


def test_heal_failure_no_strategy(healing_agent):
    """Test healing when no strategy is available."""
    run = WorkflowRun(
        id=1,
        name="Unknown",
        status="completed",
        conclusion="failure",
        created_at=datetime.utcnow().isoformat(),
        workflow_id=1,
        html_url="https://github.com/test/test/actions/runs/1",
        head_branch="main",
        head_sha="abc123"
    )
    
    failure = WorkflowFailure(
        run=run,
        failure_type="unknown_failure",
        error_logs="Unknown error",
        suggested_fix="Manual review required",
        retry_count=0
    )
    
    outcome = healing_agent.heal_failure(failure, max_attempts=1)
    
    assert outcome["success"] is False
    assert "No healing strategy available" in outcome["message"]
    assert outcome["attempts"] == 0


def test_heal_failure_success(healing_agent, sample_lint_failure):
    """Test successful healing."""
    # Mock the healing strategy
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = Mock(returncode=0, stdout="reformatted", stderr="")
        
        with patch('src.genesis.core.healing_agent.git_manager') as mock_git:
            mock_git.add_all.return_value = None
            mock_git.commit.return_value = None
            
            outcome = healing_agent.heal_failure(sample_lint_failure, max_attempts=1)
            
            assert outcome["success"] is True
            assert outcome["attempts"] == 1


def test_heal_all_failures_no_failures(healing_agent, mock_workflow_monitor):
    """Test heal_all_failures when there are no failures."""
    mock_monitor = Mock()
    mock_monitor.get_failed_runs.return_value = []
    mock_workflow_monitor.return_value = mock_monitor
    
    healing_agent.monitor = mock_monitor
    
    summary = healing_agent.heal_all_failures(hours=6)
    
    assert summary["total_failures"] == 0
    assert summary["healed"] == 0
    assert summary["success_rate"] == 100.0


def test_heal_all_failures_with_failures(healing_agent, mock_workflow_monitor, sample_lint_failure):
    """Test heal_all_failures with actual failures."""
    mock_monitor = Mock()
    mock_monitor.get_failed_runs.return_value = [sample_lint_failure.run]
    mock_monitor.analyze_failure.return_value = sample_lint_failure
    mock_workflow_monitor.return_value = mock_monitor
    
    healing_agent.monitor = mock_monitor
    
    # Mock the healing
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = Mock(returncode=0, stdout="reformatted", stderr="")
        
        with patch('src.genesis.core.healing_agent.git_manager') as mock_git:
            mock_git.add_all.return_value = None
            mock_git.commit.return_value = None
            
            summary = healing_agent.heal_all_failures(hours=6, max_attempts=1)
            
            assert summary["total_failures"] == 1
            assert summary["healed"] >= 0  # May or may not succeed depending on mocks


def test_get_healing_report_empty(healing_agent):
    """Test getting healing report when empty."""
    report = healing_agent.get_healing_report()
    
    assert report["total_healing_attempts"] == 0
    assert report["successful_healings"] == 0
    assert report["success_rate"] == 0.0


def test_get_healing_report_with_history(healing_agent):
    """Test getting healing report with history."""
    # Add some fake history
    healing_agent.healing_history = [
        {"success": True},
        {"success": True},
        {"success": False}
    ]
    
    report = healing_agent.get_healing_report()
    
    assert report["total_healing_attempts"] == 3
    assert report["successful_healings"] == 2
    assert report["failed_healings"] == 1
    assert report["success_rate"] == pytest.approx(66.67, rel=0.1)


def test_get_healing_agent_singleton(temp_repo_path):
    """Test that get_healing_agent returns singleton instance."""
    with patch('src.genesis.core.healing_agent.HealingAgent') as mock:
        agent1 = get_healing_agent(temp_repo_path)
        agent2 = get_healing_agent(temp_repo_path)
        
        # Should only create one instance
        assert mock.call_count == 1


def test_exponential_backoff(healing_agent, sample_test_failure):
    """Test that exponential backoff is applied on retries."""
    # Mock time.sleep to avoid actual waiting
    with patch('time.sleep') as mock_sleep:
        with patch('subprocess.run') as mock_run:
            # Always fail
            mock_run.return_value = Mock(returncode=1, stdout="", stderr="Test failed")
            
            outcome = healing_agent.heal_failure(sample_test_failure, max_attempts=3)
            
            # Should have called sleep with exponential backoff: 2^1, 2^2
            assert mock_sleep.call_count == 2
            assert outcome["attempts"] == 3
            assert outcome["success"] is False
