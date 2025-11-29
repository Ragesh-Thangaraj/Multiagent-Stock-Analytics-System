"""
MCP Server for ADK Agents

This module provides the Model Context Protocol server for secure code execution,
tool calling, and external API management.
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime
import json

from .guardrails import Guardrails, SecurityPolicy, RiskLevel

logger = logging.getLogger(__name__)


@dataclass
class ToolDefinition:
    """Definition of a callable tool."""
    name: str
    description: str
    function: Callable
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    risk_level: RiskLevel = RiskLevel.LOW
    requires_auth: bool = False


@dataclass
class APIConnector:
    """External API connector configuration."""
    name: str
    base_url: str
    auth_type: str = "api_key"
    rate_limit: int = 100
    timeout_seconds: float = 30.0
    headers: Dict[str, str] = field(default_factory=dict)


class MCPServer:
    """
    MCP Server for secure tool execution and API management.
    
    Provides:
    - Secure code execution with sandboxing
    - Tool registration and calling
    - External API connectors with rate limiting
    - Request/response logging
    - Guardrails enforcement
    """
    
    def __init__(
        self,
        policy: Optional[SecurityPolicy] = None,
        enable_logging: bool = True,
    ):
        """
        Initialize the MCP Server.
        
        Args:
            policy: Security policy for guardrails
            enable_logging: Whether to log all operations
        """
        self.guardrails = Guardrails(policy)
        self.tools: Dict[str, ToolDefinition] = {}
        self.api_connectors: Dict[str, APIConnector] = {}
        self.enable_logging = enable_logging
        self.execution_history: List[Dict[str, Any]] = []
        
        self._register_default_connectors()
        
        logger.info("MCP Server initialized")
    
    def _register_default_connectors(self):
        """Register default API connectors."""
        self.register_api_connector(APIConnector(
            name="yahoo_finance",
            base_url="https://query1.finance.yahoo.com",
            auth_type="none",
            rate_limit=100,
            timeout_seconds=30.0,
        ))
        
        self.register_api_connector(APIConnector(
            name="marketaux",
            base_url="https://api.marketaux.com/v1",
            auth_type="api_key",
            rate_limit=100,
            timeout_seconds=30.0,
        ))
    
    def register_tool(self, tool: ToolDefinition):
        """
        Register a tool for execution.
        
        Args:
            tool: The tool definition to register
        """
        self.tools[tool.name] = tool
        logger.debug(f"Tool registered: {tool.name}")
    
    def register_api_connector(self, connector: APIConnector):
        """
        Register an external API connector.
        
        Args:
            connector: The API connector configuration
        """
        self.api_connectors[connector.name] = connector
        logger.debug(f"API connector registered: {connector.name}")
    
    def execute_tool(
        self,
        tool_name: str,
        inputs: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute a registered tool with security checks.
        
        Args:
            tool_name: Name of the tool to execute
            inputs: Input parameters for the tool
            context: Optional execution context
            
        Returns:
            dict: Execution result with status and output
        """
        start_time = datetime.now()
        
        if tool_name not in self.tools:
            return {
                "status": "error",
                "error": f"Tool not found: {tool_name}",
            }
        
        tool = self.tools[tool_name]
        
        is_valid, error_msg = self.guardrails.validate_input(inputs)
        if not is_valid:
            logger.warning(f"Input validation failed for {tool_name}: {error_msg}")
            return {
                "status": "error",
                "error": f"Input validation failed: {error_msg}",
            }
        
        if not self.guardrails.check_rate_limit(tool_name):
            return {
                "status": "error",
                "error": "Rate limit exceeded",
            }
        
        try:
            result = tool.function(**inputs)
            
            filtered_result = self.guardrails.filter_output(
                result if isinstance(result, dict) else {"result": result}
            )
            
            execution_record = {
                "tool_name": tool_name,
                "start_time": start_time.isoformat(),
                "end_time": datetime.now().isoformat(),
                "status": "success",
                "risk_level": tool.risk_level.value,
            }
            
            if self.enable_logging:
                self.execution_history.append(execution_record)
            
            return {
                "status": "success",
                "output": filtered_result,
            }
            
        except Exception as e:
            logger.error(f"Tool execution error for {tool_name}: {e}")
            
            if self.enable_logging:
                self.execution_history.append({
                    "tool_name": tool_name,
                    "start_time": start_time.isoformat(),
                    "end_time": datetime.now().isoformat(),
                    "status": "error",
                    "error": str(e),
                })
            
            return {
                "status": "error",
                "error": str(e),
            }
    
    async def execute_tool_async(
        self,
        tool_name: str,
        inputs: Dict[str, Any],
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Execute a tool asynchronously with timeout.
        
        Args:
            tool_name: Name of the tool to execute
            inputs: Input parameters for the tool
            timeout: Execution timeout in seconds
            
        Returns:
            dict: Execution result with status and output
        """
        timeout = timeout or self.guardrails.policy.max_calculation_timeout_seconds
        
        try:
            loop = asyncio.get_event_loop()
            result = await asyncio.wait_for(
                loop.run_in_executor(None, lambda: self.execute_tool(tool_name, inputs)),
                timeout=timeout
            )
            return result
            
        except asyncio.TimeoutError:
            logger.error(f"Tool execution timeout for {tool_name}")
            return {
                "status": "error",
                "error": f"Execution timeout after {timeout} seconds",
            }
    
    def get_api_connector(self, name: str) -> Optional[APIConnector]:
        """Get an API connector by name."""
        return self.api_connectors.get(name)
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Get statistics about tool executions."""
        if not self.execution_history:
            return {"total_executions": 0}
        
        success_count = sum(1 for e in self.execution_history if e.get('status') == 'success')
        
        tool_counts: Dict[str, int] = {}
        for execution in self.execution_history:
            tool_name = execution.get('tool_name', 'unknown')
            tool_counts[tool_name] = tool_counts.get(tool_name, 0) + 1
        
        return {
            "total_executions": len(self.execution_history),
            "success_count": success_count,
            "error_count": len(self.execution_history) - success_count,
            "success_rate": (success_count / len(self.execution_history)) * 100,
            "executions_by_tool": tool_counts,
        }
    
    def clear_execution_history(self):
        """Clear the execution history."""
        self.execution_history.clear()
        logger.debug("Execution history cleared")
    
    def export_execution_log(self, filepath: str):
        """Export execution history to a JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.execution_history, f, indent=2)
        logger.info(f"Execution log exported to {filepath}")


_global_mcp_server: Optional[MCPServer] = None


def create_mcp_server(
    policy: Optional[SecurityPolicy] = None,
    enable_logging: bool = True,
) -> MCPServer:
    """
    Create and return the global MCP server instance.
    
    Args:
        policy: Security policy for guardrails
        enable_logging: Whether to log all operations
        
    Returns:
        MCPServer: The MCP server instance
    """
    global _global_mcp_server
    
    if _global_mcp_server is None:
        _global_mcp_server = MCPServer(policy=policy, enable_logging=enable_logging)
    
    return _global_mcp_server


def get_mcp_server() -> MCPServer:
    """Get the global MCP server instance."""
    global _global_mcp_server
    
    if _global_mcp_server is None:
        _global_mcp_server = create_mcp_server()
    
    return _global_mcp_server
