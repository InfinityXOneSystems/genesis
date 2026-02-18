"""
Tests for Genesis Core Repository Scanner
"""

import pytest
from src.genesis.core.repo_scanner import RepoScanner, RepositoryInfo


def test_scanner_initialization():
    """Test scanner initialization."""
    scanner = RepoScanner()
    assert scanner is not None
    assert scanner.base_url == "https://api.github.com"


def test_scanner_with_token():
    """Test scanner with GitHub token."""
    scanner = RepoScanner(github_token="test_token")
    assert scanner.github_token == "test_token"


def test_list_organization_repos():
    """Test listing organization repositories."""
    scanner = RepoScanner()
    repos = scanner.list_organization_repos("InfinityXOneSystems")
    assert repos is not None
    assert isinstance(repos, list)


def test_analyze_repository():
    """Test repository analysis."""
    scanner = RepoScanner()
    analysis = scanner.analyze_repository("InfinityXOneSystems/genesis")
    
    assert analysis is not None
    assert 'repository' in analysis
    assert 'health_score' in analysis
    assert 'opportunities' in analysis
    assert analysis['repository'] == "InfinityXOneSystems/genesis"


def test_health_score_calculation():
    """Test health score calculation."""
    scanner = RepoScanner()
    
    # Test with no opportunities
    analysis = {
        'opportunities': []
    }
    score = scanner._calculate_health_score(analysis)
    assert score == 1.0
    
    # Test with some opportunities
    analysis = {
        'opportunities': [
            {'type': 'test', 'severity': 'medium'},
            {'type': 'test', 'severity': 'low'}
        ]
    }
    score = scanner._calculate_health_score(analysis)
    assert 0.0 <= score <= 1.0
    assert score < 1.0


def test_scan_for_improvements():
    """Test scanning for improvements."""
    scanner = RepoScanner()
    improvements = scanner.scan_for_improvements("InfinityXOneSystems")
    
    assert improvements is not None
    assert isinstance(improvements, list)


def test_generate_improvement_tasks():
    """Test generating tasks from opportunities."""
    scanner = RepoScanner()
    
    opportunities = [
        {
            'type': 'documentation',
            'severity': 'medium',
            'title': 'Missing README',
            'description': 'Add README file'
        },
        {
            'type': 'testing',
            'severity': 'high',
            'title': 'Add tests',
            'description': 'Add unit tests'
        }
    ]
    
    tasks = scanner.generate_improvement_tasks(opportunities)
    
    assert len(tasks) == 2
    assert tasks[0]['type'] == 'documentation'
    assert tasks[0]['persona'] == 'chief_architect'
    assert tasks[1]['type'] == 'testing'
    assert tasks[1]['persona'] == 'qa_engineer'


def test_assign_persona_for_opportunity():
    """Test persona assignment for different opportunity types."""
    scanner = RepoScanner()
    
    assert scanner._assign_persona_for_opportunity('documentation') == 'chief_architect'
    assert scanner._assign_persona_for_opportunity('frontend') == 'frontend_lead'
    assert scanner._assign_persona_for_opportunity('backend') == 'backend_lead'
    assert scanner._assign_persona_for_opportunity('security') == 'devsecops_engineer'
    assert scanner._assign_persona_for_opportunity('testing') == 'qa_engineer'
    assert scanner._assign_persona_for_opportunity('ci_cd') == 'devsecops_engineer'
    assert scanner._assign_persona_for_opportunity('unknown') == 'chief_architect'
