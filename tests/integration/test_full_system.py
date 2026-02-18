"""Integration tests for the full system"""

import pytest
from pathlib import Path
from genesis.core import Orchestrator, AutonomousLoop
from genesis.analysis import RepositoryScanner
from genesis.benchmarking import BenchmarkSystem


@pytest.fixture
def test_repo(tmp_path):
    """Create a complete test repository"""
    # Create Python files
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("def main(): pass\n" * 20)
    
    # Create tests
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_main.py").write_text("def test_main(): pass\n")
    
    # Create docs
    (tmp_path / "README.md").write_text("# Test Project\n")
    
    # Create CI
    (tmp_path / ".github").mkdir()
    (tmp_path / ".github" / "workflows").mkdir()
    (tmp_path / ".github" / "workflows" / "ci.yml").write_text("name: CI\n")
    
    return tmp_path


@pytest.mark.asyncio
async def test_full_system_integration(test_repo):
    """Test complete system integration"""
    # 1. Scan repository
    scanner = RepositoryScanner()
    repo_info = scanner.scan_repository(str(test_repo))
    
    assert repo_info is not None
    assert repo_info.has_tests is True
    assert repo_info.has_ci is True
    
    # 2. Run orchestrator
    orchestrator = Orchestrator(
        repository_path=str(test_repo),
        output_dir=test_repo / "output",
    )
    
    results = await orchestrator.run_full_cycle()
    
    assert "planning" in results
    assert "validation" in results
    
    # 3. Run benchmarks
    benchmark_system = BenchmarkSystem()
    benchmark_results = benchmark_system.run_benchmarks()
    
    assert benchmark_results is not None


@pytest.mark.asyncio
async def test_autonomous_loop_integration(test_repo):
    """Test autonomous loop integration"""
    loop = AutonomousLoop(
        repository_path=str(test_repo),
        target_threshold=1.2,
    )
    
    # Run with a low iteration limit for testing
    loop.orchestrator.agents["evolution"].improvement_cycles = 0
    
    result = await loop.run()
    
    assert "iterations" in result
    assert "final_score" in result


@pytest.mark.asyncio
async def test_agent_coordination(test_repo):
    """Test agent coordination and memory sharing"""
    orchestrator = Orchestrator(
        repository_path=str(test_repo),
        output_dir=test_repo / "output",
    )
    
    # Run planner
    plan_result = await orchestrator.run_agent("planner")
    
    # Check that plan is in context
    plan_from_memory = orchestrator.context.get_latest_memory("execution_plan")
    assert plan_from_memory is not None
    
    # Run builder (should use the plan)
    builder_result = await orchestrator.run_agent("builder")
    assert builder_result["status"] == "success"


@pytest.mark.asyncio
async def test_end_to_end_workflow(test_repo):
    """Test complete end-to-end workflow"""
    # Initialize orchestrator
    orchestrator = Orchestrator(
        repository_path=str(test_repo),
        output_dir=test_repo / "output",
    )
    
    # Phase 1: Analysis
    scanner = RepositoryScanner()
    repo_info = scanner.scan_repository(str(test_repo))
    orchestrator.context.analysis_results = {
        "repositories": [repo_info],
    }
    
    # Phase 2: Planning
    plan_result = await orchestrator.run_agent("planner")
    assert "tasks" in plan_result
    
    # Phase 3: Idea Generation
    ideas_result = await orchestrator.run_agent("idea_generator")
    assert len(ideas_result["ideas"]) > 0
    
    # Phase 4: Building
    builder_result = await orchestrator.run_agent("builder")
    assert builder_result["status"] == "success"
    
    # Phase 5: Validation
    validation_result = await orchestrator.run_agent("validator")
    assert validation_result["pass_rate"] > 0
    
    # Phase 6: Memory
    memory_result = await orchestrator.run_agent("memory")
    assert memory_result["memory_size"] > 0
    
    # Phase 7: Evolution
    evolution_result = await orchestrator.run_agent("evolution")
    assert "current_score" in evolution_result
