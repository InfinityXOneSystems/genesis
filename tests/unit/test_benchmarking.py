"""Tests for benchmarking system"""

import pytest
from pathlib import Path
from genesis.benchmarking import BenchmarkSystem


@pytest.fixture
def benchmark_system():
    """Create a benchmark system"""
    return BenchmarkSystem()


def test_benchmark_initialization(benchmark_system):
    """Test benchmark system initialization"""
    assert benchmark_system is not None
    assert len(benchmark_system.competitors) > 0
    assert "langchain" in benchmark_system.competitors


def test_benchmark_genesis(benchmark_system):
    """Test Genesis benchmarking"""
    scores = benchmark_system._benchmark_genesis()
    
    assert "performance" in scores
    assert "autonomy" in scores
    assert "accuracy" in scores
    assert all(0 <= score <= 1 for score in scores.values())


def test_benchmark_competitor(benchmark_system):
    """Test competitor benchmarking"""
    scores = benchmark_system._benchmark_competitor("langchain")
    
    assert "performance" in scores
    assert "autonomy" in scores
    assert all(0 <= score <= 1 for score in scores.values())


def test_run_benchmarks(benchmark_system):
    """Test running full benchmarks"""
    results = benchmark_system.run_benchmarks()
    
    assert "genesis" in results
    assert "competitors" in results
    assert "comparison" in results
    assert len(results["competitors"]) > 0


def test_calculate_comparison(benchmark_system):
    """Test comparison calculation"""
    results = benchmark_system.run_benchmarks()
    comparison = results["comparison"]
    
    assert "overall_advantage" in comparison
    assert "category_leaders" in comparison
    assert len(comparison["overall_advantage"]) > 0


def test_generate_report(benchmark_system):
    """Test report generation"""
    results = benchmark_system.run_benchmarks()
    report = benchmark_system.generate_report(results)
    
    assert report is not None
    assert len(report) > 0
    assert "Genesis Benchmark Report" in report
    assert "Overall Scores" in report
