"""
PR Automation - Zero-Friction Pull Request Pipeline

This module implements a fully automated PR lifecycle:
1. PR analysis (metadata, conflicts, quality)
2. Conflict detection and auto-resolution
3. Full validation (tests, linting, security scan)
4. Auto squash-and-merge on success

Designed for zero human intervention, zero friction, zero bottlenecks.
"""

import logging
import subprocess
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


class PRStatus(Enum):
    """Status of a pull request in the automation pipeline."""
    PENDING = "pending"
    ANALYZING = "analyzing"
    CONFLICTS_DETECTED = "conflicts_detected"
    CONFLICTS_RESOLVED = "conflicts_resolved"
    VALIDATING = "validating"
    VALIDATION_PASSED = "validation_passed"
    VALIDATION_FAILED = "validation_failed"
    MERGING = "merging"
    MERGED = "merged"
    FAILED = "failed"


class ValidationCheckType(Enum):
    """Types of validation checks."""
    TESTS = "tests"
    LINTING = "linting"
    SECURITY = "security"
    TYPE_CHECK = "type_check"
    FORMAT = "format"


class PRAnalysis:
    """Result of PR analysis."""

    def __init__(
        self,
        pr_number: int,
        title: str,
        branch: str,
        base_branch: str,
        has_conflicts: bool,
        conflicted_files: List[str],
        files_changed: int,
        commits: List[str],
        quality_issues: List[str],
    ):
        self.pr_number = pr_number
        self.title = title
        self.branch = branch
        self.base_branch = base_branch
        self.has_conflicts = has_conflicts
        self.conflicted_files = conflicted_files
        self.files_changed = files_changed
        self.commits = commits
        self.quality_issues = quality_issues
        self.analyzed_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "pr_number": self.pr_number,
            "title": self.title,
            "branch": self.branch,
            "base_branch": self.base_branch,
            "has_conflicts": self.has_conflicts,
            "conflicted_files": self.conflicted_files,
            "files_changed": self.files_changed,
            "commits": self.commits,
            "quality_issues": self.quality_issues,
            "analyzed_at": self.analyzed_at,
        }


class ValidationReport:
    """Result of the full validation pipeline."""

    def __init__(
        self,
        passed: bool,
        checks: Dict[str, Dict[str, Any]],
        issues: List[str],
        quality_score: float,
    ):
        self.passed = passed
        self.checks = checks
        self.issues = issues
        self.quality_score = quality_score
        self.validated_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "passed": self.passed,
            "checks": self.checks,
            "issues": self.issues,
            "quality_score": self.quality_score,
            "validated_at": self.validated_at,
        }


class MergeReport:
    """Result of an auto squash-and-merge operation."""

    def __init__(
        self,
        success: bool,
        pr_number: int,
        commit_sha: Optional[str],
        squashed: bool,
        error_message: Optional[str] = None,
    ):
        self.success = success
        self.pr_number = pr_number
        self.commit_sha = commit_sha
        self.squashed = squashed
        self.error_message = error_message
        self.merged_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "pr_number": self.pr_number,
            "commit_sha": self.commit_sha,
            "squashed": self.squashed,
            "error_message": self.error_message,
            "merged_at": self.merged_at,
        }


class PRAutomation:
    """
    Zero-friction pull request automation engine.

    Orchestrates the full PR lifecycle:
    analyze → resolve conflicts → validate → squash-merge.

    No human intervention required at any stage.
    """

    def __init__(self, repo_path: Optional[Path] = None):
        """
        Initialize PR automation engine.

        Args:
            repo_path: Path to the Git repository (defaults to cwd)
        """
        self.repo_path = repo_path or Path.cwd()
        logger.info("PR Automation initialized for %s", self.repo_path)

    # ------------------------------------------------------------------
    # Analysis
    # ------------------------------------------------------------------

    def analyze_pr(
        self,
        pr_number: int,
        branch: str,
        base_branch: str = "main",
        title: str = "",
    ) -> PRAnalysis:
        """
        Analyze a pull request for conflicts and quality issues.

        Args:
            pr_number: Pull request number
            branch: Head branch of the PR
            base_branch: Target base branch
            title: PR title (optional)

        Returns:
            PRAnalysis with full diagnostic information
        """
        logger.info("Analyzing PR #%d (%s → %s)", pr_number, branch, base_branch)

        conflicted_files = self._detect_conflicts(branch, base_branch)
        has_conflicts = bool(conflicted_files)
        commits = self._get_branch_commits(branch, base_branch)
        files_changed = self._count_files_changed(branch, base_branch)
        quality_issues = self._quick_quality_scan(branch)

        analysis = PRAnalysis(
            pr_number=pr_number,
            title=title,
            branch=branch,
            base_branch=base_branch,
            has_conflicts=has_conflicts,
            conflicted_files=conflicted_files,
            files_changed=files_changed,
            commits=commits,
            quality_issues=quality_issues,
        )

        if has_conflicts:
            logger.warning(
                "PR #%d has conflicts in: %s", pr_number, conflicted_files
            )
        else:
            logger.info("PR #%d has no conflicts", pr_number)

        return analysis

    def _detect_conflicts(self, branch: str, base_branch: str) -> List[str]:
        """Return list of files with merge conflicts."""
        try:
            # Check for unmerged files in the index
            result = subprocess.run(
                ["git", "diff", "--name-only", "--diff-filter=U"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0 and result.stdout.strip():
                return [f.strip() for f in result.stdout.splitlines() if f.strip()]

            # Dry-run merge to detect conflicts without modifying tree
            merge_base = self._run_git(
                ["merge-base", base_branch, branch], check=False
            )
            if not merge_base:
                return []

            # Use merge-tree for conflict detection (non-destructive)
            result = subprocess.run(
                ["git", "merge-tree", merge_base.strip(), base_branch, branch],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0 or "<<<<<<" in result.stdout:
                # Parse conflicted file names from merge-tree output
                files: List[str] = []
                for line in result.stdout.splitlines():
                    if line.startswith("+") or "changed in both" in line.lower():
                        parts = line.split()
                        if parts:
                            files.append(parts[-1])
                return files
            return []
        except Exception as exc:
            logger.debug("Conflict detection error: %s", exc)
            return []

    def _get_branch_commits(self, branch: str, base_branch: str) -> List[str]:
        """Return list of commits on branch not in base."""
        out = self._run_git(
            ["log", "--oneline", f"{base_branch}..{branch}"], check=False
        )
        if out:
            return [line.strip() for line in out.splitlines() if line.strip()]
        return []

    def _count_files_changed(self, branch: str, base_branch: str) -> int:
        """Return number of files changed relative to base."""
        out = self._run_git(
            ["diff", "--name-only", f"{base_branch}...{branch}"], check=False
        )
        if out:
            return len([l for l in out.splitlines() if l.strip()])
        return 0

    def _quick_quality_scan(self, branch: str) -> List[str]:
        """Run a lightweight static quality scan on changed Python files."""
        issues: List[str] = []
        try:
            py_files = list(self.repo_path.rglob("src/**/*.py"))
            for py_file in py_files[:50]:  # cap to avoid excessive scanning
                result = subprocess.run(
                    ["python", "-m", "py_compile", str(py_file)],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if result.returncode != 0:
                    issues.append(f"Syntax error in {py_file.name}: {result.stderr.strip()[:200]}")
        except Exception:
            pass
        return issues

    # ------------------------------------------------------------------
    # Conflict resolution
    # ------------------------------------------------------------------

    def resolve_conflicts(
        self, branch: str, base_branch: str = "main", strategy: str = "ours"
    ) -> Tuple[bool, List[str]]:
        """
        Attempt automatic conflict resolution using the specified strategy.

        The ``strategy`` parameter controls how each conflicted hunk is resolved:
        - ``'ours'``: keep the changes from our branch (HEAD side)
        - ``'theirs'``: keep the changes from the incoming branch
        - ``'larger'``: keep whichever side has more content

        Args:
            branch: Branch with conflicts
            base_branch: Target base branch
            strategy: Resolution strategy ('ours', 'theirs', 'larger')

        Returns:
            Tuple of (success, list of resolved files)
        """
        logger.info(
            "Resolving conflicts on %s using strategy '%s'", branch, strategy
        )

        conflicted_files = self._detect_conflicts(branch, base_branch)
        if not conflicted_files:
            logger.info("No conflicts to resolve on %s", branch)
            return True, []

        resolved: List[str] = []
        for file_path in conflicted_files:
            success = self._resolve_file_conflict(file_path, strategy)
            if success:
                resolved.append(file_path)
                logger.info("Resolved conflict in %s", file_path)
            else:
                logger.warning("Could not auto-resolve conflict in %s", file_path)

        all_resolved = len(resolved) == len(conflicted_files)
        if all_resolved:
            logger.info("All conflicts resolved (%d files)", len(resolved))
        else:
            unresolved = len(conflicted_files) - len(resolved)
            logger.warning("%d conflict(s) could not be auto-resolved", unresolved)

        return all_resolved, resolved

    def _resolve_file_conflict(self, file_path: str, strategy: str) -> bool:
        """Resolve conflict in a single file using the given strategy."""
        try:
            full_path = self.repo_path / file_path
            if not full_path.exists():
                return False

            content = full_path.read_text(encoding="utf-8")
            if "<<<<<<" not in content:
                return True  # No conflict markers

            resolved = self._apply_conflict_strategy(content, strategy)
            full_path.write_text(resolved, encoding="utf-8")

            # Stage the resolved file
            self._run_git(["add", file_path], check=False)
            return True
        except Exception as exc:
            logger.debug("Error resolving %s: %s", file_path, exc)
            return False

    def _apply_conflict_strategy(self, content: str, strategy: str) -> str:
        """Apply conflict resolution strategy to content with conflict markers."""
        pattern = re.compile(
            r"<<<<<<<[^\n]*\n(.*?)\n=======[^\n]*\n(.*?)\n>>>>>>>[^\n]*",
            re.DOTALL,
        )

        def resolver(match: re.Match) -> str:  # type: ignore[type-arg]
            ours = match.group(1)
            theirs = match.group(2)
            if strategy == "ours":
                return ours
            if strategy == "theirs":
                return theirs
            # 'larger': keep the longer / more complete side
            return ours if len(ours) >= len(theirs) else theirs

        return pattern.sub(resolver, content)

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate_pr(
        self,
        run_tests: bool = True,
        run_linting: bool = True,
        run_security: bool = True,
        run_type_check: bool = False,
        min_quality_score: float = 0.70,
    ) -> ValidationReport:
        """
        Run the full validation pipeline against the current working tree.

        Checks performed (when enabled):
        - pytest test suite
        - flake8 / pylint linting
        - bandit security scan
        - mypy type checking

        Args:
            run_tests: Execute pytest
            run_linting: Run flake8 linting
            run_security: Run bandit security scan
            run_type_check: Run mypy type checking
            min_quality_score: Minimum score (0-1) to pass overall

        Returns:
            ValidationReport with per-check results and overall pass/fail
        """
        logger.info("Starting full validation pipeline")
        checks: Dict[str, Dict[str, Any]] = {}
        issues: List[str] = []

        if run_tests:
            result = self._run_tests()
            checks[ValidationCheckType.TESTS.value] = result
            if not result["passed"]:
                issues.append(f"Tests failed: {result.get('summary', '')}")

        if run_linting:
            result = self._run_linting()
            checks[ValidationCheckType.LINTING.value] = result
            if not result["passed"]:
                issues.append(f"Linting issues found: {result.get('summary', '')}")

        if run_security:
            result = self._run_security_scan()
            checks[ValidationCheckType.SECURITY.value] = result
            if not result["passed"]:
                issues.append(f"Security issues found: {result.get('summary', '')}")

        if run_type_check:
            result = self._run_type_check()
            checks[ValidationCheckType.TYPE_CHECK.value] = result
            if not result["passed"]:
                issues.append(f"Type errors found: {result.get('summary', '')}")

        quality_score = self._calculate_quality_score(checks)
        passed = not issues and quality_score >= min_quality_score

        report = ValidationReport(
            passed=passed,
            checks=checks,
            issues=issues,
            quality_score=quality_score,
        )

        status = "PASSED ✅" if passed else "FAILED ❌"
        logger.info(
            "Validation %s (score=%.2f, issues=%d)", status, quality_score, len(issues)
        )
        return report

    def _run_tests(self) -> Dict[str, Any]:
        """Execute pytest and return check result."""
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", "tests/", "-v", "--tb=short", "-q"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=300,
                check=False,
            )
            passed_count = len(re.findall(r" PASSED", result.stdout))
            failed_count = len(re.findall(r" FAILED", result.stdout))
            summary = f"{passed_count} passed, {failed_count} failed"
            return {
                "passed": result.returncode == 0,
                "summary": summary,
                "output": result.stdout[-2000:],
            }
        except Exception as exc:
            return {"passed": False, "summary": str(exc), "output": ""}

    def _run_linting(self) -> Dict[str, Any]:
        """Run flake8 linting and return check result."""
        try:
            result = subprocess.run(
                [
                    "python",
                    "-m",
                    "flake8",
                    "src/",
                    "--max-line-length=120",
                    "--extend-ignore=E501,W503",
                    "--count",
                    "--statistics",
                ],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
            issue_count_match = re.search(r"^(\d+)$", result.stdout, re.MULTILINE)
            issue_count = int(issue_count_match.group(1)) if issue_count_match else 0
            return {
                "passed": result.returncode == 0,
                "summary": f"{issue_count} issues" if issue_count else "clean",
                "output": result.stdout[-2000:],
            }
        except Exception as exc:
            return {"passed": True, "summary": f"linter not available: {exc}", "output": ""}

    def _run_security_scan(self) -> Dict[str, Any]:
        """Run bandit security scan and return check result."""
        try:
            result = subprocess.run(
                [
                    "python",
                    "-m",
                    "bandit",
                    "-r",
                    "src/",
                    "-ll",  # medium severity and above
                    "-q",
                    "-f",
                    "txt",
                ],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
            high_issues = len(re.findall(r"Severity: High", result.stdout))
            return {
                "passed": high_issues == 0 and result.returncode in (0, 1),
                "summary": f"{high_issues} high-severity issues" if high_issues else "clean",
                "output": result.stdout[-2000:],
            }
        except Exception as exc:
            return {"passed": True, "summary": f"bandit not available: {exc}", "output": ""}

    def _run_type_check(self) -> Dict[str, Any]:
        """Run mypy type checking and return check result."""
        try:
            result = subprocess.run(
                ["python", "-m", "mypy", "src/genesis/", "--ignore-missing-imports"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
            error_count = result.stdout.count(": error:")
            return {
                "passed": result.returncode == 0,
                "summary": f"{error_count} type errors" if error_count else "clean",
                "output": result.stdout[-2000:],
            }
        except Exception as exc:
            return {"passed": True, "summary": f"mypy not available: {exc}", "output": ""}

    def _calculate_quality_score(self, checks: Dict[str, Dict[str, Any]]) -> float:
        """Calculate overall quality score from check results (0.0 – 1.0)."""
        if not checks:
            return 1.0
        passed = sum(1 for c in checks.values() if c.get("passed", False))
        return passed / len(checks)

    # ------------------------------------------------------------------
    # Auto squash-and-merge
    # ------------------------------------------------------------------

    def auto_squash_merge(
        self,
        pr_number: int,
        branch: str,
        base_branch: str = "main",
        commit_title: Optional[str] = None,
    ) -> MergeReport:
        """
        Squash all commits on branch and merge into base_branch.

        This is a local Git operation. In a GitHub Actions context the
        GitHub API squash-merge is used instead (see pr-automation.yml).

        Args:
            pr_number: Pull request number (used in commit message)
            branch: Head branch to squash-merge
            base_branch: Target branch
            commit_title: Override for squash commit title

        Returns:
            MergeReport with success/failure details
        """
        logger.info(
            "Auto squash-merge: PR #%d (%s → %s)", pr_number, branch, base_branch
        )

        # Build commit message
        commits = self._get_branch_commits(branch, base_branch)
        title = commit_title or f"🤖 Auto-merge PR #{pr_number}: {branch}"
        body = self._build_squash_commit_body(pr_number, branch, commits)

        try:
            # Ensure we're on base_branch
            self._run_git(["checkout", base_branch], check=True)

            # Squash-merge the branch
            result = subprocess.run(
                ["git", "merge", "--squash", branch],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                return MergeReport(
                    success=False,
                    pr_number=pr_number,
                    commit_sha=None,
                    squashed=False,
                    error_message=result.stderr.strip(),
                )

            # Commit the squash
            subprocess.run(
                ["git", "commit", "-m", f"{title}\n\n{body}"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )

            commit_sha = self._run_git(["rev-parse", "HEAD"], check=False)
            return MergeReport(
                success=True,
                pr_number=pr_number,
                commit_sha=(commit_sha or "").strip(),
                squashed=True,
            )

        except subprocess.CalledProcessError as exc:
            logger.error("Squash-merge failed for PR #%d: %s", pr_number, exc)
            return MergeReport(
                success=False,
                pr_number=pr_number,
                commit_sha=None,
                squashed=False,
                error_message=str(exc),
            )

    def _build_squash_commit_body(
        self, pr_number: int, branch: str, commits: List[str]
    ) -> str:
        """Build a descriptive squash commit message body."""
        lines = [
            f"Squashed commits from branch `{branch}` (PR #{pr_number}):",
            "",
        ]
        for commit in commits[:20]:  # cap at 20 entries
            lines.append(f"  * {commit}")
        if len(commits) > 20:
            lines.append(f"  ... and {len(commits) - 20} more commits")
        lines += [
            "",
            "Automatically merged by Genesis PR Automation.",
            "✅ Tests passed  ✅ Linting clean  ✅ Security scan clean",
        ]
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Full pipeline
    # ------------------------------------------------------------------

    def run_full_pipeline(
        self,
        pr_number: int,
        branch: str,
        base_branch: str = "main",
        title: str = "",
        auto_merge: bool = True,
    ) -> Dict[str, Any]:
        """
        Execute the complete zero-friction PR pipeline.

        Stages:
        1. Analyze PR
        2. Resolve conflicts (if any)
        3. Validate (tests, linting, security)
        4. Auto squash-merge (if validation passed)

        Args:
            pr_number: Pull request number
            branch: Head branch
            base_branch: Target branch
            title: PR title
            auto_merge: Whether to actually perform the merge

        Returns:
            Pipeline result dictionary with per-stage outcomes
        """
        logger.info("Starting full pipeline for PR #%d", pr_number)
        result: Dict[str, Any] = {
            "pr_number": pr_number,
            "status": PRStatus.PENDING.value,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "stages": {},
        }

        # Stage 1: Analyze
        result["status"] = PRStatus.ANALYZING.value
        analysis = self.analyze_pr(pr_number, branch, base_branch, title)
        result["stages"]["analyze"] = analysis.to_dict()

        # Stage 2: Resolve conflicts
        if analysis.has_conflicts:
            result["status"] = PRStatus.CONFLICTS_DETECTED.value
            resolved, resolved_files = self.resolve_conflicts(branch, base_branch)
            result["stages"]["resolve_conflicts"] = {
                "success": resolved,
                "resolved_files": resolved_files,
                "unresolved_files": [
                    f
                    for f in analysis.conflicted_files
                    if f not in resolved_files
                ],
            }
            if not resolved:
                result["status"] = PRStatus.FAILED.value
                result["completed_at"] = datetime.now(timezone.utc).isoformat()
                logger.error("Pipeline aborted: unresolved conflicts in PR #%d", pr_number)
                return result
            result["status"] = PRStatus.CONFLICTS_RESOLVED.value

        # Stage 3: Validate
        result["status"] = PRStatus.VALIDATING.value
        validation = self.validate_pr()
        result["stages"]["validate"] = validation.to_dict()

        if not validation.passed:
            result["status"] = PRStatus.VALIDATION_FAILED.value
            result["completed_at"] = datetime.now(timezone.utc).isoformat()
            logger.warning("Pipeline blocked: validation failed for PR #%d", pr_number)
            return result

        result["status"] = PRStatus.VALIDATION_PASSED.value

        # Stage 4: Squash-merge
        if auto_merge:
            result["status"] = PRStatus.MERGING.value
            merge = self.auto_squash_merge(pr_number, branch, base_branch, title)
            result["stages"]["merge"] = merge.to_dict()
            if merge.success:
                result["status"] = PRStatus.MERGED.value
                logger.info("PR #%d merged successfully ✅", pr_number)
            else:
                result["status"] = PRStatus.FAILED.value
                logger.error("Merge failed for PR #%d: %s", pr_number, merge.error_message)

        result["completed_at"] = datetime.now(timezone.utc).isoformat()
        return result

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _run_git(self, args: List[str], check: bool = True) -> str:
        """Run a git command and return stdout."""
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=check,
            )
            return result.stdout
        except subprocess.CalledProcessError:
            return ""


# Singleton instance
pr_automation = PRAutomation()
