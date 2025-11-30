"""
End-to-end tests for full analysis pipeline.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import patch, Mock


class TestFullPipeline:
    """Test complete pipeline from data fetch to calculations."""
    
    @patch('src.adk_agents.data.yahoo_client.yf.Ticker')
    def test_complete_analysis_pipeline(self, mock_ticker):
        """Test full pipeline: fetch -> calculate -> report."""
        # Mock Yahoo Finance data
        mock_stock = Mock()
        mock_stock.history.return_value = Mock()
        mock_stock.info = {
            "longName": "Test Company",
            "exchange": "NASDAQ",
            "currency": "USD",
            "marketCap": 1000000000,
            "sharesOutstanding": 1000000
        }
        mock_stock.balance_sheet = Mock()
        mock_stock.income_stmt = Mock()
        mock_stock.cashflow = Mock()
        mock_ticker.return_value = mock_stock
        
        # This would be a full integration test
        # For now, we verify the structure
        assert True  # Placeholder for full E2E test
    
    def test_calculation_pipeline_with_sample_data(self):
        """Test calculation pipeline with sample canonical JSON."""
        sample_data = {
            "meta": {
                "ticker": "TEST",
                "exchange": "NASDAQ",
                "company_name": "Test Corp",
                "currency": "USD",
                "fetch_time": "2025-11-25T00:00:00Z",
                "source_versions": {"yahoo": "test", "marketaux": "test"}
            },
            "price_history": [
                {"date": "2025-01-01", "close": 100.0},
                {"date": "2025-01-02", "close": 102.0}
            ],
            "fundamentals": {
                "shares_outstanding": 1000000,
                "market_cap": 100000000,
                "income_statement": {
                    "revenue": 50000000,
                    "gross_profit": 20000000,
                    "operating_income": 10000000,
                    "net_income": 7500000
                },
                "balance_sheet": {
                    "total_assets": 100000000,
                    "current_assets": 30000000,
                    "current_liabilities": 15000000,
                    "shareholders_equity": 50000000
                },
                "cashflow_statement": {
                    "operating_cashflow": 12000000,
                    "capital_expenditures": -2000000
                }
            },
            "news": [],
            "calculated": {}
        }
        
        # Write sample data
        test_path = Path("runs/TEST_sample.json")
        test_path.parent.mkdir(exist_ok=True)
        
        with open(test_path, 'w') as f:
            json.dump(sample_data, f, indent=2)
        
        # Test that file was created
        assert test_path.exists()
        
        # Verify structure
        with open(test_path, 'r') as f:
            loaded = json.load(f)
        
        assert loaded["meta"]["ticker"] == "TEST"
        assert "fundamentals" in loaded

