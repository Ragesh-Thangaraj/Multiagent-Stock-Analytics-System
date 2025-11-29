"""
Logging and Monitoring System for ADK Agents

This module provides comprehensive logging and monitoring for agent performance,
including structured logging, metrics collection, and performance auditing.
"""

import logging
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict, field
from pathlib import Path
from contextlib import contextmanager
import threading

logger = logging.getLogger(__name__)


@dataclass
class AgentMetrics:
    """Metrics for a single agent execution."""
    agent_name: str
    operation: str
    start_time: float
    end_time: float = 0.0
    duration_ms: float = 0.0
    status: str = "pending"
    input_size: int = 0
    output_size: int = 0
    error_message: Optional[str] = None
    metrics_calculated: int = 0
    metrics_successful: int = 0
    
    def complete(self, status: str = "success", error: Optional[str] = None):
        """Mark the execution as complete."""
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000
        self.status = status
        self.error_message = error


@dataclass
class PipelineMetrics:
    """Metrics for the entire analysis pipeline."""
    pipeline_id: str
    ticker: str
    start_time: float
    end_time: float = 0.0
    total_duration_ms: float = 0.0
    status: str = "pending"
    agent_metrics: List[AgentMetrics] = field(default_factory=list)
    layer1_duration_ms: float = 0.0
    layer2_duration_ms: float = 0.0
    layer3_duration_ms: float = 0.0
    total_metrics_calculated: int = 0
    total_metrics_successful: int = 0
    
    def complete(self, status: str = "success"):
        """Mark the pipeline as complete."""
        self.end_time = time.time()
        self.total_duration_ms = (self.end_time - self.start_time) * 1000
        self.status = status
        
        for agent in self.agent_metrics:
            self.total_metrics_calculated += agent.metrics_calculated
            self.total_metrics_successful += agent.metrics_successful


class AgentMonitor:
    """
    Central monitoring system for ADK agents.
    Tracks performance, logs events, and provides auditing capabilities.
    """
    
    def __init__(self, log_dir: str = "logs/agents"):
        """
        Initialize the Agent Monitor.
        
        Args:
            log_dir: Directory for storing log files
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.current_pipeline: Optional[PipelineMetrics] = None
        self.pipeline_history: List[PipelineMetrics] = []
        self._lock = threading.Lock()
        
        self._setup_file_logging()
        
    def _setup_file_logging(self):
        """Set up file-based logging for agents."""
        log_file = self.log_dir / f"agent_log_{datetime.now().strftime('%Y%m%d')}.log"
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        
        formatter = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        root_logger = logging.getLogger('src.adk_agents')
        root_logger.addHandler(file_handler)
        root_logger.setLevel(logging.DEBUG)
    
    def start_pipeline(self, ticker: str) -> str:
        """
        Start tracking a new analysis pipeline.
        
        Args:
            ticker: The stock ticker being analyzed
            
        Returns:
            str: The pipeline ID
        """
        pipeline_id = f"{ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        with self._lock:
            self.current_pipeline = PipelineMetrics(
                pipeline_id=pipeline_id,
                ticker=ticker,
                start_time=time.time(),
            )
        
        logger.info(f"Pipeline started: {pipeline_id}")
        self._log_event("pipeline_start", {"pipeline_id": pipeline_id, "ticker": ticker})
        
        return pipeline_id
    
    def end_pipeline(self, status: str = "success"):
        """
        End the current pipeline and log final metrics.
        
        Args:
            status: The final status of the pipeline
        """
        with self._lock:
            if self.current_pipeline:
                self.current_pipeline.complete(status)
                self.pipeline_history.append(self.current_pipeline)
                
                self._log_event("pipeline_end", {
                    "pipeline_id": self.current_pipeline.pipeline_id,
                    "status": status,
                    "duration_ms": self.current_pipeline.total_duration_ms,
                    "metrics_success_rate": (
                        self.current_pipeline.total_metrics_successful / 
                        max(self.current_pipeline.total_metrics_calculated, 1)
                    ) * 100,
                })
                
                logger.info(
                    f"Pipeline completed: {self.current_pipeline.pipeline_id} "
                    f"in {self.current_pipeline.total_duration_ms:.0f}ms "
                    f"({self.current_pipeline.total_metrics_successful}/"
                    f"{self.current_pipeline.total_metrics_calculated} metrics)"
                )
                
                self._save_pipeline_metrics(self.current_pipeline)
                self.current_pipeline = None
    
    @contextmanager
    def track_agent(self, agent_name: str, operation: str):
        """
        Context manager to track agent execution.
        
        Args:
            agent_name: Name of the agent
            operation: The operation being performed
            
        Yields:
            AgentMetrics: The metrics object for this execution
        """
        metrics = AgentMetrics(
            agent_name=agent_name,
            operation=operation,
            start_time=time.time(),
        )
        
        logger.debug(f"Agent {agent_name} starting: {operation}")
        
        try:
            yield metrics
            metrics.complete("success")
        except Exception as e:
            metrics.complete("error", str(e))
            logger.error(f"Agent {agent_name} error: {e}")
            raise
        finally:
            with self._lock:
                if self.current_pipeline:
                    self.current_pipeline.agent_metrics.append(metrics)
            
            self._log_event("agent_execution", {
                "agent_name": agent_name,
                "operation": operation,
                "status": metrics.status,
                "duration_ms": metrics.duration_ms,
                "metrics_calculated": metrics.metrics_calculated,
                "metrics_successful": metrics.metrics_successful,
            })
            
            logger.debug(
                f"Agent {agent_name} completed: {operation} "
                f"in {metrics.duration_ms:.0f}ms [{metrics.status}]"
            )
    
    def record_layer_timing(self, layer: int, duration_ms: float):
        """
        Record timing for a pipeline layer.
        
        Args:
            layer: Layer number (1, 2, or 3)
            duration_ms: Duration in milliseconds
        """
        with self._lock:
            if self.current_pipeline:
                if layer == 1:
                    self.current_pipeline.layer1_duration_ms = duration_ms
                elif layer == 2:
                    self.current_pipeline.layer2_duration_ms = duration_ms
                elif layer == 3:
                    self.current_pipeline.layer3_duration_ms = duration_ms
        
        logger.info(f"Layer {layer} completed in {duration_ms:.0f}ms")
    
    def _log_event(self, event_type: str, data: Dict[str, Any]):
        """Log a structured event to the events file."""
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "data": data,
        }
        
        events_file = self.log_dir / f"events_{datetime.now().strftime('%Y%m%d')}.jsonl"
        
        with open(events_file, 'a') as f:
            f.write(json.dumps(event) + '\n')
    
    def _save_pipeline_metrics(self, pipeline: PipelineMetrics):
        """Save pipeline metrics to a JSON file."""
        metrics_file = self.log_dir / f"pipeline_{pipeline.pipeline_id}.json"
        
        with open(metrics_file, 'w') as f:
            json.dump(asdict(pipeline), f, indent=2, default=str)
    
    def get_pipeline_summary(self) -> Dict[str, Any]:
        """Get a summary of pipeline history."""
        if not self.pipeline_history:
            return {"total_pipelines": 0}
        
        durations = [p.total_duration_ms for p in self.pipeline_history]
        success_count = sum(1 for p in self.pipeline_history if p.status == "success")
        
        return {
            "total_pipelines": len(self.pipeline_history),
            "success_rate": (success_count / len(self.pipeline_history)) * 100,
            "avg_duration_ms": sum(durations) / len(durations),
            "min_duration_ms": min(durations),
            "max_duration_ms": max(durations),
            "total_metrics_calculated": sum(p.total_metrics_calculated for p in self.pipeline_history),
        }
    
    def get_agent_performance(self, agent_name: str) -> Dict[str, Any]:
        """Get performance summary for a specific agent."""
        agent_executions = []
        
        for pipeline in self.pipeline_history:
            for agent in pipeline.agent_metrics:
                if agent.agent_name == agent_name:
                    agent_executions.append(agent)
        
        if not agent_executions:
            return {"agent_name": agent_name, "executions": 0}
        
        durations = [a.duration_ms for a in agent_executions]
        success_count = sum(1 for a in agent_executions if a.status == "success")
        
        return {
            "agent_name": agent_name,
            "executions": len(agent_executions),
            "success_rate": (success_count / len(agent_executions)) * 100,
            "avg_duration_ms": sum(durations) / len(durations),
            "min_duration_ms": min(durations),
            "max_duration_ms": max(durations),
        }
    
    def save_metrics_to_disk(self, ticker: str, pipeline_id: str):
        """
        Save all metrics for an analysis to disk.
        
        Args:
            ticker: The stock ticker that was analyzed
            pipeline_id: The pipeline ID
        """
        metrics_file = self.log_dir / f"metrics_{pipeline_id}.json"
        
        metrics_data = {
            "ticker": ticker,
            "pipeline_id": pipeline_id,
            "timestamp": datetime.now().isoformat(),
            "pipeline_summary": self.get_pipeline_summary(),
            "agent_performance": {
                "DataAgent": self.get_agent_performance("DataAgent"),
                "RatioAgent": self.get_agent_performance("RatioAgent"),
                "ValuationAgent": self.get_agent_performance("ValuationAgent"),
                "RiskAnalysisAgent": self.get_agent_performance("RiskAnalysisAgent"),
                "PresentationAgent": self.get_agent_performance("PresentationAgent"),
            },
        }
        
        try:
            with open(metrics_file, 'w') as f:
                json.dump(metrics_data, f, indent=2, default=str)
            
            logger.info(f"Metrics saved to {metrics_file}")
        except Exception as e:
            logger.error(f"Failed to save metrics to disk: {e}")


_global_monitor: Optional[AgentMonitor] = None


def setup_agent_logging(log_dir: str = "logs/agents") -> AgentMonitor:
    """
    Set up and return the global agent monitor.
    
    Args:
        log_dir: Directory for storing log files
        
    Returns:
        AgentMonitor: The global monitor instance
    """
    global _global_monitor
    
    if _global_monitor is None:
        _global_monitor = AgentMonitor(log_dir=log_dir)
        logger.info("Agent monitoring system initialized")
    
    return _global_monitor


def get_monitor() -> AgentMonitor:
    """Get the global agent monitor instance."""
    global _global_monitor
    
    if _global_monitor is None:
        _global_monitor = setup_agent_logging()
    
    return _global_monitor
