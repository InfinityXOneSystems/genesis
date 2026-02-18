"""Tests for orchestrator"""

import pytest
from pathlib import Path
from genesis.core import Orchestrator


@pytest.fixture
def orchestrator(tmp_path):
    """Create a test orchestrator"""
    return Orchestrator(
        repository_path=str(tmp_path),
        output_dir=tmp_path / "output",
    )


@pytest.mark.asyncio
async def test_orchestrator_initialization(orchestrator):
    """Test orchestrator initialization"""
    assert orchestrator is not None
    assert len(orchestrator.agents) == 7
    assert "planner" in orchestrator.agents
    assert "builder" in orchestrator.agents
    assert "validator" in orchestrator.agents


@pytest.mark.asyncio
async def test_run_agent(orchestrator):
    """Test running a single agent"""
    result = await orchestrator.run_agent("planner")
    
    assert result is not None
    assert "tasks" in result


@pytest.mark.asyncio
async def test_run_full_cycle(orchestrator):
    """Test running a full cycle"""
    results = await orchestrator.run_full_cycle()
    
    assert results is not None
    assert "planning" in results
    assert "validation" in results
    assert "evolution" in results


@pytest.mark.asyncio
async def test_run_invalid_agent(orchestrator):
    """Test running an invalid agent"""
    with pytest.raises(ValueError):
        await orchestrator.run_agent("invalid_agent")


def test_get_system_status(orchestrator):
    """Test getting system status"""
    status = orchestrator.get_system_status()
    
    assert "agents" in status
    assert "context" in status
    assert len(status["agents"]) == 7
