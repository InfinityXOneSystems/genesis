"""
Tests for Genesis Core Agent Team
"""

import pytest
from src.genesis.core.agent_team import AgentTeam, agent_team


def test_agent_team_initialization():
    """Test that agent team initializes correctly."""
    team = AgentTeam()
    assert team is not None
    assert len(team.personas) == 11  # 5 original + 6 DevOps agents


def test_list_personas():
    """Test listing all available personas."""
    personas = agent_team.list_personas()
    assert len(personas) == 11  # 5 original + 6 DevOps agents
    # Original agents
    assert 'chief_architect' in personas
    assert 'frontend_lead' in personas
    assert 'backend_lead' in personas
    assert 'devsecops_engineer' in personas
    assert 'qa_engineer' in personas
    # DevOps team agents
    assert 'workflow_analyzer' in personas
    assert 'auto_diagnostician' in personas
    assert 'auto_healer' in personas
    assert 'conflict_resolver' in personas
    assert 'auto_validator' in personas
    assert 'auto_merger' in personas


def test_get_persona():
    """Test getting a specific persona."""
    persona = agent_team.get_persona('chief_architect')
    assert persona is not None
    assert persona.name == 'Chief Architect'
    assert persona.role == 'System Architecture & High-Level Design'
    assert len(persona.expertise) > 0
    assert len(persona.system_prompt) > 0


def test_persona_has_required_fields():
    """Test that all personas have required fields."""
    for persona_id in agent_team.list_personas():
        persona = agent_team.get_persona(persona_id)
        assert persona.name
        assert persona.role
        assert persona.expertise
        assert persona.system_prompt
        assert persona.tools
        assert persona.responsibilities


def test_chief_architect_persona():
    """Test Chief Architect persona details."""
    persona = agent_team.get_persona('chief_architect')
    assert 'System Design' in persona.expertise
    assert 'architecture' in persona.system_prompt.lower()
    assert 'code_analysis' in persona.tools


def test_frontend_lead_persona():
    """Test Frontend Lead persona details."""
    persona = agent_team.get_persona('frontend_lead')
    assert 'React/Next.js' in persona.expertise
    assert 'TypeScript' in persona.expertise
    assert 'typescript' in persona.system_prompt.lower()


def test_backend_lead_persona():
    """Test Backend Lead persona details."""
    persona = agent_team.get_persona('backend_lead')
    assert 'Python/FastAPI' in persona.expertise
    assert 'fastapi' in persona.system_prompt.lower()


def test_devsecops_persona():
    """Test DevSecOps Engineer persona details."""
    persona = agent_team.get_persona('devsecops_engineer')
    assert 'GitHub Actions' in persona.expertise
    assert 'security' in persona.system_prompt.lower()


def test_qa_engineer_persona():
    """Test QA Engineer persona details."""
    persona = agent_team.get_persona('qa_engineer')
    assert 'Test Automation' in persona.expertise
    assert 'test' in persona.system_prompt.lower()


def test_invalid_persona():
    """Test getting a non-existent persona."""
    persona = agent_team.get_persona('invalid_persona')
    assert persona is None
