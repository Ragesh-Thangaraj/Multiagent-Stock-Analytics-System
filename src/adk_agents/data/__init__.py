"""
Data fetching utilities for the Stock Analytics Agent.
Consolidates Yahoo Finance and MarketAux API clients.
"""

from src.adk_agents.data.yahoo_client import YahooFinanceClient
from src.adk_agents.data.marketaux_client import MarketAuxClient
from src.adk_agents.data.fetcher import DataFetcher

__all__ = ['YahooFinanceClient', 'MarketAuxClient', 'DataFetcher']
