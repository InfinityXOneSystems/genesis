"""Base Agent class and common agent functionality"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, UTC
from genesis.utils import StructuredLogger


@dataclass
class AgentContext:
    """Shared context for agents"""
    repository_path: str
    analysis_results: Dict[str, Any] = field(default_factory=dict)
    benchmarks: Dict[str, Any] = field(default_factory=dict)
    memory: List[Dict[str, Any]] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)
    
    def add_memory(self, key: str, value: Any) -> None:
        """Add to shared memory"""
        self.memory.append({
            "timestamp": datetime.now(UTC).isoformat(),
            "key": key,
            "value": value,
        })
    
    def get_latest_memory(self, key: str) -> Optional[Any]:
        """Get most recent memory entry for a key"""
        for entry in reversed(self.memory):
            if entry["key"] == key:
                return entry["value"]
        return None


class BaseAgent(ABC):
    """Base class for all agents in the system"""
    
    def __init__(self, name: str, context: AgentContext):
        self.name = name
        self.context = context
        self.logger = StructuredLogger(name)
        self.status = "initialized"
    
    @abstractmethod
    async def execute(self) -> Dict[str, Any]:
        """Execute the agent's primary function"""
        pass
    
    def log_action(self, action: str, details: Dict[str, Any]) -> None:
        """Log an action taken by this agent"""
        self.logger.log_action(action, details)
    
    def log_metric(self, metric: str, value: float) -> None:
        """Log a metric"""
        self.logger.log_metric(metric, value)
        self.context.metrics[f"{self.name}.{metric}"] = value
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            "name": self.name,
            "status": self.status,
            "timestamp": datetime.now(UTC).isoformat(),
        }
