"""
Tests for DevOps team agents and modules
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from genesis.core.workflow_analyzer import WorkflowAnalyzer, FailureCategory
from genesis.core.auto_diagnostician import AutoDiagnostician, IssueType
from genesis.core.auto_healer import AutoHealer, HealingStrategy
from genesis.core.conflict_resolver import ConflictResolver
from genesis.core.auto_validator import AutoValidator, ValidationStatus
from genesis.core.auto_merger import AutoMerger, MergeStatus
from genesis.core.pr_automation import (
    PRAutomation,
    PRStatus,
    ValidationCheckType,
    PRAnalysis,
    ValidationReport,
    MergeReport,
)


class TestWorkflowAnalyzer:
    """Tests for WorkflowAnalyzer."""
    
    def test_initialization(self):
        """Test workflow analyzer initialization."""
        analyzer = WorkflowAnalyzer()
        assert analyzer is not None
        assert analyzer.failure_patterns is not None
    
    def test_categorize_test_failure(self):
        """Test categorization of test failures."""
        analyzer = WorkflowAnalyzer()
        logs = "Error: test_function failed with assertion error"
        
        result = analyzer.analyze_workflow_run(
            workflow_name="CI",
            run_id=123,
            logs=logs,
            status="failure"
        )
        
        assert result["category"] == FailureCategory.TEST_FAILURE.value
        assert result["severity"] in ["low", "medium", "high", "critical"]
    
    def test_categorize_lint_failure(self):
        """Test categorization of lint failures."""
        analyzer = WorkflowAnalyzer()
        logs = "Error: pylint found style violations"
        
        result = analyzer.analyze_workflow_run(
            workflow_name="Lint",
            run_id=124,
            logs=logs,
            status="failure"
        )
        
        assert result["category"] == FailureCategory.LINT_FAILURE.value
    
    def test_categorize_build_failure(self):
        """Test categorization of build failures."""
        analyzer = WorkflowAnalyzer()
        logs = "Error: build failed with compilation error"
        
        result = analyzer.analyze_workflow_run(
            workflow_name="Build",
            run_id=125,
            logs=logs,
            status="failure"
        )
        
        assert result["category"] == FailureCategory.BUILD_FAILURE.value
    
    def test_success_status(self):
        """Test analysis of successful runs."""
        analyzer = WorkflowAnalyzer()
        
        result = analyzer.analyze_workflow_run(
            workflow_name="CI",
            run_id=126,
            logs="All tests passed",
            status="success"
        )
        
        assert result["category"] == "success"
        assert result["failures"] == []


class TestAutoDiagnostician:
    """Tests for AutoDiagnostician."""
    
    def test_initialization(self):
        """Test auto diagnostician initialization."""
        diagnostician = AutoDiagnostician()
        assert diagnostician is not None
    
    def test_diagnose_dependency_error(self):
        """Test diagnosis of dependency errors."""
        diagnostician = AutoDiagnostician()
        
        diagnosis = diagnostician.diagnose_error(
            error_message="ModuleNotFoundError: No module named 'pytest'",
            stack_trace="Traceback: File test.py, line 1"
        )
        
        assert diagnosis.issue_type == IssueType.DEPENDENCY_CONFLICT
        assert len(diagnosis.recommendations) > 0
        assert diagnosis.severity in ["low", "medium", "high", "critical"]
    
    def test_diagnose_configuration_error(self):
        """Test diagnosis of configuration errors."""
        diagnostician = AutoDiagnostician()
        
        diagnosis = diagnostician.diagnose_error(
            error_message="Configuration error: Missing environment variable API_KEY"
        )
        
        assert diagnosis.issue_type == IssueType.CONFIGURATION_ERROR
        assert "environment" in diagnosis.root_cause.lower()
    
    def test_diagnose_security_vulnerability(self):
        """Test diagnosis of security vulnerabilities."""
        diagnostician = AutoDiagnostician()
        
        diagnosis = diagnostician.diagnose_error(
            error_message="Security vulnerability: CVE-2023-12345 found in dependency"
        )
        
        assert diagnosis.issue_type == IssueType.SECURITY_VULNERABILITY
        assert diagnosis.severity in ["high", "critical"]
    
    def test_collect_evidence(self):
        """Test evidence collection."""
        diagnostician = AutoDiagnostician()
        
        diagnosis = diagnostician.diagnose_error(
            error_message="Test error",
            stack_trace="File test.py line 10\nFile main.py line 5",
            context={"file": "test.py", "line": 10}
        )
        
        assert len(diagnosis.evidence) > 0
        assert len(diagnosis.affected_files) > 0


class TestAutoHealer:
    """Tests for AutoHealer."""
    
    def test_initialization(self):
        """Test auto healer initialization."""
        healer = AutoHealer()
        assert healer is not None
        assert healer.repo_path is not None
    
    def test_select_strategy_dependency(self):
        """Test strategy selection for dependency issues."""
        healer = AutoHealer()
        
        from genesis.core.auto_diagnostician import DiagnosisResult
        
        diagnosis = DiagnosisResult(
            issue_type=IssueType.DEPENDENCY_CONFLICT,
            severity="medium",
            description="Missing dependency",
            root_cause="Module not installed",
            evidence=["ModuleNotFoundError"],
            affected_files=["test.py"],
            recommendations=["Install module"]
        )
        
        strategy = healer._select_strategy(diagnosis)
        assert strategy == HealingStrategy.DEPENDENCY_UPDATE
    
    def test_select_strategy_security(self):
        """Test strategy selection for security issues."""
        healer = AutoHealer()
        
        from genesis.core.auto_diagnostician import DiagnosisResult
        
        diagnosis = DiagnosisResult(
            issue_type=IssueType.SECURITY_VULNERABILITY,
            severity="high",
            description="Security issue",
            root_cause="Vulnerable dependency",
            evidence=["CVE-2023-12345"],
            affected_files=[],
            recommendations=["Update package"]
        )
        
        strategy = healer._select_strategy(diagnosis)
        assert strategy == HealingStrategy.SECURITY_PATCH


class TestConflictResolver:
    """Tests for ConflictResolver."""
    
    def test_initialization(self):
        """Test conflict resolver initialization."""
        resolver = ConflictResolver()
        assert resolver is not None
        assert resolver.repo_path is not None
    
    def test_parse_conflicts(self):
        """Test conflict parsing."""
        resolver = ConflictResolver()
        
        content = """
line 1
<<<<<<< HEAD
ours line
=======
theirs line
>>>>>>> branch
line 2
"""
        
        conflicts = resolver._parse_conflicts(content)
        assert len(conflicts) == 1
        assert conflicts[0]['ours_content'].strip() == "ours line"
        assert conflicts[0]['theirs_content'].strip() == "theirs line"
    
    def test_resolve_identical_sides(self):
        """Test resolution when both sides are identical."""
        resolver = ConflictResolver()
        
        conflict = {
            'ours_content': 'same line\n',
            'theirs_content': 'same line\n'
        }
        
        resolution = resolver._resolve_conflict(conflict, "test.py")
        assert resolution == 'same line\n'
    
    def test_resolve_empty_side(self):
        """Test resolution when one side is empty."""
        resolver = ConflictResolver()
        
        conflict = {
            'ours_content': '',
            'theirs_content': 'their code\n'
        }
        
        resolution = resolver._resolve_conflict(conflict, "test.py")
        assert resolution == 'their code\n'


class TestAutoValidator:
    """Tests for AutoValidator."""
    
    def test_initialization(self):
        """Test auto validator initialization."""
        validator = AutoValidator()
        assert validator is not None
        assert validator.repo_path is not None
    
    def test_calculate_quality_score(self):
        """Test quality score calculation."""
        validator = AutoValidator()
        
        checks = [
            {
                "name": "tests",
                "status": ValidationStatus.PASSED.value,
                "passed": 10,
                "failed": 0
            },
            {
                "name": "linters",
                "status": ValidationStatus.PASSED.value
            }
        ]
        
        score = validator._calculate_quality_score(checks)
        assert 90 <= score <= 110  # With bonus for 100% pass rate
    
    def test_calculate_quality_score_with_failures(self):
        """Test quality score with failures."""
        validator = AutoValidator()
        
        checks = [
            {
                "name": "tests",
                "status": ValidationStatus.FAILED.value,
                "passed": 5,
                "failed": 5
            }
        ]
        
        score = validator._calculate_quality_score(checks)
        assert score < 100


class TestAutoMerger:
    """Tests for AutoMerger."""
    
    def test_initialization(self):
        """Test auto merger initialization."""
        merger = AutoMerger()
        assert merger is not None
        assert merger.repo_path is not None
    
    def test_generate_squash_message(self):
        """Test squash message generation."""
        merger = AutoMerger()
        
        commits = [
            "abc123 Fix bug",
            "def456 Add feature",
            "ghi789 Update docs"
        ]
        
        message = merger._generate_squash_message(pr_number=42, commits=commits)
        
        assert "PR #42" in message
        assert "Fix bug" in message
        assert "Add feature" in message
        assert "Update docs" in message
    
    def test_can_merge_pr_structure(self):
        """Test PR merge readiness check structure."""
        merger = AutoMerger()
        
        readiness = merger.can_merge_pr(pr_number=123)
        
        assert "can_merge" in readiness
        assert "pr_number" in readiness
        assert "checks" in readiness
        assert "blockers" in readiness
        assert readiness["pr_number"] == 123


def test_agent_team_includes_devops_agents():
    """Test that agent team includes new DevOps agents."""
    from genesis.core.agent_team import agent_team
    
    personas = agent_team.list_personas()
    
    # Check for new DevOps agents
    assert "workflow_analyzer" in personas
    assert "auto_diagnostician" in personas
    assert "auto_healer" in personas
    assert "conflict_resolver" in personas
    assert "auto_validator" in personas
    assert "auto_merger" in personas


def test_all_devops_agents_have_system_prompts():
    """Test that all DevOps agents have system prompts."""
    from genesis.core.agent_team import agent_team
    
    devops_agents = [
        "workflow_analyzer",
        "auto_diagnostician",
        "auto_healer",
        "conflict_resolver",
        "auto_validator",
        "auto_merger"
    ]
    
    for agent_id in devops_agents:
        persona = agent_team.get_persona(agent_id)
        assert persona is not None
        assert persona.system_prompt
        assert len(persona.system_prompt) > 100
        assert persona.expertise
        assert persona.responsibilities


class TestPRAutomation:
    """Tests for the zero-friction PRAutomation module."""

    def test_initialization(self):
        """Test PR automation initializes correctly."""
        automation = PRAutomation()
        assert automation is not None
        assert automation.repo_path is not None

    def test_pr_status_enum_values(self):
        """Test PRStatus enum has required states."""
        assert PRStatus.PENDING.value == "pending"
        assert PRStatus.MERGED.value == "merged"
        assert PRStatus.FAILED.value == "failed"
        assert PRStatus.VALIDATION_PASSED.value == "validation_passed"
        assert PRStatus.CONFLICTS_DETECTED.value == "conflicts_detected"

    def test_validation_check_type_enum(self):
        """Test ValidationCheckType enum covers all check types."""
        types = {e.value for e in ValidationCheckType}
        assert "tests" in types
        assert "linting" in types
        assert "security" in types
        assert "type_check" in types
        assert "format" in types

    def test_pr_analysis_to_dict(self):
        """Test PRAnalysis serialises to a complete dictionary."""
        analysis = PRAnalysis(
            pr_number=7,
            title="Add feature X",
            branch="feature/x",
            base_branch="main",
            has_conflicts=False,
            conflicted_files=[],
            files_changed=3,
            commits=["abc123 Initial commit"],
            quality_issues=[],
        )
        data = analysis.to_dict()
        assert data["pr_number"] == 7
        assert data["title"] == "Add feature X"
        assert data["has_conflicts"] is False
        assert data["files_changed"] == 3
        assert "analyzed_at" in data

    def test_pr_analysis_with_conflicts(self):
        """Test PRAnalysis with conflicts present."""
        analysis = PRAnalysis(
            pr_number=8,
            title="Conflicting PR",
            branch="fix/conflict",
            base_branch="main",
            has_conflicts=True,
            conflicted_files=["src/foo.py", "src/bar.py"],
            files_changed=2,
            commits=[],
            quality_issues=["Syntax error in foo.py"],
        )
        data = analysis.to_dict()
        assert data["has_conflicts"] is True
        assert len(data["conflicted_files"]) == 2
        assert len(data["quality_issues"]) == 1

    def test_validation_report_passed(self):
        """Test ValidationReport for a fully passing pipeline."""
        report = ValidationReport(
            passed=True,
            checks={
                "tests":    {"passed": True, "summary": "51 passed, 0 failed"},
                "linting":  {"passed": True, "summary": "clean"},
                "security": {"passed": True, "summary": "clean"},
            },
            issues=[],
            quality_score=1.0,
        )
        data = report.to_dict()
        assert data["passed"] is True
        assert data["quality_score"] == 1.0
        assert data["issues"] == []
        assert "validated_at" in data

    def test_validation_report_failed(self):
        """Test ValidationReport for a failing pipeline."""
        report = ValidationReport(
            passed=False,
            checks={
                "tests":   {"passed": False, "summary": "2 failed"},
                "linting": {"passed": True,  "summary": "clean"},
            },
            issues=["Tests failed: 2 failed"],
            quality_score=0.5,
        )
        data = report.to_dict()
        assert data["passed"] is False
        assert data["quality_score"] == 0.5
        assert len(data["issues"]) == 1

    def test_merge_report_success(self):
        """Test MergeReport for a successful squash-merge."""
        report = MergeReport(
            success=True,
            pr_number=42,
            commit_sha="deadbeef",
            squashed=True,
        )
        data = report.to_dict()
        assert data["success"] is True
        assert data["pr_number"] == 42
        assert data["commit_sha"] == "deadbeef"
        assert data["squashed"] is True
        assert data["error_message"] is None
        assert "merged_at" in data

    def test_merge_report_failure(self):
        """Test MergeReport for a failed merge."""
        report = MergeReport(
            success=False,
            pr_number=99,
            commit_sha=None,
            squashed=False,
            error_message="Merge conflict unresolved",
        )
        data = report.to_dict()
        assert data["success"] is False
        assert data["error_message"] == "Merge conflict unresolved"

    def test_apply_conflict_strategy_ours(self):
        """Test conflict resolution keeps 'ours' side."""
        automation = PRAutomation()
        content = "before\n<<<<<<< HEAD\nours content\n=======\ntheirs content\n>>>>>>> feature\nafter\n"
        resolved = automation._apply_conflict_strategy(content, "ours")
        assert "ours content" in resolved
        assert "theirs content" not in resolved
        assert "<<<<<<" not in resolved

    def test_apply_conflict_strategy_theirs(self):
        """Test conflict resolution keeps 'theirs' side."""
        automation = PRAutomation()
        content = "before\n<<<<<<< HEAD\nours content\n=======\ntheirs content\n>>>>>>> feature\nafter\n"
        resolved = automation._apply_conflict_strategy(content, "theirs")
        assert "theirs content" in resolved
        assert "ours content" not in resolved
        assert "<<<<<<" not in resolved

    def test_apply_conflict_strategy_larger(self):
        """Test conflict resolution keeps the longer side."""
        automation = PRAutomation()
        # 'theirs' is longer → should be chosen
        content = (
            "<<<<<<< HEAD\n"
            "short\n"
            "=======\n"
            "much longer theirs content here\n"
            ">>>>>>> feature\n"
        )
        resolved = automation._apply_conflict_strategy(content, "larger")
        assert "much longer theirs content here" in resolved

    def test_calculate_quality_score_all_pass(self):
        """Test quality score is 1.0 when all checks pass."""
        automation = PRAutomation()
        checks = {
            "tests":    {"passed": True},
            "linting":  {"passed": True},
            "security": {"passed": True},
        }
        score = automation._calculate_quality_score(checks)
        assert score == 1.0

    def test_calculate_quality_score_partial(self):
        """Test quality score is fractional when some checks fail."""
        automation = PRAutomation()
        checks = {
            "tests":    {"passed": True},
            "linting":  {"passed": False},
            "security": {"passed": True},
        }
        score = automation._calculate_quality_score(checks)
        assert abs(score - 2 / 3) < 0.01

    def test_calculate_quality_score_empty(self):
        """Test quality score is 1.0 when no checks were run."""
        automation = PRAutomation()
        assert automation._calculate_quality_score({}) == 1.0

    def test_build_squash_commit_body(self):
        """Test squash commit body includes PR reference and commit list."""
        automation = PRAutomation()
        commits = ["abc123 Fix bug", "def456 Add feature"]
        body = automation._build_squash_commit_body(55, "feature/test", commits)
        assert "PR #55" in body
        assert "Fix bug" in body
        assert "Add feature" in body
        assert "Genesis PR Automation" in body

    def test_build_squash_commit_body_many_commits(self):
        """Test squash commit body truncates long commit lists."""
        automation = PRAutomation()
        commits = [f"sha{i} commit {i}" for i in range(30)]
        body = automation._build_squash_commit_body(10, "feature/many", commits)
        assert "and 10 more commits" in body

    def test_singleton_instance(self):
        """Test the module-level singleton is a PRAutomation instance."""
        from genesis.core.pr_automation import pr_automation
        assert isinstance(pr_automation, PRAutomation)
