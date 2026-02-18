"""Repository Scanner - Analyzes repositories and generates global analysis"""

import os
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict
from genesis.utils import setup_logging, save_json_report


@dataclass
class RepositoryInfo:
    """Information about a repository"""
    name: str
    path: str
    language: str
    files_count: int
    lines_of_code: int
    has_tests: bool
    has_ci: bool
    has_docs: bool
    dependencies: List[str]


class RepositoryScanner:
    """Scans and analyzes repositories"""
    
    def __init__(self):
        self.logger = setup_logging()
    
    def scan_repository(self, repo_path: str) -> RepositoryInfo:
        """Scan a single repository"""
        self.logger.info(f"Scanning repository: {repo_path}")
        
        path = Path(repo_path)
        
        # Detect primary language
        language = self._detect_language(path)
        
        # Count files and LOC
        files_count, lines_of_code = self._count_files_and_lines(path)
        
        # Check for tests, CI, docs
        has_tests = self._has_tests(path)
        has_ci = self._has_ci(path)
        has_docs = self._has_docs(path)
        
        # Extract dependencies
        dependencies = self._extract_dependencies(path, language)
        
        return RepositoryInfo(
            name=path.name,
            path=str(path),
            language=language,
            files_count=files_count,
            lines_of_code=lines_of_code,
            has_tests=has_tests,
            has_ci=has_ci,
            has_docs=has_docs,
            dependencies=dependencies,
        )
    
    def generate_global_analysis(
        self,
        repositories: List[RepositoryInfo],
        output_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """Generate global analysis report"""
        self.logger.info("Generating global analysis report")
        
        # Aggregate statistics
        total_files = sum(r.files_count for r in repositories)
        total_loc = sum(r.lines_of_code for r in repositories)
        
        languages = {}
        for repo in repositories:
            lang = repo.language
            languages[lang] = languages.get(lang, 0) + 1
        
        # Build dependency graph
        dependency_graph = self._build_dependency_graph(repositories)
        
        # Identify anti-patterns
        anti_patterns = self._identify_anti_patterns(repositories)
        
        # Generate refactor opportunities
        refactor_opportunities = self._identify_refactor_opportunities(repositories)
        
        analysis = {
            "summary": {
                "total_repositories": len(repositories),
                "total_files": total_files,
                "total_lines_of_code": total_loc,
                "languages": languages,
                "repositories_with_tests": sum(1 for r in repositories if r.has_tests),
                "repositories_with_ci": sum(1 for r in repositories if r.has_ci),
                "repositories_with_docs": sum(1 for r in repositories if r.has_docs),
            },
            "repositories": [asdict(r) for r in repositories],
            "dependency_graph": dependency_graph,
            "anti_patterns": anti_patterns,
            "refactor_opportunities": refactor_opportunities,
            "tech_stack": self._analyze_tech_stack(repositories),
        }
        
        # Save report
        if output_path:
            save_json_report(analysis, output_path)
        
        return analysis
    
    def _detect_language(self, path: Path) -> str:
        """Detect primary programming language"""
        extensions = {
            ".py": "Python",
            ".js": "JavaScript",
            ".ts": "TypeScript",
            ".go": "Go",
            ".java": "Java",
            ".rs": "Rust",
            ".cpp": "C++",
            ".c": "C",
        }
        
        counts = {}
        for ext, lang in extensions.items():
            count = len(list(path.rglob(f"*{ext}")))
            if count > 0:
                counts[lang] = count
        
        if counts:
            return max(counts, key=counts.get)
        return "Unknown"
    
    def _count_files_and_lines(self, path: Path) -> tuple[int, int]:
        """Count files and lines of code"""
        files = 0
        lines = 0
        
        excluded_dirs = {".git", "node_modules", "venv", "__pycache__", ".next", "dist", "build"}
        
        for file_path in path.rglob("*"):
            # Skip excluded directories
            if any(excluded in file_path.parts for excluded in excluded_dirs):
                continue
            
            if file_path.is_file():
                files += 1
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines += len(f.readlines())
                except:
                    pass
        
        return files, lines
    
    def _has_tests(self, path: Path) -> bool:
        """Check if repository has tests"""
        test_indicators = ["test", "tests", "spec", "__tests__"]
        
        for indicator in test_indicators:
            if list(path.rglob(f"*{indicator}*")):
                return True
        
        return False
    
    def _has_ci(self, path: Path) -> bool:
        """Check if repository has CI/CD"""
        ci_files = [
            ".github/workflows",
            ".gitlab-ci.yml",
            ".travis.yml",
            "Jenkinsfile",
            ".circleci",
        ]
        
        for ci_file in ci_files:
            if (path / ci_file).exists():
                return True
        
        return False
    
    def _has_docs(self, path: Path) -> bool:
        """Check if repository has documentation"""
        doc_indicators = ["README.md", "docs", "documentation"]
        
        for indicator in doc_indicators:
            if (path / indicator).exists():
                return True
        
        return False
    
    def _extract_dependencies(self, path: Path, language: str) -> List[str]:
        """Extract dependencies based on language"""
        dependencies = []
        
        if language == "Python":
            # Check for requirements.txt, pyproject.toml
            req_file = path / "requirements.txt"
            if req_file.exists():
                with open(req_file, 'r') as f:
                    dependencies = [line.strip().split('==')[0] for line in f if line.strip()]
        
        elif language == "JavaScript" or language == "TypeScript":
            # Check for package.json
            pkg_file = path / "package.json"
            if pkg_file.exists():
                with open(pkg_file, 'r') as f:
                    pkg = json.load(f)
                    dependencies = list(pkg.get("dependencies", {}).keys())
        
        return dependencies
    
    def _build_dependency_graph(self, repositories: List[RepositoryInfo]) -> Dict[str, List[str]]:
        """Build dependency graph across repositories"""
        graph = {}
        
        for repo in repositories:
            graph[repo.name] = repo.dependencies[:5]  # Top 5 deps
        
        return graph
    
    def _identify_anti_patterns(self, repositories: List[RepositoryInfo]) -> List[Dict[str, Any]]:
        """Identify anti-patterns"""
        patterns = []
        
        for repo in repositories:
            if not repo.has_tests:
                patterns.append({
                    "repository": repo.name,
                    "pattern": "no_tests",
                    "severity": "high",
                    "description": "Repository lacks test coverage",
                })
            
            if not repo.has_ci:
                patterns.append({
                    "repository": repo.name,
                    "pattern": "no_ci_cd",
                    "severity": "medium",
                    "description": "No CI/CD pipeline configured",
                })
        
        return patterns
    
    def _identify_refactor_opportunities(
        self, repositories: List[RepositoryInfo]
    ) -> List[Dict[str, Any]]:
        """Identify refactoring opportunities"""
        opportunities = []
        
        # Check for potential monorepo consolidation
        if len(repositories) > 3:
            opportunities.append({
                "type": "monorepo_consolidation",
                "description": "Multiple repositories could be consolidated into a monorepo",
                "affected_repositories": [r.name for r in repositories],
                "priority": "high",
            })
        
        # Check for shared dependencies
        all_deps = {}
        for repo in repositories:
            for dep in repo.dependencies:
                all_deps[dep] = all_deps.get(dep, 0) + 1
        
        common_deps = {dep: count for dep, count in all_deps.items() if count > 1}
        if common_deps:
            opportunities.append({
                "type": "shared_dependencies",
                "description": "Common dependencies could be managed centrally",
                "dependencies": list(common_deps.keys()),
                "priority": "medium",
            })
        
        return opportunities
    
    def _analyze_tech_stack(self, repositories: List[RepositoryInfo]) -> Dict[str, Any]:
        """Analyze technology stack"""
        languages = {}
        for repo in repositories:
            lang = repo.language
            languages[lang] = languages.get(lang, 0) + 1
        
        return {
            "languages": languages,
            "primary_language": max(languages, key=languages.get) if languages else "Unknown",
            "is_polyglot": len(languages) > 1,
        }
