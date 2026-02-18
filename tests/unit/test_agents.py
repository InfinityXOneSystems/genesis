"""Tests for agent system"""

import pytest
from pathlib import Path
from genesis.agents import (
    AgentContext,
    PlannerAgent,
    BuilderAgent,
    ValidatorAgent,
    IdeaGeneratorAgent,
    MemoryAgent,
    EvolutionAgent,
    DeploymentAgent,
)


@pytest.fixture
def context():
    """Create a test context"""
    return AgentContext(repository_path="/tmp/test_repo")


@pytest.mark.asyncio
async def test_planner_agent(context):
    """Test PlannerAgent execution"""
    agent = PlannerAgent(context)
    result = await agent.execute()
    
    assert result is not None
    assert "tasks" in result
    assert len(result["tasks"]) > 0
    assert result["total_phases"] > 0


@pytest.mark.asyncio
async def test_builder_agent(context):
    """Test BuilderAgent execution"""
    # Add a plan to context
    context.add_memory("execution_plan", {
        "tasks": [
            {"phase": "implementation", "task": "test_task"}
        ]
    })
    
    agent = BuilderAgent(context)
    result = await agent.execute()
    
    assert result["status"] == "success"
    assert "tasks_completed" in result


@pytest.mark.asyncio
async def test_validator_agent(context):
    """Test ValidatorAgent execution"""
    agent = ValidatorAgent(context)
    result = await agent.execute()
    
    assert result["status"] == "success"
    assert "tests_run" in result
    assert "pass_rate" in result
    assert result["pass_rate"] >= 0 and result["pass_rate"] <= 1


@pytest.mark.asyncio
async def test_idea_generator_agent(context):
    """Test IdeaGeneratorAgent execution"""
    agent = IdeaGeneratorAgent(context)
    result = await agent.execute()
    
    assert result["status"] == "success"
    assert "ideas" in result
    assert len(result["ideas"]) > 0


@pytest.mark.asyncio
async def test_memory_agent(context):
    """Test MemoryAgent execution"""
    agent = MemoryAgent(context)
    
    # Store some data
    agent.store("test_key", "test_value")
    
    # Execute
    result = await agent.execute()
    
    assert result["status"] == "success"
    assert result["memory_size"] >= 1


@pytest.mark.asyncio
async def test_memory_agent_retrieve(context):
    """Test MemoryAgent retrieval"""
    agent = MemoryAgent(context)
    
    # Store data
    agent.store("plan", "execution plan details")
    agent.store("test", "test results")
    
    # Retrieve
    results = agent.retrieve("plan")
    
    assert len(results) > 0
    assert results[0]["key"] == "plan"


@pytest.mark.asyncio
async def test_evolution_agent(context):
    """Test EvolutionAgent execution"""
    # Add some metrics
    context.metrics["ValidatorAgent.test_pass_rate"] = 0.85
    
    agent = EvolutionAgent(context)
    result = await agent.execute()
    
    assert result["status"] == "success"
    assert "current_score" in result
    assert "new_score" in result


@pytest.mark.asyncio
async def test_deployment_agent_success(context):
    """Test DeploymentAgent successful deployment"""
    # Add passing validation results
    context.add_memory("validation_results", {
        "pass_rate": 0.96,
        "security_scan": {"vulnerabilities_found": 0}
    })
    
    agent = DeploymentAgent(context)
    result = await agent.execute()
    
    assert result["status"] == "success"
    assert "deployment_id" in result


@pytest.mark.asyncio
async def test_deployment_agent_blocked(context):
    """Test DeploymentAgent blocked deployment"""
    # Add failing validation results
    context.add_memory("validation_results", {
        "pass_rate": 0.80,
        "security_scan": {"vulnerabilities_found": 2}
    })
    
    agent = DeploymentAgent(context)
    result = await agent.execute()
    
    assert result["status"] == "blocked"


def test_agent_context():
    """Test AgentContext functionality"""
    context = AgentContext(repository_path="/tmp/test")
    
    # Test memory
    context.add_memory("key1", "value1")
    context.add_memory("key2", "value2")
    
    assert len(context.memory) == 2
    assert context.get_latest_memory("key1") == "value1"
    
    # Test metrics
    context.metrics["test_metric"] = 0.95
    assert context.metrics["test_metric"] == 0.95
