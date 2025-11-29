"""
Google Agent Development Kit (ADK) Stock Analytics Agents

This module implements a three-layer agent architecture for stock analysis:
- Layer 1: DataAgent (fetches stock data from Yahoo Finance and MarketAux)
- Layer 2: RatioAgent, ValuationAgent, RiskAnalysisAgent (run in parallel)
- Layer 3: PresentationAgent (generates reports)

The agents are orchestrated using SequentialAgent and ParallelAgent.

Also includes:
- Data utilities (Yahoo Finance, MarketAux clients, DataFetcher)
- Gemini AI agents (Conversational, Summarization, News analysis)
"""

from .orchestrator import StockAnalyticsOrchestrator, run_stock_analysis
from .data_agent import DataAgent
from .ratio_agent import RatioAgent
from .valuation_agent import ValuationAgent
from .risk_agent import RiskAnalysisAgent
from .presentation_agent import PresentationAgent
from .logging_monitor import AgentMonitor, setup_agent_logging

__all__ = [
    'StockAnalyticsOrchestrator',
    'run_stock_analysis',
    'DataAgent',
    'RatioAgent',
    'ValuationAgent',
    'RiskAnalysisAgent',
    'PresentationAgent',
    'AgentMonitor',
    'setup_agent_logging',
]
