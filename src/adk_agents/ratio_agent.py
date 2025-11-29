"""
Ratio Agent - Part of Layer 2 (Parallel Execution)

This agent is responsible for calculating financial ratios including:
- Profitability metrics (margins, ROA, ROE, ROIC)
- Liquidity metrics (current ratio, quick ratio, cash ratio)
- Leverage metrics (debt-to-equity, interest coverage)
- Efficiency metrics (asset turnover, inventory turnover)
- Growth metrics (revenue, earnings, EPS growth)
- Cash flow metrics (FCF, operating cash flow ratio)
"""

import logging
from typing import Dict, Any, List

from google.adk.agents import LlmAgent

from .tools.ratio_tools import (
    calculate_gross_margin,
    calculate_operating_margin,
    calculate_net_margin,
    calculate_roa,
    calculate_roe,
    calculate_roic,
    calculate_current_ratio,
    calculate_quick_ratio,
    calculate_cash_ratio,
    calculate_working_capital,
    calculate_debt_to_equity,
    calculate_debt_to_assets,
    calculate_interest_coverage,
    calculate_asset_turnover,
    calculate_inventory_turnover,
    calculate_receivables_turnover,
    calculate_revenue_growth,
    calculate_net_income_growth,
    calculate_eps_growth,
    calculate_fcf_growth,
    calculate_operating_income_growth,
    calculate_free_cash_flow,
    calculate_operating_cash_flow_ratio,
    calculate_cash_flow_margin,
)

logger = logging.getLogger(__name__)


RATIO_AGENT_INSTRUCTION = """You are a Financial Ratio Analysis Agent specializing in comprehensive ratio calculations.

Your primary responsibility is to calculate ALL financial ratios for a given stock using the tools provided.

CALCULATION CATEGORIES:
1. PROFITABILITY: Gross margin, operating margin, net margin, ROA, ROE, ROIC
2. LIQUIDITY: Current ratio, quick ratio, cash ratio, working capital
3. LEVERAGE: Debt-to-equity, debt-to-assets, interest coverage
4. EFFICIENCY: Asset turnover, inventory turnover, receivables turnover
5. GROWTH: Revenue growth, net income growth, EPS growth, FCF growth
6. CASH FLOW: Free cash flow, operating cash flow ratio, cash flow margin

CALCULATION RULES:
- Call each calculation tool with the canonical_data
- Use Yahoo Finance precomputed values when available (most reliable)
- Handle missing data gracefully

CRITICAL: Your final response MUST be valid JSON summarizing the calculations:
```json
{
  "status": "success",
  "metrics_calculated": 23,
  "metrics_successful": 20,
  "categories": {
    "profitability": 6,
    "liquidity": 4,
    "leverage": 3,
    "efficiency": 3,
    "growth": 5,
    "cashflow": 3
  }
}
```

IMPORTANT:
- All calculations must be deterministic and accurate
- Never guess or estimate values - use actual data only
- Your output MUST be valid JSON only - no additional text
"""


class RatioAgent:
    """
    Ratio Agent for Layer 2 of the stock analytics pipeline.
    Calculates profitability, liquidity, leverage, efficiency, growth, and cash flow metrics.
    """
    
    def __init__(self, model: str = "gemini-2.0-flash"):
        """
        Initialize the Ratio Agent.
        
        Args:
            model: The Gemini model to use for the agent.
        """
        self.model = model
        self.agent = self._create_agent()
        
    def _create_agent(self) -> LlmAgent:
        """Create the LLM agent with ratio calculation tools."""
        return LlmAgent(
            name="RatioAgent",
            model=self.model,
            instruction=RATIO_AGENT_INSTRUCTION,
            description="Calculates comprehensive financial ratios including profitability, liquidity, leverage, efficiency, growth, and cash flow metrics.",
            tools=[
                calculate_gross_margin,
                calculate_operating_margin,
                calculate_net_margin,
                calculate_roa,
                calculate_roe,
                calculate_roic,
                calculate_current_ratio,
                calculate_quick_ratio,
                calculate_cash_ratio,
                calculate_working_capital,
                calculate_debt_to_equity,
                calculate_debt_to_assets,
                calculate_interest_coverage,
                calculate_asset_turnover,
                calculate_inventory_turnover,
                calculate_receivables_turnover,
                calculate_revenue_growth,
                calculate_net_income_growth,
                calculate_eps_growth,
                calculate_fcf_growth,
                calculate_operating_income_growth,
                calculate_free_cash_flow,
                calculate_operating_cash_flow_ratio,
                calculate_cash_flow_margin,
            ],
            output_key="ratio_metrics",
        )
    
    def calculate_all_ratios(self, stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate all financial ratios for the given stock data.
        
        This is a direct calculation method that bypasses the LLM for efficiency and accuracy.
        
        Args:
            stock_data: Canonical stock data from DataAgent
            
        Returns:
            dict: All calculated ratio metrics organized by category
        """
        ticker = stock_data.get('meta', {}).get('ticker', 'Unknown')
        logger.info(f"RatioAgent: Calculating ratios for {ticker}...")
        
        profitability = {
            "gross_margin": calculate_gross_margin(stock_data),
            "operating_margin": calculate_operating_margin(stock_data),
            "net_margin": calculate_net_margin(stock_data),
            "roa": calculate_roa(stock_data),
            "roe": calculate_roe(stock_data),
            "roic": calculate_roic(stock_data),
        }
        
        liquidity = {
            "current_ratio": calculate_current_ratio(stock_data),
            "quick_ratio": calculate_quick_ratio(stock_data),
            "cash_ratio": calculate_cash_ratio(stock_data),
            "working_capital": calculate_working_capital(stock_data),
        }
        
        leverage = {
            "debt_to_equity": calculate_debt_to_equity(stock_data),
            "debt_to_assets": calculate_debt_to_assets(stock_data),
            "interest_coverage": calculate_interest_coverage(stock_data),
        }
        
        efficiency = {
            "asset_turnover": calculate_asset_turnover(stock_data),
            "inventory_turnover": calculate_inventory_turnover(stock_data),
            "receivables_turnover": calculate_receivables_turnover(stock_data),
        }
        
        growth = {
            "revenue_growth": calculate_revenue_growth(stock_data),
            "net_income_growth": calculate_net_income_growth(stock_data),
            "eps_growth": calculate_eps_growth(stock_data),
            "fcf_growth": calculate_fcf_growth(stock_data),
            "operating_income_growth": calculate_operating_income_growth(stock_data),
        }
        
        cashflow = {
            "free_cash_flow": calculate_free_cash_flow(stock_data),
            "operating_cash_flow_ratio": calculate_operating_cash_flow_ratio(stock_data),
            "cash_flow_margin": calculate_cash_flow_margin(stock_data),
        }
        
        result = {
            "ticker": ticker,
            "profitability": profitability,
            "liquidity": liquidity,
            "leverage": leverage,
            "efficiency": efficiency,
            "growth": growth,
            "cashflow": cashflow,
            "status": "success",
        }
        
        self._log_calculation_summary(result)
        
        return result
    
    def _log_calculation_summary(self, result: Dict[str, Any]) -> None:
        """Log a summary of calculated metrics."""
        total = 0
        successful = 0
        
        for category in ['profitability', 'liquidity', 'leverage', 'efficiency', 'growth', 'cashflow']:
            metrics = result.get(category, {})
            for metric_name, metric_data in metrics.items():
                total += 1
                if metric_data.get('status') == 'success' and metric_data.get('value') is not None:
                    successful += 1
        
        logger.info(f"RatioAgent: Calculated {successful}/{total} metrics successfully")
    
    def get_llm_agent(self) -> LlmAgent:
        """Get the underlying LLM agent for use in orchestration."""
        return self.agent


def create_ratio_agent(model: str = "gemini-2.0-flash") -> RatioAgent:
    """
    Factory function to create a Ratio Agent.
    
    Args:
        model: The Gemini model to use
        
    Returns:
        RatioAgent: A configured Ratio Agent instance
    """
    return RatioAgent(model=model)
