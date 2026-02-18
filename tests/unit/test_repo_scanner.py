"""Tests for repository scanner"""

import pytest
from pathlib import Path
from genesis.analysis import RepositoryScanner, RepositoryInfo


@pytest.fixture
def scanner():
    """Create a repository scanner"""
    return RepositoryScanner()


@pytest.fixture
def test_repo(tmp_path):
    """Create a test repository"""
    # Create some test files
    (tmp_path / "main.py").write_text("print('hello')\n" * 10)
    (tmp_path / "test.py").write_text("def test_main(): pass\n")
    (tmp_path / "README.md").write_text("# Test Repo\n")
    
    # Create tests directory
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_example.py").write_text("def test_example(): pass\n")
    
    return tmp_path


def test_scan_repository(scanner, test_repo):
    """Test repository scanning"""
    info = scanner.scan_repository(str(test_repo))
    
    assert info is not None
    assert info.name == test_repo.name
    assert info.language == "Python"
    assert info.files_count > 0
    assert info.lines_of_code > 0
    assert info.has_tests is True


def test_detect_language(scanner, tmp_path):
    """Test language detection"""
    # Create Python files
    (tmp_path / "test.py").write_text("print('test')")
    
    info = scanner.scan_repository(str(tmp_path))
    assert info.language == "Python"


def test_has_tests(scanner, test_repo):
    """Test test detection"""
    info = scanner.scan_repository(str(test_repo))
    assert info.has_tests is True


def test_has_docs(scanner, test_repo):
    """Test documentation detection"""
    info = scanner.scan_repository(str(test_repo))
    assert info.has_docs is True


def test_generate_global_analysis(scanner, test_repo):
    """Test global analysis generation"""
    repo_info = scanner.scan_repository(str(test_repo))
    
    analysis = scanner.generate_global_analysis([repo_info])
    
    assert "summary" in analysis
    assert "repositories" in analysis
    assert "dependency_graph" in analysis
    assert "anti_patterns" in analysis
    assert analysis["summary"]["total_repositories"] == 1


def test_identify_anti_patterns(scanner, tmp_path):
    """Test anti-pattern identification"""
    # Create repo without tests
    (tmp_path / "main.py").write_text("print('test')")
    
    info = scanner.scan_repository(str(tmp_path))
    analysis = scanner.generate_global_analysis([info])
    
    assert len(analysis["anti_patterns"]) > 0
    assert any(p["pattern"] == "no_tests" for p in analysis["anti_patterns"])
