"""MemoryAgent - Maintains context using RAG (Retrieval-Augmented Generation)"""

from typing import Any, Dict, List, Optional
from datetime import datetime, UTC
from genesis.agents.base import BaseAgent, AgentContext


class MemoryAgent(BaseAgent):
    """Agent responsible for memory management and RAG"""
    
    def __init__(self, context: AgentContext):
        super().__init__("MemoryAgent", context)
        self.memory_store: List[Dict[str, Any]] = []
        self.embeddings_cache: Dict[str, List[float]] = {}
    
    async def execute(self) -> Dict[str, Any]:
        """Manage memory and provide context retrieval"""
        self.status = "processing"
        self.log_action("start_memory_management", {})
        
        # Update memory from context
        self._update_memory_store()
        
        # Optimize memory storage
        self._optimize_memory()
        
        self.log_metric("memory_entries", len(self.memory_store))
        self.status = "completed"
        
        return {
            "status": "success",
            "memory_size": len(self.memory_store),
            "cache_size": len(self.embeddings_cache),
        }
    
    def _update_memory_store(self) -> None:
        """Update memory store from context"""
        for entry in self.context.memory:
            if entry not in self.memory_store:
                self.memory_store.append(entry)
    
    def _optimize_memory(self) -> None:
        """Optimize memory by removing old or redundant entries"""
        # Keep only recent entries (e.g., last 1000)
        if len(self.memory_store) > 1000:
            self.memory_store = self.memory_store[-1000:]
    
    def store(self, key: str, value: Any, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Store information in memory"""
        entry = {
            "key": key,
            "value": value,
            "timestamp": datetime.now(UTC).isoformat(),
            "metadata": metadata or {},
        }
        
        self.memory_store.append(entry)
        self.context.add_memory(key, value)
        
        self.log_action("store_memory", {"key": key})
    
    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Retrieve relevant information from memory"""
        self.log_action("retrieve_memory", {"query": query, "top_k": top_k})
        
        # Simple keyword-based retrieval
        # In production, this would use embeddings and vector similarity
        results = []
        query_lower = query.lower()
        
        for entry in reversed(self.memory_store):
            key = str(entry.get("key", "")).lower()
            value = str(entry.get("value", "")).lower()
            
            if query_lower in key or query_lower in value:
                results.append(entry)
                if len(results) >= top_k:
                    break
        
        return results
    
    def get_context_summary(self) -> Dict[str, Any]:
        """Get a summary of current context"""
        return {
            "total_entries": len(self.memory_store),
            "recent_keys": [
                entry["key"]
                for entry in self.memory_store[-10:]
            ],
            "memory_types": list(set(
                entry.get("metadata", {}).get("type", "unknown")
                for entry in self.memory_store
            )),
        }
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text (placeholder for actual implementation)"""
        # In production, this would use an embedding model
        # For now, return a simple hash-based representation
        if text in self.embeddings_cache:
            return self.embeddings_cache[text]
        
        # Placeholder: create a simple embedding
        embedding = [float(ord(c)) for c in text[:128]]
        embedding = embedding + [0.0] * (128 - len(embedding))
        
        self.embeddings_cache[text] = embedding
        return embedding
