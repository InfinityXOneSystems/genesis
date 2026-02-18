"""Core utilities and shared functionality"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from rich.console import Console
from rich.logging import RichHandler

console = Console()


def setup_logging(level: str = "INFO", log_file: Optional[Path] = None) -> logging.Logger:
    """Setup structured logging with rich output"""
    handlers = [RichHandler(console=console, rich_tracebacks=True)]
    
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        handlers.append(file_handler)
    
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(message)s",
        handlers=handlers,
    )
    
    return logging.getLogger("genesis")


def save_json_report(data: Dict[str, Any], output_path: Path) -> None:
    """Save a JSON report with metadata"""
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "version": "0.1.0",
        "data": data,
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    console.print(f"[green]✓[/green] Report saved to {output_path}")


def load_json_report(input_path: Path) -> Dict[str, Any]:
    """Load a JSON report"""
    with open(input_path, 'r') as f:
        return json.load(f)


class StructuredLogger:
    """Structured logger for agent actions"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(f"genesis.{name}")
        self.name = name
    
    def log_action(self, action: str, details: Dict[str, Any]) -> None:
        """Log a structured action"""
        log_data = {
            "agent": self.name,
            "action": action,
            "timestamp": datetime.utcnow().isoformat(),
            **details,
        }
        self.logger.info(json.dumps(log_data))
    
    def log_metric(self, metric: str, value: float, context: Optional[Dict[str, Any]] = None) -> None:
        """Log a metric"""
        log_data = {
            "agent": self.name,
            "metric": metric,
            "value": value,
            "timestamp": datetime.utcnow().isoformat(),
            **(context or {}),
        }
        self.logger.info(json.dumps(log_data))
