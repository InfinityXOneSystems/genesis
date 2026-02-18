"""DeploymentAgent - Handles deployment and rollback operations"""

from typing import Any, Dict, List, Optional
from genesis.agents.base import BaseAgent, AgentContext


class DeploymentAgent(BaseAgent):
    """Agent responsible for deployment operations"""
    
    def __init__(self, context: AgentContext):
        super().__init__("DeploymentAgent", context)
        self.deployments = []
    
    async def execute(self) -> Dict[str, Any]:
        """Execute deployment operations"""
        self.status = "deploying"
        self.log_action("start_deployment", {})
        
        # Check if safe to deploy
        validation = self.context.get_latest_memory("validation_results")
        if not self._is_safe_to_deploy(validation):
            self.status = "blocked"
            return {
                "status": "blocked",
                "reason": "validation_failed",
            }
        
        # Execute deployment
        deployment_result = await self._deploy()
        
        # Monitor deployment
        health_check = await self._health_check()
        
        if not health_check["healthy"]:
            # Rollback on failure
            await self._rollback()
            self.status = "rolled_back"
            return {
                "status": "rolled_back",
                "reason": "health_check_failed",
            }
        
        self.log_metric("deployment_success_rate", 1.0)
        self.status = "completed"
        
        return {
            "status": "success",
            "deployment_id": deployment_result["id"],
            "health": health_check,
        }
    
    def _is_safe_to_deploy(self, validation: Optional[Dict[str, Any]]) -> bool:
        """Check if it's safe to deploy"""
        if not validation:
            return False
        
        # Check validation criteria
        pass_rate = validation.get("pass_rate", 0.0)
        security_issues = validation.get("security_scan", {}).get("vulnerabilities_found", 0)
        
        return pass_rate >= 0.95 and security_issues == 0
    
    async def _deploy(self) -> Dict[str, Any]:
        """Execute deployment"""
        self.log_action("deploy", {"target": "production"})
        
        deployment = {
            "id": f"deploy-{len(self.deployments) + 1}",
            "timestamp": "2024-01-01T00:00:00Z",
            "status": "deployed",
            "strategy": "rolling",
        }
        
        self.deployments.append(deployment)
        
        return deployment
    
    async def _health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        self.log_action("health_check", {})
        
        # Simulate health check
        return {
            "healthy": True,
            "services": {
                "api": "healthy",
                "database": "healthy",
                "cache": "healthy",
            },
            "response_time_ms": 150,
        }
    
    async def _rollback(self) -> Dict[str, Any]:
        """Rollback deployment"""
        self.log_action("rollback", {})
        
        if self.deployments:
            self.deployments[-1]["status"] = "rolled_back"
        
        return {
            "status": "success",
            "action": "rollback",
        }
    
    def canary_deploy(self, percentage: int = 10) -> Dict[str, Any]:
        """Deploy to a percentage of infrastructure (canary deployment)"""
        self.log_action("canary_deploy", {"percentage": percentage})
        
        return {
            "strategy": "canary",
            "percentage": percentage,
            "status": "monitoring",
        }
