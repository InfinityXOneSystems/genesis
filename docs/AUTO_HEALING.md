# Genesis Auto-Healing System

## Overview

The Genesis Auto-Healing System is a sophisticated, autonomous mechanism that continuously monitors GitHub Actions workflows and automatically fixes failures without human intervention. This system ensures the Genesis platform maintains 24/7 operational excellence.

## Architecture

### Components

1. **Workflow Monitor** (`workflow_monitor.py`)
   - Monitors all GitHub Actions workflows via GitHub API
   - Detects and categorizes failures
   - Provides health metrics and status reporting

2. **Healing Agent** (`healing_agent.py`)
   - Orchestrates healing operations
   - Implements specialized healing strategies
   - Manages retry logic with exponential backoff

3. **Healing Strategies**
   - Test Failure Strategy
   - Lint Failure Strategy
   - Dependency Failure Strategy
   - Security Failure Strategy
   - Build Failure Strategy

## How It Works

### 1. Failure Detection

The Workflow Monitor continuously polls GitHub Actions:

```python
from src.genesis.core.workflow_monitor import get_workflow_monitor

monitor = get_workflow_monitor()
health = monitor.get_workflow_health_status()
```

Health metrics include:
- Total workflows
- Total runs (24h window)
- Failed runs count
- Success rate percentage
- Health status: `healthy`, `degraded`, or `critical`

### 2. Failure Analysis

When a failure is detected, the monitor:

1. Retrieves workflow run details
2. Fetches job logs
3. Categorizes the failure type
4. Suggests appropriate healing strategies

```python
failures = monitor.get_failed_runs(hours=6)
for run in failures:
    failure = monitor.analyze_failure(run)
    print(f"Type: {failure.failure_type}")
    print(f"Fix: {failure.suggested_fix}")
```

### 3. Healing Strategies

Each failure type has a specialized healing strategy:

#### Test Failure Strategy

**Handles**: Failing pytest, jest, or other test suites

**Actions**:
1. Reruns tests to check for flakiness
2. Analyzes test output for common issues
3. Identifies import errors or fixture problems

**Success Rate**: High for flaky tests

#### Lint Failure Strategy

**Handles**: Black, isort, pylint, eslint failures

**Actions**:
1. Runs black formatter on Python code
2. Runs isort for import sorting
3. Auto-commits formatting changes

**Success Rate**: Very High (>90%)

```python
# Example: Auto-fix linting issues
from src.genesis.core.healing_agent import get_healing_agent

agent = get_healing_agent()
outcome = agent.heal_failure(lint_failure)
```

#### Dependency Failure Strategy

**Handles**: pip install, npm install failures

**Actions**:
1. Clears package manager cache
2. Reinstalls dependencies from requirements
3. Updates pinned versions if needed

**Success Rate**: High

#### Security Failure Strategy

**Handles**: CVE vulnerabilities, security scan failures

**Actions**:
1. Identifies vulnerable packages
2. Updates to patched versions
3. Commits security fixes

**Success Rate**: Medium (depends on breaking changes)

#### Build Failure Strategy

**Handles**: Compilation errors, build configuration issues

**Actions**:
1. Retries build process
2. Checks for common configuration errors
3. Attempts to fix build scripts

**Success Rate**: Medium

### 4. Recursive Retry Logic

The healing agent implements exponential backoff:

```
Attempt 1: Immediate
Attempt 2: Wait 2 seconds
Attempt 3: Wait 4 seconds
...
Attempt N: Wait 2^N seconds
```

Maximum retry attempts: 3 (configurable)

### 5. Healing Outcomes

Each healing operation produces a detailed outcome:

```json
{
  "workflow_run_id": 12345,
  "workflow_name": "CI",
  "failure_type": "lint_failure",
  "success": true,
  "message": "Applied fixes: black formatter, isort",
  "attempts": 1,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Integration with Genesis Loop

The healing phase is integrated into the main autonomous loop:

```
Plan → Code → Validate → Heal → Deploy
```

### GitHub Actions Workflow

The `heal` job runs after `validate`:

```yaml
heal:
  name: 🏥 Heal Phase
  runs-on: ubuntu-latest
  needs: [validate]
  if: always()
  
  steps:
    - name: Execute Heal Phase
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      run: |
        python src/genesis/core/loop.py heal
```

Note: The `if: always()` ensures healing runs even if validation fails.

## Usage

### Automatic (Recommended)

The healing system runs automatically every 6 hours as part of the Genesis Loop workflow.

### Manual Healing

Force a healing cycle:

```bash
# Run healing phase
python src/genesis/core/loop.py heal
```

### Check Workflow Health

```bash
# Python script
python -c "
from src.genesis.core.workflow_monitor import get_workflow_monitor
import json

monitor = get_workflow_monitor()
health = monitor.get_workflow_health_status()
print(json.dumps(health, indent=2))
"
```

### Healing Specific Failures

```python
from src.genesis.core.healing_agent import get_healing_agent
from pathlib import Path

# Initialize agent
agent = get_healing_agent(Path.cwd())

# Detect and heal all failures from last 6 hours
summary = agent.heal_all_failures(hours=6, max_attempts=3)

print(f"Healed: {summary['healed']}/{summary['total_failures']}")
print(f"Success rate: {summary['success_rate']:.1f}%")
```

## Configuration

### Environment Variables

```bash
# GitHub token for API access
export GITHUB_TOKEN=ghp_xxxxxxxxxxxxx
```

### Customization

Adjust healing parameters in `healing_agent.py`:

```python
# Maximum retry attempts per failure
MAX_ATTEMPTS = 3

# Time window for failure detection (hours)
DETECTION_WINDOW = 6

# Exponential backoff base
BACKOFF_BASE = 2
```

## Monitoring

### Healing History

The healing agent maintains a history of all operations:

```python
agent = get_healing_agent()
report = agent.get_healing_report()

print(f"Total attempts: {report['total_healing_attempts']}")
print(f"Successful: {report['successful_healings']}")
print(f"Failed: {report['failed_healings']}")
print(f"Success rate: {report['success_rate']:.1f}%")
```

### Workflow Health Dashboard

View real-time health metrics:

```python
monitor = get_workflow_monitor()
health = monitor.get_workflow_health_status()

if health['health_status'] == 'critical':
    print("⚠️ System health is critical!")
elif health['health_status'] == 'degraded':
    print("⚡ System health is degraded")
else:
    print("✅ System is healthy")
```

## Best Practices

1. **Monitor regularly**: Check healing reports after each cycle
2. **Review failed healings**: Some issues require manual intervention
3. **Keep strategies updated**: Add new strategies as patterns emerge
4. **Test healing logic**: Use unit tests to verify strategy effectiveness
5. **Log everything**: Maintain detailed logs for debugging

## Limitations

Current limitations and future improvements:

- **Manual fixes required**: Complex issues may still need human review
- **Strategy coverage**: Not all failure types have healing strategies
- **External dependencies**: Some fixes depend on third-party services
- **Rate limits**: GitHub API rate limits may affect monitoring frequency

## Future Enhancements

Planned improvements:

1. **Machine Learning**: Learn from healing patterns to improve strategies
2. **Predictive Healing**: Predict and prevent failures before they occur
3. **Cross-repository healing**: Heal failures across multiple repos
4. **Custom strategies**: User-defined healing strategies via configuration
5. **Advanced analytics**: Detailed failure pattern analysis and reporting

## Troubleshooting

### Healing not working

1. Check GitHub token permissions:
   ```bash
   echo $GITHUB_TOKEN
   ```

2. Verify API access:
   ```python
   from src.genesis.core.workflow_monitor import get_workflow_monitor
   monitor = get_workflow_monitor()
   workflows = monitor.get_workflows()
   print(f"Found {len(workflows)} workflows")
   ```

3. Check logs:
   ```bash
   tail -f logs/healing_agent.log
   ```

### High failure rate

If healing success rate is below 50%:

1. Review failure types:
   ```python
   agent = get_healing_agent()
   failures = agent.detect_failures(hours=24)
   for f in failures:
       print(f"Type: {f.failure_type}, Logs: {f.error_logs[:200]}")
   ```

2. Add custom strategies for common failures
3. Increase max retry attempts
4. Review and update existing strategies

## Contributing

To add a new healing strategy:

1. Create a new strategy class inheriting from `HealingStrategy`:

```python
class CustomFailureStrategy(HealingStrategy):
    def can_handle(self, failure: WorkflowFailure) -> bool:
        return failure.failure_type == "custom_failure"
    
    def heal(self, failure: WorkflowFailure, repo_path: Path) -> Tuple[bool, str]:
        # Implement healing logic
        return True, "Successfully healed custom failure"
```

2. Register the strategy in `HealingAgent.__init__`:

```python
self.strategies: List[HealingStrategy] = [
    TestFailureStrategy(),
    LintFailureStrategy(),
    # ... other strategies
    CustomFailureStrategy()  # Add your strategy
]
```

3. Add tests in `tests/test_healing_agent.py`

4. Update documentation

## Support

For issues or questions:

- Create an issue on GitHub
- Check existing documentation
- Review healing logs
- Contact the Genesis team

---

**Genesis Auto-Healing System** - Keeping the system running 24/7 without human intervention.
