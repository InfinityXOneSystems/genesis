"""Core Orchestrator - Coordinates all agents and workflows"""

import asyncio
from typing import Any, Dict, List, Optional
from pathlib import Path

from genesis.agents import (
    AgentContext,
    PlannerAgent,
    BuilderAgent,
    ValidatorAgent,
    IdeaGeneratorAgent,
    MemoryAgent,
    EvolutionAgent,
    DeploymentAgent,
)
from genesis.utils import setup_logging, save_json_report, StructuredLogger


class Orchestrator:
    """Central orchestrator for the multi-agent system"""
    
    def __init__(self, repository_path: str, output_dir: Optional[Path] = None):
        self.repository_path = repository_path
        self.output_dir = output_dir or Path("./output")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self.logger = setup_logging(log_file=self.output_dir / "orchestrator.log")
        self.structured_logger = StructuredLogger("Orchestrator")
        
        # Initialize context
        self.context = AgentContext(repository_path=repository_path)
        
        # Initialize agents
        self.agents = {
            "planner": PlannerAgent(self.context),
            "builder": BuilderAgent(self.context),
            "validator": ValidatorAgent(self.context),
            "idea_generator": IdeaGeneratorAgent(self.context),
            "memory": MemoryAgent(self.context),
            "evolution": EvolutionAgent(self.context),
            "deployment": DeploymentAgent(self.context),
        }
        
        self.logger.info("Orchestrator initialized with %d agents", len(self.agents))
    
    async def run_full_cycle(self) -> Dict[str, Any]:
        """Run a complete autonomous engineering cycle"""
        self.structured_logger.log_action("start_full_cycle", {
            "agents": list(self.agents.keys()),
        })
        
        results = {}
        
        # Phase 1: Planning
        self.logger.info("Phase 1: Planning")
        results["planning"] = await self.agents["planner"].execute()
        
        # Phase 2: Idea Generation
        self.logger.info("Phase 2: Idea Generation")
        results["ideas"] = await self.agents["idea_generator"].execute()
        
        # Phase 3: Building
        self.logger.info("Phase 3: Building")
        results["building"] = await self.agents["builder"].execute()
        
        # Phase 4: Validation
        self.logger.info("Phase 4: Validation")
        results["validation"] = await self.agents["validator"].execute()
        
        # Phase 5: Memory Update
        self.logger.info("Phase 5: Memory Update")
        results["memory"] = await self.agents["memory"].execute()
        
        # Phase 6: Evolution
        self.logger.info("Phase 6: Evolution")
        results["evolution"] = await self.agents["evolution"].execute()
        
        # Phase 7: Deployment (if safe)
        if results["validation"].get("pass_rate", 0) >= 0.95:
            self.logger.info("Phase 7: Deployment")
            self.context.add_memory("validation_results", results["validation"])
            results["deployment"] = await self.agents["deployment"].execute()
        else:
            self.logger.warning("Skipping deployment - validation failed")
            results["deployment"] = {"status": "skipped", "reason": "validation_failed"}
        
        # Save results
        self._save_cycle_results(results)
        
        self.structured_logger.log_action("complete_full_cycle", {
            "phases_completed": len(results),
        })
        
        return results
    
    async def run_agent(self, agent_name: str) -> Dict[str, Any]:
        """Run a specific agent"""
        if agent_name not in self.agents:
            raise ValueError(f"Unknown agent: {agent_name}")
        
        self.logger.info(f"Running agent: {agent_name}")
        result = await self.agents[agent_name].execute()
        
        return result
    
    async def run_evolution_loop(self, max_iterations: int = 10) -> Dict[str, Any]:
        """Run the recursive improvement loop"""
        self.structured_logger.log_action("start_evolution_loop", {
            "max_iterations": max_iterations,
        })
        
        iteration = 0
        evolution_agent = self.agents["evolution"]
        
        while iteration < max_iterations and evolution_agent.should_continue_evolution():
            self.logger.info(f"Evolution iteration {iteration + 1}/{max_iterations}")
            
            # Run evolution cycle
            result = await evolution_agent.execute()
            
            # Check if target reached
            if result.get("target_reached", False):
                self.logger.info("Target score reached!")
                break
            
            iteration += 1
        
        final_score = evolution_agent.current_score
        target_score = evolution_agent.target_score
        
        return {
            "iterations": iteration,
            "final_score": final_score,
            "target_score": target_score,
            "target_reached": final_score >= target_score,
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        return {
            "agents": {
                name: agent.get_status()
                for name, agent in self.agents.items()
            },
            "context": {
                "memory_entries": len(self.context.memory),
                "metrics": self.context.metrics,
            },
        }
    
    def _save_cycle_results(self, results: Dict[str, Any]) -> None:
        """Save cycle results to file"""
        output_file = self.output_dir / "cycle_results.json"
        save_json_report(results, output_file)


async def main() -> None:
    """Main entry point for testing"""
    orchestrator = Orchestrator(
        repository_path="/home/runner/work/genesis/genesis",
        output_dir=Path("./output"),
    )
    
    # Run a full cycle
    results = await orchestrator.run_full_cycle()
    
    print("\n=== Cycle Results ===")
    for phase, result in results.items():
        print(f"{phase}: {result.get('status', 'unknown')}")
    
    # Get system status
    status = orchestrator.get_system_status()
    print(f"\nTotal metrics: {len(status['context']['metrics'])}")


if __name__ == "__main__":
    asyncio.run(main())
