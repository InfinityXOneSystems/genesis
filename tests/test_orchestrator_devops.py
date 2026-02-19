"""
Tests for Genesis Core Orchestrator
"""

import pytest
import json
import tempfile
from pathlib import Path
from src.genesis.core.orchestrator import GenesisOrchestrator, Task, TaskStatus


@pytest.fixture
def temp_manifest():
    """Create a temporary manifest file."""
    fd, manifest_path = tempfile.mkstemp(suffix='.json')
    # Close the file descriptor but keep the path
    import os
    os.close(fd)
    # Remove the file so orchestrator creates it fresh
    Path(manifest_path).unlink(missing_ok=True)
    yield manifest_path
    Path(manifest_path).unlink(missing_ok=True)


def test_orchestrator_initialization(temp_manifest):
    """Test orchestrator initialization."""
    orchestrator = GenesisOrchestrator(manifest_path=temp_manifest)
    assert orchestrator is not None
    assert orchestrator.system_state['version'] == '0.1.0'
    assert orchestrator.system_state['epoch'] == 1


def test_create_task(temp_manifest):
    """Test task creation."""
    orchestrator = GenesisOrchestrator(manifest_path=temp_manifest)
    
    task = orchestrator.create_task(
        title="Test Task",
        description="This is a test task",
        assigned_persona="chief_architect",
        priority=3
    )
    
    assert task is not None
    assert task.title == "Test Task"
    assert task.assigned_persona == "chief_architect"
    assert task.priority == 3
    assert task.status == TaskStatus.PENDING


def test_get_next_task(temp_manifest):
    """Test getting the next task."""
    orchestrator = GenesisOrchestrator(manifest_path=temp_manifest)
    
    # Create multiple tasks with different priorities
    task1 = orchestrator.create_task(
        title="Low Priority",
        description="Low priority task",
        assigned_persona="frontend_lead",
        priority=1
    )
    
    task2 = orchestrator.create_task(
        title="High Priority",
        description="High priority task",
        assigned_persona="backend_lead",
        priority=5
    )
    
    # Get next task should return high priority one
    next_task = orchestrator.get_next_task()
    assert next_task is not None
    assert next_task.priority == 5
    assert next_task.title == "High Priority"


def test_update_task_status(temp_manifest):
    """Test updating task status."""
    orchestrator = GenesisOrchestrator(manifest_path=temp_manifest)
    
    task = orchestrator.create_task(
        title="Test Task",
        description="Test",
        assigned_persona="qa_engineer",
        priority=2
    )
    
    # Update to in progress
    success = orchestrator.update_task_status(
        task.task_id,
        TaskStatus.IN_PROGRESS
    )
    assert success is True
    assert orchestrator.tasks[task.task_id].status == TaskStatus.IN_PROGRESS


def test_get_system_health(temp_manifest):
    """Test getting system health."""
    orchestrator = GenesisOrchestrator(manifest_path=temp_manifest)
    
    # Create some tasks
    orchestrator.create_task("Task 1", "Test", "chief_architect", 1)
    orchestrator.create_task("Task 2", "Test", "frontend_lead", 1)
    
    health = orchestrator.get_system_health()
    
    assert health is not None
    assert health['status'] == 'initializing'
    assert health['epoch'] == 1
    assert health['total_tasks'] == 2
    assert health['pending_tasks'] == 2


def test_initialize_bootstrap_tasks(temp_manifest):
    """Test creating bootstrap tasks."""
    orchestrator = GenesisOrchestrator(manifest_path=temp_manifest)
    
    tasks = orchestrator.initialize_bootstrap_tasks()
    
    assert len(tasks) == 5
    assert any(t.assigned_persona == 'chief_architect' for t in tasks)
    assert any(t.assigned_persona == 'frontend_lead' for t in tasks)
    assert any(t.assigned_persona == 'backend_lead' for t in tasks)


def test_execute_autonomous_cycle(temp_manifest):
    """Test executing an autonomous cycle."""
    orchestrator = GenesisOrchestrator(manifest_path=temp_manifest)
    
    # Create a task first
    orchestrator.create_task(
        title="Test Cycle Task",
        description="Test task for cycle",
        assigned_persona="backend_lead",
        priority=3
    )
    
    result = orchestrator.execute_autonomous_cycle()
    
    assert result is not None
    assert 'cycle_id' in result
    assert 'started_at' in result
    assert 'completed_at' in result


def test_manifest_persistence(temp_manifest):
    """Test that manifest is saved correctly."""
    orchestrator = GenesisOrchestrator(manifest_path=temp_manifest)
    
    orchestrator.create_task(
        title="Persistent Task",
        description="This should persist",
        assigned_persona="devsecops_engineer",
        priority=2
    )
    
    # Check that manifest file was created
    assert Path(temp_manifest).exists()
    
    # Load and verify
    with open(temp_manifest, 'r') as f:
        manifest = json.load(f)
    
    assert manifest['version'] == '0.1.0'
    assert len(manifest['task_queue']) > 0
