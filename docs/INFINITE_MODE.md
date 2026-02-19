# Genesis Infinite Mode Configuration

## Overview

Genesis now supports **Infinite Mode** - a constraint-free operational mode that allows the autonomous system to continuously improve without artificial limitations.

## What is Infinite Mode?

In traditional mode, Genesis operates with:
- Fixed iteration limits (default: 50 iterations)
- Hard validation thresholds (95% pass rate for deployment)
- Target threshold stopping conditions
- Evolution loop caps (10 iterations)

**Infinite Mode removes these constraints**, enabling:
- ♾️ Unlimited iterations - runs until externally stopped
- 📈 Continuous improvement without stopping at thresholds
- 🔄 Self-regulated evolution based on actual performance
- 🚀 Dynamic validation criteria (90% in infinite mode vs 95% standard)

## Configuration Options

### CLI Usage

```bash
# Standard mode with default limits
genesis loop --repo-path . --threshold 1.2

# Custom iteration limit
genesis loop --repo-path . --threshold 1.2 --max-iterations 100

# Unlimited iterations (runs until threshold met)
genesis loop --repo-path . --threshold 1.2 --max-iterations 0

# Infinite mode (never stops, continuous improvement)
genesis loop --repo-path . --infinite
```

### GitHub Actions Workflow

The workflow now supports infinite mode via workflow_dispatch inputs:

```yaml
workflow_dispatch:
  inputs:
    threshold:
      description: 'Target threshold'
      default: '1.2'
    max_iterations:
      description: 'Max iterations (0 for unlimited)'
      default: ''
    infinite_mode:
      description: 'Enable infinite mode'
      type: boolean
      default: false
```

### Python API

```python
from genesis.core import AutonomousLoop

# Standard mode
loop = AutonomousLoop(
    repository_path=".",
    target_threshold=1.2,
    max_iterations=50
)

# Continuous mode (no iteration limit, stops at threshold)
loop = AutonomousLoop(
    repository_path=".",
    target_threshold=1.2,
    max_iterations=None
)

# Infinite mode (never stops)
loop = AutonomousLoop(
    repository_path=".",
    target_threshold=1.2,
    infinite_mode=True
)

await loop.run()
```

## Dynamic Validation Thresholds

The system automatically adjusts validation thresholds based on mode:

| Mode | Deployment Threshold | Philosophy |
|------|---------------------|------------|
| Standard | 95% pass rate | Conservative, safe deployments |
| Infinite | 90% pass rate | More aggressive, faster iteration |
| Configurable | Custom via context | Adapt to system maturity |

Configuration via orchestrator context:
```python
context.set_config("min_deployment_pass_rate", 0.85)  # Custom threshold
```

## Evolution Loop

The evolution loop also supports infinite mode:

```python
from genesis.core import Orchestrator

orchestrator = Orchestrator(repository_path=".")

# Standard evolution (10 iterations)
await orchestrator.run_evolution_loop(max_iterations=10)

# Infinite evolution
await orchestrator.run_evolution_loop(infinite_mode=True)
```

## Safety Considerations

### Resource Management

Infinite mode respects:
- GitHub Actions workflow timeout (6 hours default)
- System resource limits
- External termination signals

### Monitoring

When running in infinite mode:
- Monitor system metrics closely
- Set up alerts for anomalies
- Use structured logging to track iterations
- Review outputs regularly

### Best Practices

1. **Start with standard mode** to understand system behavior
2. **Use continuous mode** (unlimited iterations with threshold) before infinite
3. **Reserve infinite mode** for long-running autonomous improvement scenarios
4. **Set up external monitoring** when using infinite mode in production
5. **Use workflow timeouts** as a safety net

## Integration with Infinity Orchestrator

Genesis can integrate with external orchestration systems like the Infinity Orchestrator GitHub App for:
- Distributed constraint-free operation
- Cross-repository coordination
- Resource pooling
- Advanced scheduling

To enable integration:
```bash
# Set environment variable
export INFINITY_ORCHESTRATOR_ENABLED=true
export INFINITY_ORCHESTRATOR_APP_ID=your_app_id

# Or via configuration
genesis loop --infinite --orchestrator infinity
```

## Environment Variables

- `GENESIS_INFINITE_MODE` - Enable infinite mode globally
- `GENESIS_MAX_ITERATIONS` - Default max iterations (0 = unlimited)
- `GENESIS_MIN_PASS_RATE` - Minimum validation pass rate
- `INFINITY_ORCHESTRATOR_ENABLED` - Enable external orchestrator integration

## Logging and Observability

Infinite mode includes enhanced logging:
```
🚀 Infinite mode enabled - no iteration constraints
🔄 Evolution iteration 42 (infinite)
📊 Pass rate: 91.5% (threshold: 90.0%)
♾️  Continuing autonomous improvement...
```

## Philosophy

> "Remove artificial limitations to unleash autonomous potential."

Genesis is designed to continuously improve itself without human-imposed constraints. Infinite mode embodies this philosophy by:
- Trusting the autonomous agents to self-regulate
- Letting the system decide when to stop (never, in infinite mode)
- Prioritizing learning and experimentation
- Embracing continuous evolution

## Support and Feedback

For questions or feedback about infinite mode:
- Open an issue on GitHub
- Review the implementation in `src/genesis/core/loop.py`
- Check logs for troubleshooting
- Monitor system metrics

---

**Note**: Infinite mode is experimental and designed for autonomous systems with proper monitoring and safety guardrails in place.
