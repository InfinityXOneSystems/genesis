# Agent System Documentation

## Overview

Genesis employs a multi-agent architecture where specialized agents work together to achieve autonomous engineering goals. Each agent has specific responsibilities and communicates through a shared context.

## Agent Types

### Base Agent

All agents inherit from `BaseAgent`, which provides:
- Structured logging
- Metric tracking
- Status management
- Context access

```python
from genesis.agents import BaseAgent, AgentContext

class CustomAgent(BaseAgent):
    def __init__(self, context: AgentContext):
        super().__init__("CustomAgent", context)
    
    async def execute(self) -> Dict[str, Any]:
        # Agent logic here
        pass
```

## Core Agents

### PlannerAgent

**Purpose**: Task planning and decomposition

**Responsibilities**:
- Analyze requirements
- Create execution plans
- Decompose complex tasks
- Identify dependencies

**Example Usage**:
```python
agent = PlannerAgent(context)
plan = await agent.execute()
print(plan["tasks"])
```

### BuilderAgent

**Purpose**: Code generation and implementation

**Responsibilities**:
- Generate code from specifications
- Apply patches
- Refactor existing code
- Track implementation progress

**Example Usage**:
```python
agent = BuilderAgent(context)
result = await agent.execute()
print(f"Patches applied: {result['patches_applied']}")
```

### ValidatorAgent

**Purpose**: Testing and validation

**Responsibilities**:
- Run unit tests
- Run integration tests
- Perform security scanning
- Validate code quality

**Example Usage**:
```python
agent = ValidatorAgent(context)
result = await agent.execute()
print(f"Pass rate: {result['pass_rate']}")
```

### IdeaGeneratorAgent

**Purpose**: Innovation and improvement proposals

**Responsibilities**:
- Analyze benchmarks
- Generate improvement ideas
- Prioritize proposals
- Estimate impact

**Example Usage**:
```python
agent = IdeaGeneratorAgent(context)
result = await agent.execute()
for idea in result["ideas"]:
    print(f"{idea['title']}: {idea['priority']}")
```

### MemoryAgent

**Purpose**: Context management and RAG

**Responsibilities**:
- Store information
- Retrieve relevant context
- Manage embeddings
- Optimize memory

**Example Usage**:
```python
agent = MemoryAgent(context)

# Store information
agent.store("key", "value", metadata={"type": "config"})

# Retrieve information
results = agent.retrieve("key", top_k=5)
```

### EvolutionAgent

**Purpose**: System optimization

**Responsibilities**:
- Assess system performance
- Generate improvements
- Apply safe changes
- Track progress

**Example Usage**:
```python
agent = EvolutionAgent(context)
result = await agent.execute()
print(f"Score: {result['current_score']} -> {result['new_score']}")
```

### DeploymentAgent

**Purpose**: Deployment operations

**Responsibilities**:
- Deploy changes
- Health checking
- Rollback on failure
- Canary deployments

**Example Usage**:
```python
agent = DeploymentAgent(context)
result = await agent.execute()
print(f"Deployment: {result['status']}")
```

## Agent Context

The `AgentContext` provides shared state between agents:

```python
context = AgentContext(repository_path="/path/to/repo")

# Add to memory
context.add_memory("key", "value")

# Get from memory
value = context.get_latest_memory("key")

# Store metrics
context.metrics["my_metric"] = 0.95
```

## Agent Coordination

Agents coordinate through the Orchestrator:

```python
from genesis.core import Orchestrator

orchestrator = Orchestrator(
    repository_path="/path/to/repo",
    output_dir=Path("./output")
)

# Run single agent
result = await orchestrator.run_agent("planner")

# Run full cycle
results = await orchestrator.run_full_cycle()
```

## Custom Agents

To create a custom agent:

1. **Inherit from BaseAgent**:
```python
from genesis.agents import BaseAgent, AgentContext

class MyAgent(BaseAgent):
    def __init__(self, context: AgentContext):
        super().__init__("MyAgent", context)
```

2. **Implement execute method**:
```python
async def execute(self) -> Dict[str, Any]:
    self.status = "working"
    self.log_action("start", {})
    
    # Your logic here
    result = self._do_work()
    
    self.log_metric("work_done", 1.0)
    self.status = "completed"
    
    return result
```

3. **Register with orchestrator**:
```python
orchestrator.agents["my_agent"] = MyAgent(context)
```

## Best Practices

1. **Always log actions**: Use `self.log_action()` for traceability
2. **Track metrics**: Use `self.log_metric()` for monitoring
3. **Update status**: Keep status current (initialized, working, completed, failed)
4. **Use context**: Share data through context, not global variables
5. **Handle errors**: Catch exceptions and update status to "failed"
6. **Be idempotent**: Agents should be safe to re-run
7. **Document behavior**: Add docstrings explaining agent purpose

## Agent Lifecycle

1. **Initialization**: Created with context
2. **Execution**: `execute()` method called
3. **Action Logging**: Actions logged throughout
4. **Metric Tracking**: Metrics recorded
5. **Memory Update**: Results stored in context
6. **Completion**: Status updated to completed

## Testing Agents

```python
import pytest
from genesis.agents import AgentContext, MyAgent

@pytest.fixture
def context():
    return AgentContext(repository_path="/tmp/test")

@pytest.mark.asyncio
async def test_my_agent(context):
    agent = MyAgent(context)
    result = await agent.execute()
    
    assert result["status"] == "success"
    assert agent.status == "completed"
```

## Performance Considerations

- Agents run asynchronously for better performance
- Use caching to avoid redundant work
- Batch operations when possible
- Monitor metrics to identify bottlenecks
- Scale horizontally by running multiple instances

## Security

- Validate all inputs
- Sanitize outputs
- Use least-privilege access
- Log security-relevant actions
- Scan for vulnerabilities regularly
