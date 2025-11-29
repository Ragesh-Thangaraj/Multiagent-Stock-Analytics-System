"""
Unit tests for profitability calculation module.
Uses the ADK tools for ratio calculations.
"""

import pytest
import json
from src.adk_agents.tools.ratio_tools import (
    calculate_gross_margin,
    calculate_operating_margin,
    calculate_net_margin,
    calculate_roa,
    calculate_roe,
)


def calculate_profitability(data):
    """Wrapper to maintain test compatibility with new ADK tools."""
    results = {
        "gross_margin": calculate_gross_margin(data),
        "operating_margin": calculate_operating_margin(data),
        "net_margin": calculate_net_margin(data),
        "roa": calculate_roa(data),
        "roe": calculate_roe(data),
    }
    return results


class TestProfitabilityCalculations:
    """Test suite for profitability metrics."""
    
    def test_gross_margin_calculation(self):
        """Test gross margin calculation."""
        data = {
            "fundamentals": {
                "income_statement": {
                    "revenue": 100000,
                    "gross_profit": 40000
                }
            }
        }
        
        metrics = calculate_profitability(data)
        
        assert "gross_margin" in metrics
        assert metrics["gross_margin"]["value"] == 0.4
        assert metrics["gross_margin"]["formula"] == "gross_profit / revenue"
    
    def test_operating_margin_calculation(self):
        """Test operating margin calculation."""
        data = {
            "fundamentals": {
                "income_statement": {
                    "revenue": 100000,
                    "operating_income": 25000
                }
            }
        }
        
        metrics = calculate_profitability(data)
        
        assert "operating_margin" in metrics
        assert metrics["operating_margin"]["value"] == 0.25
    
    def test_net_margin_calculation(self):
        """Test net margin calculation."""
        data = {
            "fundamentals": {
                "income_statement": {
                    "revenue": 100000,
                    "net_income": 15000
                }
            }
        }
        
        metrics = calculate_profitability(data)
        
        assert "net_margin" in metrics
        assert metrics["net_margin"]["value"] == 0.15
    
    def test_roa_calculation(self):
        """Test Return on Assets calculation."""
        data = {
            "fundamentals": {
                "income_statement": {
                    "net_income": 15000
                },
                "balance_sheet": {
                    "total_assets": 200000
                }
            }
        }
        
        metrics = calculate_profitability(data)
        
        assert "roa" in metrics
        assert metrics["roa"]["value"] == 0.075
    
    def test_roe_calculation(self):
        """Test Return on Equity calculation."""
        data = {
            "fundamentals": {
                "income_statement": {
                    "net_income": 15000
                },
                "balance_sheet": {
                    "shareholders_equity": 100000
                }
            }
        }
        
        metrics = calculate_profitability(data)
        
        assert "roe" in metrics
        assert metrics["roe"]["value"] == 0.15
    
    def test_missing_data_handling(self):
        """Test handling of missing data with null_reason."""
        data = {
            "fundamentals": {
                "income_statement": {},
                "balance_sheet": {}
            }
        }
        
        metrics = calculate_profitability(data)
        
        assert metrics["gross_margin"]["value"] is None
        assert metrics["gross_margin"]["null_reason"] == "missing_revenue_or_gross_profit"
    
    def test_zero_division_handling(self):
        """Test handling of zero division."""
        data = {
            "fundamentals": {
                "income_statement": {
                    "revenue": 0,
                    "gross_profit": 40000
                }
            }
        }
        
        metrics = calculate_profitability(data)
        
        assert metrics["gross_margin"]["value"] is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
