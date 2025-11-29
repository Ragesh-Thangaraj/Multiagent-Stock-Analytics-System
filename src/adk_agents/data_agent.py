"""
Data Agent - Layer 1 of the Stock Analytics Pipeline

This agent is responsible for fetching stock data from Yahoo Finance and MarketAux APIs.
It stores the canonical data in the session state using output_key for downstream agents.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from google.adk.agents import LlmAgent
from google.genai import types

from .tools.data_tools import fetch_yahoo_finance_data, fetch_marketaux_news, get_stock_info

logger = logging.getLogger(__name__)


DATA_AGENT_INSTRUCTION = """You are a Data Collection Agent specializing in financial data retrieval.

Your primary responsibility is to fetch comprehensive stock data for analysis. When given a stock ticker:

1. ALWAYS use the fetch_yahoo_finance_data tool to get:
   - Company metadata (name, sector, industry)
   - Price history for the specified period
   - Financial fundamentals (income statement, balance sheet, cash flow)
   - Precomputed financial ratios from Yahoo Finance

2. Use fetch_marketaux_news to get recent news articles about the company

3. Validate that all data was retrieved successfully before proceeding

CRITICAL: Your final response MUST be valid JSON in this exact format:
```json
{
  "status": "success",
  "ticker": "SYMBOL",
  "company_name": "Company Name",
  "sector": "Sector",
  "industry": "Industry",
  "price_history_days": 252,
  "news_count": 10,
  "has_fundamentals": true,
  "has_info": true
}
```

If data fetch fails, return:
```json
{
  "status": "error",
  "ticker": "SYMBOL",
  "error_message": "Description of error"
}
```

IMPORTANT:
- Always convert lowercase tickers to uppercase
- Handle errors gracefully and report any data retrieval issues
- Your output MUST be valid JSON only - no additional text
"""


class DataAgent:
    """
    Data Agent for Layer 1 of the stock analytics pipeline.
    Fetches stock data from Yahoo Finance and MarketAux APIs.
    """
    
    def __init__(self, model: str = "gemini-2.0-flash"):
        """
        Initialize the Data Agent.
        
        Args:
            model: The Gemini model to use for the agent.
        """
        self.model = model
        self.agent = self._create_agent()
        self.last_fetch_data: Optional[Dict[str, Any]] = None
        self.last_fetch_timestamp: Optional[str] = None
        
    def _create_agent(self) -> LlmAgent:
        """Create the LLM agent with data fetching tools."""
        return LlmAgent(
            name="DataAgent",
            model=self.model,
            instruction=DATA_AGENT_INSTRUCTION,
            description="Fetches comprehensive stock data from Yahoo Finance and MarketAux APIs for financial analysis.",
            tools=[
                fetch_yahoo_finance_data,
                fetch_marketaux_news,
                get_stock_info,
            ],
            output_key="canonical_data",
        )
    
    def fetch_stock_data(self, ticker: str, period_days: int = 252) -> Dict[str, Any]:
        """
        Fetch comprehensive stock data for a given ticker.
        
        This is a direct data fetch method that bypasses the LLM for efficiency.
        Use this when you want to fetch data without conversational interaction.
        
        Args:
            ticker: The stock ticker symbol (e.g., "AAPL", "MSFT")
            period_days: Number of trading days of price history to fetch
            
        Returns:
            dict: Comprehensive stock data including:
                - meta: Company metadata
                - price_history: Historical price data
                - fundamentals: Financial statements
                - info: Precomputed ratios
                - news: Recent news articles
        """
        ticker = ticker.upper().strip()
        
        if period_days is None:
            period_days = 252
        try:
            period_days = int(period_days)
        except (TypeError, ValueError):
            period_days = 252
        
        logger.info(f"DataAgent: Fetching data for {ticker}...")
        
        yahoo_data = fetch_yahoo_finance_data(ticker, period_days)
        
        if yahoo_data.get('status') == 'error':
            logger.error(f"DataAgent: Failed to fetch Yahoo Finance data for {ticker}")
            return {
                "status": "error",
                "error_message": yahoo_data.get('error_message', 'Unknown error'),
                "ticker": ticker,
            }
        
        news_data = fetch_marketaux_news(ticker, limit=10)
        
        meta = yahoo_data.get('meta', {})
        canonical_data = {
            "meta": {
                "ticker": ticker,
                "company_name": meta.get('company_name', ticker),
                "sector": meta.get('sector', 'Unknown'),
                "industry": meta.get('industry', 'Unknown'),
                "exchange": meta.get('exchange', 'N/A'),
                "currency": meta.get('currency', 'USD'),
                "market_cap": meta.get('market_cap'),
                "fetch_timestamp": datetime.now().isoformat(),
                "period_days": period_days,
            },
            "price_history": yahoo_data.get('price_history', []),
            "fundamentals": yahoo_data.get('fundamentals', {}),
            "info": yahoo_data.get('info', {}),
            "news": news_data.get('articles', []) if news_data.get('status') == 'success' else [],
            "status": "success",
        }
        
        self.last_fetch_data = canonical_data
        self.last_fetch_timestamp = canonical_data['meta']['fetch_timestamp']
        
        logger.info(f"DataAgent: Successfully fetched data for {ticker}")
        logger.info(f"  - Price history: {len(canonical_data['price_history'])} days")
        logger.info(f"  - News articles: {len(canonical_data['news'])}")
        
        return canonical_data
    
    def get_llm_agent(self) -> LlmAgent:
        """Get the underlying LLM agent for use in orchestration."""
        return self.agent
    
    def validate_data(self, data: Dict[str, Any]) -> Dict[str, bool]:
        """
        Validate that required data fields are present.
        
        Args:
            data: The canonical data dictionary
            
        Returns:
            dict: Validation results for each data category
        """
        validation = {
            "meta": bool(data.get('meta', {}).get('ticker')),
            "price_history": len(data.get('price_history', [])) >= 20,
            "fundamentals": bool(data.get('fundamentals', {}).get('income_statement')),
            "info": bool(data.get('info')),
            "news": True,
        }
        
        return validation


def create_data_agent(model: str = "gemini-2.0-flash") -> DataAgent:
    """
    Factory function to create a Data Agent.
    
    Args:
        model: The Gemini model to use
        
    Returns:
        DataAgent: A configured Data Agent instance
    """
    return DataAgent(model=model)
