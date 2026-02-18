# Genesis Onboarding Guide

Welcome to Genesis! This guide will help you get started with the autonomous AI engineering system.

## Quick Start

### Prerequisites

- Python 3.10 or higher
- Git
- Docker (optional, for containerized deployment)
- Kubernetes (optional, for production deployment)

### Installation

1. **Clone the repository**:
```bash
git clone https://github.com/InfinityXOneSystems/genesis.git
cd genesis
```

2. **Install dependencies**:
```bash
pip install -e ".[dev]"
```

3. **Verify installation**:
```bash
genesis --help
pytest tests/
```

## Basic Usage

### Scan a Repository

Analyze a repository to understand its structure:

```bash
genesis scan --repo-path /path/to/repo --output analysis/report.json
```

### Run Benchmarks

Compare Genesis against competitors:

```bash
genesis benchmark --output benchmarks/results.json
```

### Run a Full Cycle

Execute a complete autonomous cycle:

```bash
genesis run --repo-path . --output-dir ./output
```

### Run the Autonomous Loop

Start the continuous improvement loop:

```bash
genesis loop --repo-path . --threshold 1.2
```

## Understanding the System

### Multi-Agent Architecture

Genesis uses 7 specialized agents:

1. **PlannerAgent**: Creates execution plans
2. **BuilderAgent**: Implements changes
3. **ValidatorAgent**: Tests and validates
4. **IdeaGeneratorAgent**: Proposes improvements
5. **MemoryAgent**: Maintains context (RAG)
6. **EvolutionAgent**: Optimizes performance
7. **DeploymentAgent**: Handles deployments

### Autonomous Loop

The system continuously:
1. Assesses against benchmarks
2. Generates improvement patches
3. Tests in sandbox
4. Auto-merges if safe
5. Updates system score

### Target Goals

- **Primary**: 20% better than all competitors
- **Metrics**: Performance, autonomy, accuracy, scalability, security
- **Continuous**: System never stops improving

## Development Workflow

### Project Structure

```
genesis/
├── src/genesis/          # Core Python modules
│   ├── agents/          # Multi-agent system
│   ├── analysis/        # Code analysis
│   ├── benchmarking/    # Performance benchmarks
│   ├── core/            # Orchestration
│   └── utils/           # Utilities
├── tests/               # Test suites
├── docs/                # Documentation
├── infra/              # Infrastructure
└── .github/            # CI/CD workflows
```

### Running Tests

```bash
# All tests
pytest tests/ -v

# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# With coverage
pytest tests/ --cov=genesis --cov-report=html
```

### Code Quality

```bash
# Format code
black src tests

# Lint code
ruff check src tests

# Type checking
mypy src
```

## Using Programmatically

### Basic Example

```python
import asyncio
from pathlib import Path
from genesis.core import Orchestrator

async def main():
    # Initialize orchestrator
    orchestrator = Orchestrator(
        repository_path="/path/to/repo",
        output_dir=Path("./output")
    )
    
    # Run a full cycle
    results = await orchestrator.run_full_cycle()
    
    # Check results
    print(f"Planning: {results['planning']['status']}")
    print(f"Validation: {results['validation']['pass_rate']}")

asyncio.run(main())
```

### Custom Agent

```python
from genesis.agents import BaseAgent, AgentContext
from typing import Dict, Any

class CustomAgent(BaseAgent):
    def __init__(self, context: AgentContext):
        super().__init__("CustomAgent", context)
    
    async def execute(self) -> Dict[str, Any]:
        self.status = "working"
        self.log_action("custom_action", {"data": "example"})
        
        # Your logic here
        result = {"status": "success"}
        
        self.status = "completed"
        return result
```

## Deployment

### Docker

```bash
# Build image
docker build -t genesis:latest .

# Run container
docker run -it genesis:latest genesis --help
```

### Docker Compose

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f genesis

# Stop services
docker-compose down
```

### Kubernetes

```bash
# Install with Helm
helm install genesis ./infra/helm/genesis

# Check status
kubectl get pods -l app=genesis

# View logs
kubectl logs -l app=genesis -f
```

## Configuration

### Environment Variables

```bash
export GENESIS_ENV=production
export LOG_LEVEL=INFO
export GENESIS_TARGET_THRESHOLD=1.2
```

### Config File (Future)

```yaml
# config.yaml
environment: production
target_threshold: 1.2
log_level: INFO

agents:
  planner:
    enabled: true
  builder:
    enabled: true
  # ... more agents
```

## CI/CD Integration

Genesis includes GitHub Actions workflows:

1. **CI**: Runs tests, linting, security scans
2. **Genesis Loop**: Runs autonomous improvements every 6 hours
3. **Security**: Weekly vulnerability scans

### Manual Workflow Trigger

```bash
gh workflow run genesis-loop.yml -f threshold=1.2
```

## Troubleshooting

### Tests Failing

```bash
# Check test output
pytest tests/ -v --tb=long

# Run specific test
pytest tests/unit/test_agents.py::test_planner_agent -v
```

### Import Errors

```bash
# Reinstall package
pip install -e ".[dev]"

# Check installation
pip show genesis
```

### Performance Issues

```bash
# Profile code
python -m cProfile -o profile.stats src/genesis/cli.py run
python -m pstats profile.stats
```

## Getting Help

- **Documentation**: See `docs/` directory
- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Email**: team@genesis.ai

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run tests and linting
6. Submit a pull request

## Next Steps

1. Read [Architecture Documentation](docs/architecture.md)
2. Explore [Agent System](docs/agents.md)
3. Learn about [Benchmarking](docs/benchmarking.md)
4. Review [Deployment Guide](docs/deployment.md)

## Resources

- **Repository**: https://github.com/InfinityXOneSystems/genesis
- **Documentation**: https://genesis.readthedocs.io (planned)
- **Blog**: https://blog.genesis.ai (planned)
- **Twitter**: @genesis_ai (planned)

Welcome to the future of autonomous engineering! 🚀
