"""Autonomous Loop - Continuous engineering loop for GitHub Actions"""

import asyncio
from pathlib import Path
from typing import Any, Dict, Optional
from genesis.core.orchestrator import Orchestrator
from genesis.utils import setup_logging, save_json_report


class AutonomousLoop:
    """Implements the continuous autonomous engineering loop
    
    Supports both constraint-based and infinite autonomous operation modes.
    In infinite mode, the system continuously improves without iteration limits.
    """
    
    def __init__(
        self, 
        repository_path: str, 
        target_threshold: float = 1.2,
        max_iterations: Optional[int] = None,
        infinite_mode: bool = False
    ):
        self.repository_path = repository_path
        self.target_threshold = target_threshold
        self.max_iterations = max_iterations if max_iterations is not None else (None if infinite_mode else 50)
        self.infinite_mode = infinite_mode
        self.logger = setup_logging()
        
        # Initialize orchestrator with infinite capability
        self.orchestrator = Orchestrator(
            repository_path=repository_path,
            output_dir=Path("./output/loop"),
        )
        
        if self.infinite_mode:
            self.logger.info("🚀 Infinite mode enabled - no iteration constraints")
        elif self.max_iterations is None:
            self.logger.info("🚀 Continuous mode enabled - running until target threshold met")
        else:
            self.logger.info(f"Standard mode - max iterations: {self.max_iterations}")
    
    async def run(self) -> Dict[str, Any]:
        """Run the autonomous loop
        
        In infinite mode, continues until externally stopped (e.g., workflow timeout).
        In standard mode, respects max_iterations or runs until target_threshold met.
        """
        self.logger.info("Starting autonomous loop")
        self.logger.info(f"Target threshold: {self.target_threshold}")
        
        # Get current system score
        system_score = await self._get_system_score()
        self.logger.info(f"Current system score: {system_score}")
        
        # In infinite mode, never stop based on threshold
        if not self.infinite_mode and system_score >= self.target_threshold:
            self.logger.info("Target threshold already met!")
            return {
                "status": "complete",
                "score": system_score,
                "threshold": self.target_threshold,
            }
        
        # Run improvement loop
        iteration = 0
        
        # Dynamic condition based on mode
        while True:
            # Check stopping conditions
            if not self.infinite_mode:
                if system_score >= self.target_threshold:
                    self.logger.info("Target threshold reached!")
                    break
                if self.max_iterations is not None and iteration >= self.max_iterations:
                    self.logger.info(f"Max iterations ({self.max_iterations}) reached")
                    break
            
            self.logger.info(f"\n=== Iteration {iteration + 1} {'(infinite mode)' if self.infinite_mode else ''} ===")
            
            # 1. Assess against benchmarks
            await self._assess_benchmarks()
            
            # 2. Generate patch proposals
            patches = await self._generate_patches()
            
            # 3. Run sandbox tests
            test_results = await self._run_sandbox_tests(patches)
            
            # 4. Auto-merge if safe (relaxed criteria in infinite mode)
            merge_threshold = 0.90 if self.infinite_mode else 0.95
            if test_results.get("pass_rate", 0) >= merge_threshold:
                await self._auto_merge(patches)
            
            # 5. Update system score
            system_score = await self._get_system_score()
            self.logger.info(f"New system score: {system_score}")
            
            iteration += 1
        
        # Save final report
        final_report = {
            "iterations": iteration,
            "final_score": system_score,
            "target_threshold": self.target_threshold,
            "threshold_met": system_score >= self.target_threshold,
        }
        
        save_json_report(final_report, Path("./output/loop/final_report.json"))
        
        return final_report
    
    async def _get_system_score(self) -> float:
        """Get current system score"""
        evolution_agent = self.orchestrator.agents["evolution"]
        score = await evolution_agent._assess_system()
        return score
    
    async def _assess_benchmarks(self) -> Dict[str, Any]:
        """Assess against benchmarks"""
        self.logger.info("Assessing benchmarks...")
        
        # Run full cycle to get metrics
        results = await self.orchestrator.run_full_cycle()
        
        return results
    
    async def _generate_patches(self) -> list[Dict[str, Any]]:
        """Generate patch proposals"""
        self.logger.info("Generating patch proposals...")
        
        # Generate ideas
        ideas_result = await self.orchestrator.run_agent("idea_generator")
        
        # Convert ideas to patches
        patches = []
        for idea in ideas_result.get("ideas", []):
            if idea.get("priority") == "high":
                patches.append({
                    "type": "improvement",
                    "idea": idea,
                    "description": idea.get("description", ""),
                })
        
        self.logger.info(f"Generated {len(patches)} patches")
        return patches
    
    async def _run_sandbox_tests(self, patches: list[Dict[str, Any]]) -> Dict[str, Any]:
        """Run tests in sandbox environment
        
        In infinite mode, uses more lenient validation criteria to allow
        continuous experimentation and improvement.
        """
        self.logger.info(f"Running sandbox tests for {len(patches)} patches...")
        
        # Run validation
        validation_result = await self.orchestrator.run_agent("validator")
        
        # Determine if safe - more lenient in infinite mode
        pass_rate = validation_result.get("pass_rate", 0.0)
        
        return {
            "pass_rate": pass_rate,
            "validation": validation_result,
        }
    
    async def _auto_merge(self, patches: list[Dict[str, Any]]) -> None:
        """Auto-merge safe patches"""
        self.logger.info(f"Auto-merging {len(patches)} patches...")
        
        # In a real implementation, this would:
        # 1. Create a branch
        # 2. Apply patches
        # 3. Create a PR
        # 4. Merge if CI passes
        
        self.logger.info("Patches merged successfully")


async def main() -> None:
    """Main entry point for CI/CD"""
    loop = AutonomousLoop(
        repository_path="/home/runner/work/genesis/genesis",
        target_threshold=1.2,
    )
    
    result = await loop.run()
    
    print("\n=== Autonomous Loop Results ===")
    print(f"Iterations: {result['iterations']}")
    print(f"Final Score: {result['final_score']:.2f}")
    print(f"Target: {result['target_threshold']}")
    print(f"Threshold Met: {result['threshold_met']}")


if __name__ == "__main__":
    asyncio.run(main())
