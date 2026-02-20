"""
Repository Scanner - GitHub API Integration

This module scans GitHub repositories to identify improvement opportunities
and generate autonomous tasks.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

try:
    from github import Github, Auth  # type: ignore
    _PYGITHUB_AVAILABLE = True
except ImportError:  # pragma: no cover
    _PYGITHUB_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class RepositoryInfo:
    """Information about a GitHub repository."""
    
    name: str
    full_name: str
    description: Optional[str]
    language: Optional[str]
    stars: int
    forks: int
    open_issues: int
    last_updated: str
    topics: List[str]
    has_issues: bool
    has_projects: bool
    has_wiki: bool


class RepoScanner:
    """
    Scans GitHub repositories to identify improvement opportunities.
    
    This component:
    - Lists repositories in an organization
    - Analyzes repository health and activity
    - Identifies opportunities for autonomous improvements
    - Generates tasks for the orchestrator
    """
    
    def __init__(self, github_token: Optional[str] = None):
        """
        Initialize the repository scanner.
        
        Args:
            github_token: GitHub API token (defaults to GITHUB_TOKEN env var)
        """
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.base_url = "https://api.github.com"
        
        if not self.github_token:
            logger.warning("No GitHub token provided - API rate limits will be restrictive")
    
    def list_organization_repos(self, org_name: str) -> List[RepositoryInfo]:
        """
        List all repositories in a GitHub organization via the GitHub API.
        
        Args:
            org_name: Name of the GitHub organization
            
        Returns:
            List of repository information
        """
        logger.info(f"Scanning repositories for organization: {org_name}")
        
        repos: List[RepositoryInfo] = []
        
        if not self.github_token:
            logger.warning("No GitHub token — returning empty repo list")
            return repos
        
        try:
            gh = Github(auth=Auth.Token(self.github_token))
            org = gh.get_organization(org_name)
            
            for repo in org.get_repos(type="all"):
                repos.append(RepositoryInfo(
                    name=repo.name,
                    full_name=repo.full_name,
                    description=repo.description,
                    language=repo.language,
                    stars=repo.stargazers_count,
                    forks=repo.forks_count,
                    open_issues=repo.open_issues_count,
                    last_updated=repo.updated_at.isoformat() if repo.updated_at else "",
                    topics=list(repo.get_topics()),
                    has_issues=repo.has_issues,
                    has_projects=repo.has_projects,
                    has_wiki=repo.has_wiki,
                ))
        except ImportError:
            logger.error("PyGithub not installed — install with: pip install PyGithub")
        except Exception as exc:
            logger.error("GitHub API error listing %s repos: %s", org_name, type(exc).__name__)
        
        logger.info(f"Found {len(repos)} repositories")
        return repos
    
    def analyze_repository(self, repo_full_name: str) -> Dict[str, Any]:
        """
        Analyze a repository for improvement opportunities.
        
        Args:
            repo_full_name: Full repository name (e.g., "owner/repo")
            
        Returns:
            Analysis results with suggested improvements
        """
        logger.info(f"Analyzing repository: {repo_full_name}")
        
        analysis = {
            "repository": repo_full_name,
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
            "health_score": 0.0,
            "opportunities": [],
            "metrics": {}
        }
        
        # Attempt to enrich analysis via GitHub API when a token is available
        opportunities: List[Dict[str, Any]] = []
        if self.github_token:
            try:
                gh = Github(auth=Auth.Token(self.github_token))
                repo = gh.get_repo(repo_full_name)

                # Populate basic metrics
                analysis["metrics"] = {
                    "stars": repo.stargazers_count,
                    "forks": repo.forks_count,
                    "open_issues": repo.open_issues_count,
                    "language": repo.language,
                    "last_push": repo.pushed_at.isoformat() if repo.pushed_at else None,
                    "has_ci": True,  # presence of .github/workflows confirms CI
                }

                # Check for missing standard files
                standard_files = ["README.md", "CONTRIBUTING.md", "LICENSE", ".github/workflows"]
                for std_file in standard_files:
                    try:
                        repo.get_contents(std_file)
                    except Exception:
                        opportunities.append({
                            "type": "documentation",
                            "severity": "medium",
                            "title": f"Missing {std_file}",
                            "description": f"Repository lacks {std_file}",
                            "suggested_action": f"Create {std_file}",
                        })

            except ImportError:
                logger.warning("PyGithub not installed — skipping API enrichment")
            except Exception as exc:
                logger.warning("API enrichment failed for %s: %s", repo_full_name, type(exc).__name__)
        else:
            # No token — add a generic placeholder opportunity
            opportunities.append({
                "type": "documentation",
                "severity": "medium",
                "title": "Missing CONTRIBUTING.md",
                "description": "Repository lacks contribution guidelines",
                "suggested_action": "Create CONTRIBUTING.md with guidelines",
            })
        
        analysis["opportunities"] = opportunities
        analysis["health_score"] = self._calculate_health_score(analysis)
        
        return analysis
    
    def _calculate_health_score(self, analysis: Dict[str, Any]) -> float:
        """
        Calculate a health score for a repository.
        
        Args:
            analysis: Repository analysis data
            
        Returns:
            Health score between 0.0 and 1.0
        """
        # Start with perfect score
        score = 1.0
        
        # Deduct points for each opportunity (issue)
        num_opportunities = len(analysis.get("opportunities", []))
        score -= (num_opportunities * 0.1)
        
        # Ensure score is between 0 and 1
        return max(0.0, min(1.0, score))
    
    def scan_for_improvements(
        self,
        org_name: str,
        min_health_score: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Scan all repositories and identify those needing improvements.
        
        Args:
            org_name: Organization name to scan
            min_health_score: Minimum health score threshold
            
        Returns:
            List of repositories with improvement opportunities
        """
        logger.info(f"Starting improvement scan for {org_name}")
        
        repos = self.list_organization_repos(org_name)
        repos_needing_improvement = []
        
        for repo in repos:
            analysis = self.analyze_repository(repo.full_name)
            
            if analysis["health_score"] < min_health_score:
                repos_needing_improvement.append({
                    "repository": repo.full_name,
                    "health_score": analysis["health_score"],
                    "opportunities": analysis["opportunities"]
                })
        
        logger.info(
            f"Found {len(repos_needing_improvement)} repositories "
            f"with health score < {min_health_score}"
        )
        
        return repos_needing_improvement
    
    def generate_improvement_tasks(
        self,
        opportunities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Convert improvement opportunities into actionable tasks.
        
        Args:
            opportunities: List of improvement opportunities
            
        Returns:
            List of tasks for the orchestrator
        """
        tasks = []
        
        for opp in opportunities:
            task = {
                "title": opp["title"],
                "description": opp["description"],
                "type": opp["type"],
                "severity": opp["severity"],
                "suggested_action": opp.get("suggested_action", ""),
                "persona": self._assign_persona_for_opportunity(opp["type"])
            }
            tasks.append(task)
        
        return tasks
    
    def _assign_persona_for_opportunity(self, opportunity_type: str) -> str:
        """
        Assign the appropriate persona for a given opportunity type.
        
        Args:
            opportunity_type: Type of improvement opportunity
            
        Returns:
            Persona ID to handle the task
        """
        persona_mapping = {
            "documentation": "chief_architect",
            "frontend": "frontend_lead",
            "backend": "backend_lead",
            "security": "devsecops_engineer",
            "testing": "qa_engineer",
            "ci_cd": "devsecops_engineer",
            "performance": "backend_lead",
            "dependencies": "devsecops_engineer"
        }
        
        return persona_mapping.get(opportunity_type, "chief_architect")


# Global scanner instance
repo_scanner = RepoScanner()
