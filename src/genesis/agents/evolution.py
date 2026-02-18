"""EvolutionAgent - Optimizes system performance through recursive improvement"""

from typing import Any, Dict, List
from genesis.agents.base import BaseAgent, AgentContext


class EvolutionAgent(BaseAgent):
    """Agent responsible for system evolution and optimization"""
    
    def __init__(self, context: AgentContext):
        super().__init__("EvolutionAgent", context)
        self.improvement_cycles = 0
        self.current_score = 0.0
        self.target_score = 1.2  # 20% better than baseline
    
    async def execute(self) -> Dict[str, Any]:
        """Execute evolution cycle"""
        self.status = "evolving"
        self.log_action("start_evolution", {"cycle": self.improvement_cycles})
        
        # Assess current state
        current_score = await self._assess_system()
        
        # Generate improvements
        improvements = await self._generate_improvements(current_score)
        
        # Apply safe improvements
        applied = await self._apply_improvements(improvements)
        
        # Update score
        new_score = await self._assess_system()
        improvement = new_score - current_score
        
        self.improvement_cycles += 1
        self.current_score = new_score
        
        self.log_metric("system_score", new_score)
        self.log_metric("improvement_delta", improvement)
        
        self.status = "completed"
        
        return {
            "status": "success",
            "cycle": self.improvement_cycles,
            "current_score": current_score,
            "new_score": new_score,
            "improvement": improvement,
            "improvements_applied": applied,
            "target_reached": new_score >= self.target_score,
        }
    
    async def _assess_system(self) -> float:
        """Assess current system performance"""
        # Get metrics from context
        metrics = self.context.metrics
        
        # Calculate composite score
        weights = {
            "test_pass_rate": 0.3,
            "performance": 0.25,
            "security": 0.20,
            "coverage": 0.15,
            "maintainability": 0.10,
        }
        
        score = 0.0
        for metric, weight in weights.items():
            value = metrics.get(f"ValidatorAgent.{metric}", 0.8)  # Default 0.8
            score += value * weight
        
        return score
    
    async def _generate_improvements(self, current_score: float) -> List[Dict[str, Any]]:
        """Generate potential improvements"""
        improvements = []
        
        # Get ideas from IdeaGeneratorAgent
        ideas = self.context.get_latest_memory("improvement_ideas")
        
        if ideas:
            for idea in ideas:
                improvements.append({
                    "type": "implement_idea",
                    "idea": idea,
                    "estimated_impact": idea.get("estimated_impact", 0.05),
                    "risk": "low" if idea.get("priority") == "low" else "medium",
                })
        
        # Add system-level improvements
        if current_score < 0.9:
            improvements.append({
                "type": "increase_test_coverage",
                "estimated_impact": 0.10,
                "risk": "low",
            })
        
        if current_score < 0.8:
            improvements.append({
                "type": "optimize_performance",
                "estimated_impact": 0.15,
                "risk": "medium",
            })
        
        return improvements
    
    async def _apply_improvements(self, improvements: List[Dict[str, Any]]) -> int:
        """Apply safe improvements"""
        applied = 0
        
        for improvement in improvements:
            # Only apply low-risk improvements automatically
            if improvement.get("risk") == "low":
                self.log_action("apply_improvement", {"type": improvement["type"]})
                applied += 1
        
        return applied
    
    def should_continue_evolution(self) -> bool:
        """Determine if evolution should continue"""
        return (
            self.current_score < self.target_score
            and self.improvement_cycles < 100
        )
