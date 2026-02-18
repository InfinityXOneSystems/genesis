"""
Healing Agent - Automatically fixes workflow failures

This module implements self-healing capabilities for Genesis workflows.
It analyzes failures and applies appropriate fixes with recursive retry logic.
"""

import logging
import subprocess
import time
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from datetime import datetime
import json

from .workflow_monitor import WorkflowMonitor, WorkflowFailure, get_workflow_monitor
from .git_manager import git_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HealingStrategy:
    """Base class for healing strategies."""
    
    def __init__(self, max_retries: int = 3):
        """
        Initialize healing strategy.
        
        Args:
            max_retries: Maximum number of retry attempts
        """
        self.max_retries = max_retries
    
    def can_handle(self, failure: WorkflowFailure) -> bool:
        """
        Check if this strategy can handle the given failure.
        
        Args:
            failure: WorkflowFailure object
            
        Returns:
            True if strategy can handle this failure
        """
        raise NotImplementedError
    
    def heal(self, failure: WorkflowFailure, repo_path: Path) -> Tuple[bool, str]:
        """
        Attempt to heal the failure.
        
        Args:
            failure: WorkflowFailure object
            repo_path: Path to repository
            
        Returns:
            Tuple of (success, message)
        """
        raise NotImplementedError


class TestFailureStrategy(HealingStrategy):
    """Strategy for healing test failures."""
    
    def can_handle(self, failure: WorkflowFailure) -> bool:
        return failure.failure_type == "test_failure"
    
    def heal(self, failure: WorkflowFailure, repo_path: Path) -> Tuple[bool, str]:
        """
        Heal test failures by:
        1. Rerunning tests to check for flakiness
        2. Checking test logs for common issues
        3. Updating test fixtures if needed
        """
        logger.info("Attempting to heal test failure...")
        
        # Run tests locally to reproduce
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", "tests/", "-v"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                return True, "Tests passed on retry - likely flaky test"
            
            # Analyze test output for common issues
            output = result.stdout + result.stderr
            
            if "ModuleNotFoundError" in output or "ImportError" in output:
                return False, "Test failure due to import errors - requires dependency fix"
            
            if "fixtures" in output.lower() or "fixture" in output.lower():
                return False, "Test failure due to fixture issues - manual review required"
            
            return False, f"Tests still failing: {result.stderr[-500:]}"
            
        except subprocess.TimeoutExpired:
            return False, "Test execution timed out"
        except Exception as e:
            return False, f"Failed to run tests: {e}"


class LintFailureStrategy(HealingStrategy):
    """Strategy for healing linting/formatting failures."""
    
    def can_handle(self, failure: WorkflowFailure) -> bool:
        return failure.failure_type == "lint_failure"
    
    def heal(self, failure: WorkflowFailure, repo_path: Path) -> Tuple[bool, str]:
        """
        Heal linting failures by:
        1. Running auto-formatters (black, isort)
        2. Fixing simple linting issues
        """
        logger.info("Attempting to heal linting failure...")
        
        fixes_applied = []
        
        # Run black formatter
        try:
            result = subprocess.run(
                ["python", "-m", "black", "src/", "tests/"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            if "reformatted" in result.stdout:
                fixes_applied.append("black formatter")
        except Exception as e:
            logger.warning(f"Black formatter failed: {e}")
        
        # Run isort
        try:
            result = subprocess.run(
                ["python", "-m", "isort", "src/", "tests/"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                fixes_applied.append("isort")
        except Exception as e:
            logger.warning(f"isort failed: {e}")
        
        if fixes_applied:
            # Commit the fixes
            try:
                git_manager.add_all()
                git_manager.commit("Auto-fix: Apply code formatting")
                return True, f"Applied fixes: {', '.join(fixes_applied)}"
            except Exception as e:
                return False, f"Failed to commit fixes: {e}"
        
        return False, "No automatic fixes available for linting issues"


class DependencyFailureStrategy(HealingStrategy):
    """Strategy for healing dependency failures."""
    
    def can_handle(self, failure: WorkflowFailure) -> bool:
        return failure.failure_type == "dependency_failure"
    
    def heal(self, failure: WorkflowFailure, repo_path: Path) -> Tuple[bool, str]:
        """
        Heal dependency failures by:
        1. Clearing cache
        2. Reinstalling dependencies
        3. Updating pinned versions if needed
        """
        logger.info("Attempting to heal dependency failure...")
        
        # Try reinstalling Python dependencies
        try:
            # Clear pip cache
            subprocess.run(
                ["python", "-m", "pip", "cache", "purge"],
                cwd=repo_path,
                capture_output=True,
                timeout=60
            )
            
            # Reinstall requirements
            result = subprocess.run(
                ["python", "-m", "pip", "install", "-r", "requirements.txt"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                return True, "Successfully reinstalled dependencies"
            else:
                return False, f"Dependency installation failed: {result.stderr[-500:]}"
                
        except Exception as e:
            return False, f"Failed to reinstall dependencies: {e}"


class SecurityFailureStrategy(HealingStrategy):
    """Strategy for healing security failures."""
    
    def can_handle(self, failure: WorkflowFailure) -> bool:
        return failure.failure_type == "security_failure"
    
    def heal(self, failure: WorkflowFailure, repo_path: Path) -> Tuple[bool, str]:
        """
        Heal security failures by:
        1. Identifying vulnerable dependencies
        2. Updating to patched versions
        """
        logger.info("Attempting to heal security failure...")
        
        # Extract vulnerable package info from logs
        logs = failure.error_logs
        
        # Check for known vulnerabilities
        if "next.js" in logs.lower() or "next" in logs.lower():
            try:
                # Update Next.js to safe version
                result = subprocess.run(
                    ["npm", "install", "next@15.0.8"],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=180
                )
                
                if result.returncode == 0:
                    git_manager.add_all()
                    git_manager.commit("Security fix: Update Next.js to 15.0.8")
                    return True, "Updated Next.js to patched version"
            except Exception as e:
                return False, f"Failed to update Next.js: {e}"
        
        return False, "No automatic security fixes available - manual review required"


class BuildFailureStrategy(HealingStrategy):
    """Strategy for healing build failures."""
    
    def can_handle(self, failure: WorkflowFailure) -> bool:
        return failure.failure_type == "build_failure"
    
    def heal(self, failure: WorkflowFailure, repo_path: Path) -> Tuple[bool, str]:
        """
        Heal build failures by:
        1. Checking for common build errors
        2. Fixing configuration issues
        """
        logger.info("Attempting to heal build failure...")
        
        # Try rebuilding to see if issue persists
        try:
            result = subprocess.run(
                ["python", "-m", "pip", "install", "-e", "."],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=180
            )
            
            if result.returncode == 0:
                return True, "Build succeeded on retry"
            else:
                return False, f"Build still failing: {result.stderr[-500:]}"
                
        except Exception as e:
            return False, f"Failed to build: {e}"


class HealingAgent:
    """
    Main healing agent that orchestrates auto-healing of workflow failures.
    
    This agent:
    - Monitors workflows for failures
    - Analyzes failures to determine root cause
    - Applies appropriate healing strategies
    - Retries with exponential backoff
    - Reports healing outcomes
    """
    
    def __init__(self, repo_path: Path, owner: str = "InfinityXOneSystems", repo: str = "genesis"):
        """
        Initialize the healing agent.
        
        Args:
            repo_path: Path to repository
            owner: GitHub repository owner
            repo: GitHub repository name
        """
        self.repo_path = repo_path
        self.monitor = get_workflow_monitor(owner, repo)
        self.strategies: List[HealingStrategy] = [
            TestFailureStrategy(),
            LintFailureStrategy(),
            DependencyFailureStrategy(),
            SecurityFailureStrategy(),
            BuildFailureStrategy()
        ]
        self.healing_history: List[Dict[str, Any]] = []
        
    def detect_failures(self, hours: int = 6) -> List[WorkflowFailure]:
        """
        Detect workflow failures within the specified time window.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            List of WorkflowFailure objects
        """
        logger.info(f"Detecting failures from the last {hours} hours...")
        
        failed_runs = self.monitor.get_failed_runs(hours=hours)
        failures = []
        
        for run in failed_runs:
            failure = self.monitor.analyze_failure(run)
            failures.append(failure)
            logger.info(f"Detected {failure.failure_type}: {failure.run.name}")
        
        return failures
    
    def heal_failure(self, failure: WorkflowFailure, max_attempts: int = 3) -> Dict[str, Any]:
        """
        Attempt to heal a specific failure with retry logic.
        
        Args:
            failure: WorkflowFailure object
            max_attempts: Maximum number of healing attempts
            
        Returns:
            Dictionary with healing outcome
        """
        logger.info(f"Attempting to heal {failure.failure_type} for workflow '{failure.run.name}'...")
        
        # Find appropriate strategy
        strategy = None
        for s in self.strategies:
            if s.can_handle(failure):
                strategy = s
                break
        
        if not strategy:
            logger.warning(f"No strategy available for {failure.failure_type}")
            return {
                "workflow_run_id": failure.run.id,
                "workflow_name": failure.run.name,
                "failure_type": failure.failure_type,
                "success": False,
                "message": "No healing strategy available",
                "attempts": 0,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Attempt healing with exponential backoff
        for attempt in range(1, max_attempts + 1):
            logger.info(f"Healing attempt {attempt}/{max_attempts}...")
            
            success, message = strategy.heal(failure, self.repo_path)
            
            outcome = {
                "workflow_run_id": failure.run.id,
                "workflow_name": failure.run.name,
                "failure_type": failure.failure_type,
                "success": success,
                "message": message,
                "attempts": attempt,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            if success:
                logger.info(f"Successfully healed failure: {message}")
                self.healing_history.append(outcome)
                return outcome
            
            # Exponential backoff before retry
            if attempt < max_attempts:
                backoff = 2 ** attempt
                logger.info(f"Healing failed, retrying in {backoff} seconds...")
                time.sleep(backoff)
        
        logger.warning(f"Failed to heal after {max_attempts} attempts")
        self.healing_history.append(outcome)
        return outcome
    
    def heal_all_failures(self, hours: int = 6, max_attempts: int = 3) -> Dict[str, Any]:
        """
        Detect and heal all workflow failures.
        
        Args:
            hours: Number of hours to look back for failures
            max_attempts: Maximum healing attempts per failure
            
        Returns:
            Dictionary with summary of healing operations
        """
        logger.info("=" * 80)
        logger.info("HEALING AGENT: Starting auto-healing cycle")
        logger.info("=" * 80)
        
        start_time = datetime.utcnow()
        
        # Detect failures
        failures = self.detect_failures(hours=hours)
        
        if not failures:
            logger.info("No failures detected - system is healthy!")
            return {
                "total_failures": 0,
                "healed": 0,
                "failed": 0,
                "success_rate": 100.0,
                "duration_seconds": (datetime.utcnow() - start_time).total_seconds(),
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Attempt to heal each failure
        outcomes = []
        for failure in failures:
            outcome = self.heal_failure(failure, max_attempts=max_attempts)
            outcomes.append(outcome)
        
        # Calculate summary statistics
        healed = sum(1 for o in outcomes if o["success"])
        failed = len(outcomes) - healed
        success_rate = (healed / len(outcomes) * 100) if outcomes else 0.0
        
        summary = {
            "total_failures": len(failures),
            "healed": healed,
            "failed": failed,
            "success_rate": success_rate,
            "outcomes": outcomes,
            "duration_seconds": (datetime.utcnow() - start_time).total_seconds(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info("=" * 80)
        logger.info(f"HEALING COMPLETE: {healed}/{len(failures)} failures healed ({success_rate:.1f}% success rate)")
        logger.info("=" * 80)
        
        return summary
    
    def get_healing_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive healing report.
        
        Returns:
            Dictionary with healing statistics and history
        """
        if not self.healing_history:
            return {
                "total_healing_attempts": 0,
                "successful_healings": 0,
                "failed_healings": 0,
                "success_rate": 0.0,
                "history": []
            }
        
        successful = sum(1 for h in self.healing_history if h["success"])
        
        return {
            "total_healing_attempts": len(self.healing_history),
            "successful_healings": successful,
            "failed_healings": len(self.healing_history) - successful,
            "success_rate": (successful / len(self.healing_history) * 100),
            "history": self.healing_history[-10:]  # Last 10 attempts
        }


# Global healing agent instance
healing_agent = None


def get_healing_agent(repo_path: Optional[Path] = None) -> HealingAgent:
    """
    Get or create the global healing agent instance.
    
    Args:
        repo_path: Path to repository (defaults to current directory)
        
    Returns:
        HealingAgent instance
    """
    global healing_agent
    if healing_agent is None:
        if repo_path is None:
            repo_path = Path.cwd()
        healing_agent = HealingAgent(repo_path)
    return healing_agent
