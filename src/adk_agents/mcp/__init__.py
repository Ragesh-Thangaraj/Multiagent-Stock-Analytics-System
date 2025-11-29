"""
MCP (Model Context Protocol) Server for ADK Agents

This module provides secure code execution, tool calling, external API connectors,
and guardrails for the stock analytics agents.
"""

from .server import MCPServer, create_mcp_server
from .guardrails import Guardrails, SecurityPolicy

__all__ = [
    'MCPServer',
    'create_mcp_server',
    'Guardrails',
    'SecurityPolicy',
]
