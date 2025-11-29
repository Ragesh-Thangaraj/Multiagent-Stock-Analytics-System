"""
Data Fetcher - Layer 1 Data Orchestration

Orchestrates data fetching from multiple sources (Yahoo Finance, MarketAux)
and writes the canonical JSON schema to runs/ directory.

Output: runs/<TICKER>_<TIMESTAMP>.json
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
import logging

from src.adk_agents.data.yahoo_client import YahooFinanceClient
from src.adk_agents.data.marketaux_client import MarketAuxClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataFetcher:
    """
    Orchestrates data fetching from multiple sources and writes canonical JSON.
    """
    
    def __init__(self):
        self.yahoo_client = YahooFinanceClient()
        self.marketaux_client = MarketAuxClient()
    
    def fetch_and_save(self, ticker: str, period: str = "1y") -> Dict[str, Any]:
        """
        Fetch data from all sources and save to canonical JSON format.
        
        Args:
            ticker: Stock symbol (e.g., "AAPL")
            period: Historical period for price data (default "1y")
            
        Returns:
            Canonical JSON data structure
        """
        logger.info(f"Fetching data for {ticker}...")
        
        yahoo_data = self.yahoo_client.fetch_stock_data(ticker, period)
        
        if not yahoo_data.get("success"):
            logger.error(f"Failed to fetch Yahoo Finance data for {ticker}")
            return {
                "error": "yahoo_finance_fetch_failed",
                "details": yahoo_data.get("error")
            }
        
        market_data = self.yahoo_client.fetch_market_index("^GSPC", period)
        
        marketaux_news = self.marketaux_client.fetch_news(ticker, limit=20)
        
        yahoo_news = self.yahoo_client.fetch_news(ticker, max_items=10)
        
        all_news = marketaux_news + yahoo_news
        
        canonical_data = self._build_canonical_json(
            ticker=ticker.upper(),
            yahoo_data=yahoo_data,
            market_data=market_data,
            news=all_news
        )
        
        output_path = self._save_canonical_json(canonical_data)
        
        logger.info(f"Data saved to {output_path}")
        
        return canonical_data
    
    def _build_canonical_json(
        self,
        ticker: str,
        yahoo_data: Dict[str, Any],
        market_data: Dict[str, Any],
        news: list
    ) -> Dict[str, Any]:
        """
        Build the canonical JSON schema.
        
        Schema:
        {
          "meta": { ticker, exchange, company_name, currency, fetch_time, source_versions },
          "price_history": [...],
          "market_index": { ... },
          "fundamentals": { income_statement, balance_sheet, cashflow_statement, shares_outstanding, market_cap, enterprise_value },
          "news": [...],
          "calculated": {}
        }
        """
        
        fetch_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        
        info = yahoo_data.get("info", {})
        
        canonical = {
            "meta": {
                "ticker": ticker,
                "exchange": yahoo_data.get("exchange", "UNKNOWN"),
                "company_name": yahoo_data.get("company_name", ticker),
                "currency": yahoo_data.get("currency", "USD"),
                "market_cap": info.get("marketCap"),
                "fetch_time": fetch_time,
                "source_versions": {
                    "marketaux": self.marketaux_client.version,
                    "yahoo": self.yahoo_client.version
                }
            },
            "price_history": yahoo_data.get("price_history", []),
            "market_index": market_data if market_data.get("success") else None,
            "fundamentals": yahoo_data.get("fundamentals", {}),
            "info": yahoo_data.get("info", {}),
            "news": news,
            "calculated": {}
        }
        
        self._tag_missing_fields(canonical)
        
        return canonical
    
    def _tag_missing_fields(self, data: Dict[str, Any]) -> None:
        """Tag missing or null fields with null_reason."""
        fundamentals = data.get("fundamentals", {})
        
        for section_name in ["income_statement", "balance_sheet", "cashflow_statement"]:
            section = fundamentals.get(section_name, {})
            if isinstance(section, dict):
                for key, value in section.items():
                    if value is None:
                        section[key] = {"value": None, "null_reason": "not_available_from_source"}
    
    def _save_canonical_json(self, data: Dict[str, Any]) -> str:
        """Save canonical JSON to runs directory."""
        Path("runs").mkdir(exist_ok=True)
        
        ticker = data.get("meta", {}).get("ticker", "UNKNOWN")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{ticker}_{timestamp}.json"
        output_path = Path("runs") / filename
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        return str(output_path)
