"""IdeaGeneratorAgent - Proposes improvements and innovations"""

from typing import Any, Dict, List
from genesis.agents.base import BaseAgent, AgentContext


class IdeaGeneratorAgent(BaseAgent):
    """Agent responsible for generating improvement ideas"""
    
    def __init__(self, context: AgentContext):
        super().__init__("IdeaGeneratorAgent", context)
    
    async def execute(self) -> Dict[str, Any]:
        """Generate improvement ideas based on analysis and benchmarks"""
        self.status = "generating"
        self.log_action("start_idea_generation", {})
        
        # Get benchmarks and analysis
        benchmarks = self.context.benchmarks
        analysis = self.context.analysis_results
        
        # Generate ideas
        ideas = self._generate_ideas(benchmarks, analysis)
        
        # Store ideas in context
        self.context.add_memory("improvement_ideas", ideas)
        
        self.log_metric("ideas_generated", len(ideas))
        self.status = "completed"
        
        return {
            "status": "success",
            "ideas_count": len(ideas),
            "ideas": ideas,
        }
    
    def _generate_ideas(
        self,
        benchmarks: Dict[str, Any],
        analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate improvement ideas"""
        ideas = []
        
        # Performance improvements
        ideas.append({
            "category": "performance",
            "title": "Implement async/await for I/O operations",
            "description": "Convert synchronous operations to async for better performance",
            "priority": "high",
            "estimated_impact": 0.25,  # 25% improvement
        })
        
        # Architecture improvements
        ideas.append({
            "category": "architecture",
            "title": "Add caching layer for repeated operations",
            "description": "Implement Redis caching for frequently accessed data",
            "priority": "medium",
            "estimated_impact": 0.15,
        })
        
        # Security improvements
        ideas.append({
            "category": "security",
            "title": "Implement end-to-end encryption for sensitive data",
            "description": "Add encryption at rest and in transit",
            "priority": "high",
            "estimated_impact": 0.10,
        })
        
        # Testing improvements
        ideas.append({
            "category": "testing",
            "title": "Increase test coverage to 95%",
            "description": "Add tests for edge cases and error paths",
            "priority": "medium",
            "estimated_impact": 0.20,
        })
        
        # Documentation improvements
        ideas.append({
            "category": "documentation",
            "title": "Generate API documentation automatically",
            "description": "Use OpenAPI/Swagger for auto-generated docs",
            "priority": "low",
            "estimated_impact": 0.05,
        })
        
        return ideas
    
    def prioritize_ideas(self, ideas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prioritize ideas based on impact and feasibility"""
        # Sort by estimated impact (descending) and priority
        priority_map = {"high": 3, "medium": 2, "low": 1}
        
        sorted_ideas = sorted(
            ideas,
            key=lambda x: (priority_map.get(x["priority"], 0), x["estimated_impact"]),
            reverse=True,
        )
        
        return sorted_ideas
