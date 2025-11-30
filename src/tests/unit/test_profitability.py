"""
Unit tests for profitability calculation module.
Uses the ADK tools for ratio calculations.
"""

import pytest
from src.adk_agents.tools.ratio_tools import (
    calculate_gross_margin,
    calculate_operating_margin,
    calculate_net_margin,
    calculate_roa,
    calculate_roe,
)

def calculate_profitability(data):
    """Wrapper matching new ADK tools."""
    return {
        "gross_margin": calculate_gross_margin(data),
        "operating_margin": calculate_operating_margin(data),
        "net_margin": calculate_net_margin(data),
        "roa": calculate_roa(data),
        "roe": calculate_roe(data),
    }

class TestProfitabilityCalculations:

    def test_gross_margin_precomputed(self):
        """Uses Yahoo precomputed gross margins."""
        data = {
            "info": {"gross_margins": 0.40}  # 40%
        }

        metrics = calculate_profitability(data)
        gm = metrics["gross_margin"]

        assert gm["status"] == "success"
        assert gm["value"] == 40.0
        assert gm["formula"] == "(Revenue - COGS) / Revenue × 100"
        assert gm["source"] == "yahoo_finance.precomputed"

    def test_gross_margin_fundamentals(self):
        """Uses fundamentals fallback structure."""
        data = {
            "fundamentals": {
                "income_statement": {
                    "2024": {
                        "Total Revenue": 100000,
                        "Gross Profit": 40000,
                    }
                }
            }
        }

        metrics = calculate_profitability(data)
        gm = metrics["gross_margin"]

        assert gm["status"] == "success"
        assert gm["value"] == 40.0
        assert gm["source"] == "calculated.fundamentals"

    def test_operating_margin_precomputed(self):
        data = {"info": {"operating_margins": 0.25}}

        metrics = calculate_profitability(data)
        om = metrics["operating_margin"]

        assert om["status"] == "success"
        assert om["value"] == 25.0

    def test_net_margin_precomputed(self):
        data = {"info": {"profit_margins": 0.15}}

        metrics = calculate_profitability(data)
        nm = metrics["net_margin"]

        assert nm["status"] == "success"
        assert nm["value"] == 15.0

    def test_roa_precomputed(self):
        data = {"info": {"return_on_assets": 0.075}}

        metrics = calculate_profitability(data)
        roa = metrics["roa"]

        assert roa["status"] == "success"
        assert roa["value"] == 7.5

    def test_roe_precomputed(self):
        data = {"info": {"return_on_equity": 0.15}}

        metrics = calculate_profitability(data)
        roe = metrics["roe"]

        assert roe["status"] == "success"
        assert roe["value"] == 15.0

    def test_missing_data_handling(self):
        """Matches new null_reason behavior."""
        data = {
            "fundamentals": {
                "income_statement": {},
                "balance_sheet": {}
            }
        }

        metrics = calculate_profitability(data)
        gm = metrics["gross_margin"]

        assert gm["value"] is None
        assert gm["null_reason"] == "Gross margin data not available"

    def test_zero_division_handling(self):
        """New code returns None because fundamentals do not provide usable format."""
        data = {
            "fundamentals": {
                "income_statement": {
                    "2024": {
                        "Total Revenue": 0,
                        "Gross Profit": 40000
                    }
                }
            }
        }

        metrics = calculate_profitability(data)
        gm = metrics["gross_margin"]

        assert gm["value"] is None
        assert gm["status"] == "error"


