"""
Integration tests for data fetching layer.
"""

import pytest
from unittest.mock import Mock, patch
from src.adk_agents.data.yahoo_client import YahooFinanceClient
from src.adk_agents.data.fetcher import DataFetcher


class TestYahooFinanceIntegration:
    """Test Yahoo Finance client integration."""
    
    @patch('yfinance.Ticker')
    def test_fetch_stock_data_success(self, mock_ticker):
        """Test successful stock data fetch."""
        # Mock yfinance Ticker
        mock_stock = Mock()
        mock_stock.history.return_value = Mock()
        mock_stock.info = {
            "longName": "Apple Inc.",
            "exchange": "NASDAQ",
            "currency": "USD",
            "marketCap": 3000000000000,
            "sharesOutstanding": 15000000000
        }
        mock_ticker.return_value = mock_stock
        
        client = YahooFinanceClient()
        data = client.fetch_stock_data("AAPL")
        
        assert data["success"] is True
        assert data["ticker"] == "AAPL"
        assert data["company_name"] == "Apple Inc."
    
    def test_fetch_stock_data_invalid_ticker(self):
        """Test handling of invalid ticker."""
        client = YahooFinanceClient()
        data = client.fetch_stock_data("INVALID_TICKER_XYZ")
        
        # Should handle gracefully
        assert "success" in data


class TestDataFetcherIntegration:
    """Test DataFetcher integration."""
    
    @patch('src.adk_agents.data.fetcher.YahooFinanceClient')
    @patch('src.adk_agents.data.fetcher.MarketAuxClient')
    def test_fetch_and_save_creates_canonical_json(self, mock_marketaux, mock_yahoo):
        """Test that fetcher creates canonical JSON structure."""
        # Mock Yahoo client
        mock_yahoo_instance = Mock()
        mock_yahoo_instance.fetch_stock_data.return_value = {
            "success": True,
            "ticker": "AAPL",
            "company_name": "Apple Inc.",
            "exchange": "NASDAQ",
            "currency": "USD",
            "price_history": [],
            "fundamentals": {}
        }
        mock_yahoo_instance.fetch_news.return_value = []
        mock_yahoo.return_value = mock_yahoo_instance
        
        # Mock MarketAux client
        mock_marketaux_instance = Mock()
        mock_marketaux_instance.fetch_news.return_value = []
        mock_marketaux_instance.version = "v1"
        mock_marketaux.return_value = mock_marketaux_instance
        
        fetcher = DataFetcher()
        data = fetcher.fetch_and_save("AAPL")
        
        # Verify canonical structure
        assert "meta" in data
        assert "price_history" in data
        assert "fundamentals" in data
        assert "news" in data
        assert "calculated" in data
        
        assert data["meta"]["ticker"] == "AAPL"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
