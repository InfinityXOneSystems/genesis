# DevOps Team - Auto-Healing System

## Overview

The Genesis DevOps team is a comprehensive autonomous agent system that provides full automation for development operations including analysis, diagnosis, healing, conflict resolution, validation, and merging.

## Team Structure

The DevOps team consists of 6 specialized agents, each with specific responsibilities:

### 1. Workflow Analyzer 📊
**Role**: CI/CD Analysis & Workflow Intelligence

**Capabilities**:
- Monitors all GitHub Actions workflows across repositories
- Analyzes workflow runs and identifies failures
- Detects patterns in CI/CD issues
- Categorizes failures (test, lint, build, security, dependency, deployment)
- Provides intelligent insights and optimization recommendations

**Example Usage**:
```python
from genesis.core.workflow_analyzer import workflow_analyzer

# Analyze a workflow run
result = workflow_analyzer.analyze_workflow_run(
    workflow_name="CI",
    run_id=123,
    logs=workflow_logs,
    status="failure"
)

print(f"Category: {result['category']}")
print(f"Severity: {result['severity']}")
print(f"Root cause: {result['root_cause']}")
print(f"Recommendations: {result['recommendations']}")
```

### 2. Auto Diagnostician 🔍
**Role**: Automated Diagnostics & Issue Detection

**Capabilities**:
- Automatically diagnoses system issues from error messages and stack traces
- Performs health checks across all repositories
- Identifies dependency conflicts and version issues
- Detects code quality and security issues
- Provides root cause analysis with evidence

**Example Usage**:
```python
from genesis.core.auto_diagnostician import auto_diagnostician

# Diagnose an error
diagnosis = auto_diagnostician.diagnose_error(
    error_message="ModuleNotFoundError: No module named 'pytest'",
    stack_trace=stack_trace,
    context={"file": "test.py", "line": 10}
)

print(f"Issue type: {diagnosis.issue_type.value}")
print(f"Root cause: {diagnosis.root_cause}")
print(f"Severity: {diagnosis.severity}")
for rec in diagnosis.recommendations:
    print(f"  - {rec}")
```

### 3. Auto Healer 🔧
**Role**: Automated Fixing & Self-Healing

**Capabilities**:
- Automatically fixes identified issues
- Implements self-healing solutions for common problems
- Updates dependencies to fix vulnerabilities
- Repairs broken code and tests
- Fixes configuration errors and formatting issues

**Healing Strategies**:
- **Dependency Update**: Runs package manager to install/update dependencies
- **Security Patch**: Applies security updates and patches vulnerabilities
- **Format Fix**: Auto-formats code using black, prettier, etc.
- **Configuration Fix**: Creates missing config files, fixes environment variables
- **Code Fix**: LLM-assisted code repair (requires integration)

**Example Usage**:
```python
from genesis.core.auto_healer import auto_healer
from genesis.core.auto_diagnostician import auto_diagnostician

# First diagnose the issue
diagnosis = auto_diagnostician.diagnose_error(error_message, stack_trace)

# Then heal it
healing_result = auto_healer.heal_issue(diagnosis, auto_commit=True)

if healing_result.success:
    print(f"Successfully healed using {healing_result.strategy.value}")
    print(f"Files modified: {healing_result.files_modified}")
    print(f"Validation passed: {healing_result.validation_passed}")
else:
    print(f"Healing failed: {healing_result.error_message}")
```

### 4. Conflict Resolver 🤝
**Role**: Merge Conflict Resolution

**Capabilities**:
- Automatically resolves Git merge conflicts
- Uses semantic analysis to intelligently merge changes
- Handles conflicts in JSON, YAML, Markdown, and code files
- Merges compatible changes from both sides
- Identifies conflicts requiring manual review

**Resolution Strategies**:
1. **Empty Side**: Use the non-empty side
2. **Identical**: Both sides are the same
3. **Compatible Changes**: Merge both when changes are in different areas
4. **JSON Merge**: Merge JSON objects intelligently
5. **Import Merge**: Combine unique import statements

**Example Usage**:
```python
from genesis.core.conflict_resolver import conflict_resolver

# Detect conflicts
conflicts = conflict_resolver.detect_conflicts()

if conflicts:
    # Resolve them automatically
    result = conflict_resolver.resolve_conflicts(auto_commit=True)
    
    print(f"Resolved: {result.conflicts_resolved} conflicts")
    print(f"Files: {result.files_modified}")
    print(f"Manual review needed: {result.manual_review_needed}")
```

### 5. Auto Validator ✅
**Role**: Automated Validation & Verification

**Capabilities**:
- Continuously validates all changes
- Runs comprehensive test suites (pytest, jest, etc.)
- Executes linters and code quality checks
- Performs security scans
- Calculates quality scores
- Enforces quality gates

**Example Usage**:
```python
from genesis.core.auto_validator import auto_validator

# Validate changes
result = auto_validator.validate_changes(
    run_tests=True,
    run_linters=True,
    run_security=True
)

print(f"Overall status: {result.overall_status.value}")
print(f"Quality score: {result.quality_score:.2f}/100")
print(f"Tests: {result.tests_passed} passed, {result.tests_failed} failed")

if result.issues_found:
    print("Issues found:")
    for issue in result.issues_found:
        print(f"  - {issue}")
```

### 6. Auto Merger 🚀
**Role**: Automated PR Management & Merging

**Capabilities**:
- Automatically merges validated PRs
- Squashes commits for clean history
- Manages branch lifecycle
- Closes related issues automatically
- Handles bulk merge operations

**Example Usage**:
```python
from genesis.core.auto_merger import auto_merger

# Check if PR can be merged
readiness = auto_merger.can_merge_pr(
    pr_number=42,
    require_checks=True,
    require_approvals=False
)

if readiness["can_merge"]:
    # Merge the PR
    result = auto_merger.merge_pr(
        pr_number=42,
        squash=True,
        delete_branch=True,
        close_issues=True
    )
    
    if result.status.value == "success":
        print(f"Merged PR #{result.pr_number}")
        print(f"Commit SHA: {result.commit_sha}")
        print(f"Issues closed: {result.issues_closed}")
```

## Workflow Integration

### Genesis Loop Integration

The DevOps team is fully integrated into the Genesis autonomous loop:

```
Plan → Code → Validate → Diagnose → Heal → Deploy
```

**New Phases**:
- **Diagnose**: Analyzes workflow failures and system health
- **Heal**: Auto-fixes issues and resolves conflicts

**Usage**:
```bash
# Run full loop with all phases
python src/genesis/core/loop.py full

# Run specific phase
python src/genesis/core/loop.py diagnose
python src/genesis/core/loop.py heal
```

### GitHub Actions Workflows

#### DevOps Team Workflow
Located at: `.github/workflows/devops-team.yml`

Runs every 2 hours to continuously monitor and heal the system:

1. **Analyze**: Analyzes workflow failures across repositories
2. **Diagnose**: Diagnoses identified issues
3. **Heal**: Auto-fixes issues and resolves conflicts
4. **Validate**: Validates fixes with tests and linters
5. **Merge**: Auto-merges validated PRs with `autonomous-verified` label

**Trigger**:
```bash
# Manual trigger
gh workflow run devops-team.yml --ref main

# Trigger specific action
gh workflow run devops-team.yml --ref main -f action=heal
```

#### Enhanced Genesis Loop
Located at: `.github/workflows/genesis-loop.yml`

Now includes diagnose and heal phases:
- Runs every 6 hours
- Always runs diagnose and heal, even if validation fails
- Provides comprehensive system health monitoring

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Genesis DevOps Team                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Workflow   │  │     Auto     │  │     Auto     │     │
│  │   Analyzer   │─▶│ Diagnostician│─▶│    Healer    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│         │                  │                  │              │
│         │                  │                  │              │
│         ▼                  ▼                  ▼              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Conflict   │  │     Auto     │  │     Auto     │     │
│  │   Resolver   │  │  Validator   │  │    Merger    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Failure Categories

The system categorizes failures into:

1. **Test Failure**: Unit, integration, or E2E test failures
2. **Lint Failure**: Code style violations
3. **Build Failure**: Compilation or build errors
4. **Security Failure**: Vulnerabilities in code or dependencies
5. **Dependency Failure**: Missing or conflicting dependencies
6. **Deployment Failure**: Deployment configuration or execution issues
7. **Timeout**: Operations exceeding time limits

## Issue Types

The diagnostician identifies:

1. **Dependency Conflict**: Version mismatches, missing packages
2. **Configuration Error**: Missing or invalid configuration
3. **Code Quality**: Code style, complexity, or structure issues
4. **Security Vulnerability**: CVEs, security issues in dependencies
5. **Performance Issue**: Slow operations, memory leaks
6. **Integration Failure**: External service connection issues
7. **Resource Exhaustion**: Memory, disk, or handle exhaustion

## Healing Process

```
Error Detected
     ↓
Workflow Analyzer (categorize)
     ↓
Auto Diagnostician (diagnose root cause)
     ↓
Auto Healer (apply fix strategy)
     ↓
Auto Validator (validate fix)
     ↓
Auto Merger (merge if validated)
```

## Configuration

### Environment Variables

```bash
# GitHub token for API access
export GITHUB_TOKEN=your_token_here

# Optional: Configure healing behavior
export AUTO_HEAL_ENABLED=true
export AUTO_MERGE_ENABLED=true
export REQUIRE_VALIDATION=true
```

### Labels

The system uses GitHub labels:

- `autonomous-verified`: PRs ready for auto-merge
- `auto-healed`: Issues/PRs fixed by auto-healer
- `needs-manual-review`: Complex issues requiring human review

## Monitoring

The DevOps team provides comprehensive monitoring:

1. **Workflow Analysis Reports**: Categorized failure analysis
2. **Diagnostic Reports**: Root cause identification with evidence
3. **Healing Reports**: Actions taken and validation results
4. **Quality Scores**: Calculated quality metrics (0-100)
5. **Merge Reports**: Successful merges and closed issues

## Best Practices

1. **Trust but Verify**: The system is designed to handle common issues automatically, but always review critical changes
2. **Iterative Healing**: The heal phase runs even after validation failures to continuously improve
3. **Quality Gates**: Set appropriate thresholds for auto-merge (e.g., quality score > 80)
4. **Monitoring**: Regularly review DevOps team reports to identify patterns
5. **Manual Review**: Some issues are flagged for manual review - investigate these promptly

## Limitations

- **Code Fixes**: Complex code fixes require LLM integration (not included in base implementation)
- **Conflict Resolution**: Very complex conflicts with semantic ambiguity need manual review
- **Security Patches**: Some security issues may require architectural changes beyond auto-healing
- **Test Fixes**: Broken tests may require understanding business logic (LLM-assisted)

## Future Enhancements

1. **LLM Integration**: For intelligent code generation and complex fixes
2. **Learning System**: Learn from past fixes to improve strategies
3. **Multi-Repo Coordination**: Coordinate fixes across multiple repositories
4. **Rollback System**: Automatic rollback on validation failures
5. **Predictive Healing**: Predict and prevent issues before they occur

## Contributing

To extend the DevOps team:

1. Add new healing strategies in `auto_healer.py`
2. Add new conflict resolution strategies in `conflict_resolver.py`
3. Add new diagnostic patterns in `auto_diagnostician.py`
4. Add new failure categories in `workflow_analyzer.py`
5. Write tests for new functionality in `tests/test_devops_team.py`

## Support

For issues or questions:
- Check logs in `logs/` directory
- Review workflow run artifacts in GitHub Actions
- Consult the main Genesis documentation
- Open an issue in the repository
