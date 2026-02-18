"""PlannerAgent - Analyzes requirements and creates execution plans"""

from typing import Any, Dict, List
from genesis.agents.base import BaseAgent, AgentContext


class PlannerAgent(BaseAgent):
    """Agent responsible for planning and task decomposition"""
    
    def __init__(self, context: AgentContext):
        super().__init__("PlannerAgent", context)
    
    async def execute(self) -> Dict[str, Any]:
        """Create an execution plan based on analysis"""
        self.status = "planning"
        self.log_action("start_planning", {"context": "global_analysis"})
        
        # Analyze current state
        analysis = self.context.analysis_results
        
        # Generate plan
        plan = self._generate_plan(analysis)
        
        # Store plan in context
        self.context.add_memory("execution_plan", plan)
        
        self.log_metric("plan_complexity", len(plan.get("tasks", [])))
        self.status = "completed"
        
        return plan
    
    def _generate_plan(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate an execution plan"""
        # Extract insights from analysis
        repositories = analysis.get("repositories", [])
        dependencies = analysis.get("dependencies", {})
        
        # Create task list
        tasks = []
        
        # Phase 1: Analysis
        tasks.append({
            "phase": "analysis",
            "task": "complete_repository_scan",
            "priority": "high",
            "dependencies": [],
        })
        
        # Phase 2: Architecture
        if repositories:
            tasks.append({
                "phase": "architecture",
                "task": "create_unified_structure",
                "priority": "high",
                "dependencies": ["complete_repository_scan"],
            })
        
        # Phase 3: Implementation
        tasks.append({
            "phase": "implementation",
            "task": "implement_agents",
            "priority": "high",
            "dependencies": ["create_unified_structure"],
        })
        
        # Phase 4: Benchmarking
        tasks.append({
            "phase": "benchmarking",
            "task": "run_benchmarks",
            "priority": "medium",
            "dependencies": ["implement_agents"],
        })
        
        # Phase 5: Optimization
        tasks.append({
            "phase": "optimization",
            "task": "recursive_improvement",
            "priority": "medium",
            "dependencies": ["run_benchmarks"],
        })
        
        return {
            "tasks": tasks,
            "total_phases": 5,
            "estimated_complexity": "high",
            "can_parallelize": True,
        }
    
    def decompose_task(self, task: str) -> List[Dict[str, Any]]:
        """Decompose a high-level task into subtasks"""
        subtasks = []
        
        if task == "implement_agents":
            agents = [
                "PlannerAgent",
                "BuilderAgent",
                "ValidatorAgent",
                "IdeaGeneratorAgent",
                "MemoryAgent",
                "EvolutionAgent",
                "DeploymentAgent",
            ]
            for agent in agents:
                subtasks.append({
                    "name": f"implement_{agent.lower()}",
                    "description": f"Implement {agent}",
                    "estimated_time": "2h",
                })
        
        return subtasks
