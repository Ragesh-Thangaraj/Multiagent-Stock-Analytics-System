"""
Valuation Agent - Part of Layer 2 (Parallel Execution)

This agent is responsible for calculating valuation metrics including:
- P/E Ratio (trailing and forward)
- Price-to-Book (P/B)
- Price-to-Sales (P/S)
- EV/EBITDA
- PEG Ratio
- Enterprise Value
- Earnings Yield
- Book Value Per Share
- Dividend Yield
"""

import logging
from typing import Dict, Any

from google.adk.agents import LlmAgent

from .tools.valuation_tools import (
    calculate_pe_ratio,
    calculate_forward_pe,
    calculate_price_to_book,
    calculate_price_to_sales,
    calculate_ev_to_ebitda,
    calculate_peg_ratio,
    calculate_enterprise_value,
    calculate_earnings_yield,
    calculate_book_value_per_share,
    calculate_dividend_yield,
)

logger = logging.getLogger(__name__)


VALUATION_AGENT_INSTRUCTION = """You are a Valuation Analysis Agent specializing in stock valuation metrics.

Your primary responsibility is to calculate ALL valuation metrics for a given stock using the tools provided.

VALUATION METRICS TO CALCULATE:
1. P/E RATIO: Price relative to earnings (trailing 12 months)
2. FORWARD P/E: Price relative to expected future earnings
3. PRICE-TO-BOOK (P/B): Price relative to book value per share
4. PRICE-TO-SALES (P/S): Market cap relative to revenue
5. EV/EBITDA: Enterprise value relative to operating earnings
6. PEG RATIO: P/E relative to earnings growth rate
7. ENTERPRISE VALUE: Total company value including debt
8. EARNINGS YIELD: Inverse of P/E, shows return relative to price
9. BOOK VALUE PER SHARE: Net asset value per share
10. DIVIDEND YIELD: Annual dividend relative to stock price

Call each calculation tool with the canonical_data to compute the metrics.

CRITICAL: Your final response MUST be valid JSON summarizing the calculations:
```json
{
  "status": "success",
  "metrics_calculated": 10,
  "metrics_successful": 8,
  "valuation_summary": "fairly_valued"
}
```

IMPORTANT:
- Use Yahoo Finance precomputed ratios when available for accuracy
- Your output MUST be valid JSON only - no additional text
"""


class ValuationAgent:
    """
    Valuation Agent for Layer 2 of the stock analytics pipeline.
    Calculates valuation metrics like P/E, P/B, EV/EBITDA, PEG, etc.
    """
    
    def __init__(self, model: str = "gemini-2.0-flash"):
        """
        Initialize the Valuation Agent.
        
        Args:
            model: The Gemini model to use for the agent.
        """
        self.model = model
        self.agent = self._create_agent()
        
    def _create_agent(self) -> LlmAgent:
        """Create the LLM agent with valuation calculation tools."""
        return LlmAgent(
            name="ValuationAgent",
            model=self.model,
            instruction=VALUATION_AGENT_INSTRUCTION,
            description="Calculates valuation metrics including P/E, P/B, EV/EBITDA, PEG ratio to assess stock valuation.",
            tools=[
                calculate_pe_ratio,
                calculate_forward_pe,
                calculate_price_to_book,
                calculate_price_to_sales,
                calculate_ev_to_ebitda,
                calculate_peg_ratio,
                calculate_enterprise_value,
                calculate_earnings_yield,
                calculate_book_value_per_share,
                calculate_dividend_yield,
            ],
            output_key="valuation_metrics",
        )
    
    def calculate_all_valuations(self, stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate all valuation metrics for the given stock data.
        
        This is a direct calculation method that bypasses the LLM for efficiency and accuracy.
        
        Args:
            stock_data: Canonical stock data from DataAgent
            
        Returns:
            dict: All calculated valuation metrics
        """
        ticker = stock_data.get('meta', {}).get('ticker', 'Unknown')
        logger.info(f"ValuationAgent: Calculating valuations for {ticker}...")
        
        valuation_metrics = {
            "pe_ratio": calculate_pe_ratio(stock_data),
            "forward_pe": calculate_forward_pe(stock_data),
            "price_to_book": calculate_price_to_book(stock_data),
            "price_to_sales": calculate_price_to_sales(stock_data),
            "ev_to_ebitda": calculate_ev_to_ebitda(stock_data),
            "peg_ratio": calculate_peg_ratio(stock_data),
            "enterprise_value": calculate_enterprise_value(stock_data),
            "earnings_yield": calculate_earnings_yield(stock_data),
            "book_value_per_share": calculate_book_value_per_share(stock_data),
            "dividend_yield": calculate_dividend_yield(stock_data),
        }
        
        valuation_summary = self._generate_valuation_summary(valuation_metrics)
        
        result = {
            "ticker": ticker,
            "metrics": valuation_metrics,
            "summary": valuation_summary,
            "status": "success",
        }
        
        self._log_calculation_summary(result)
        
        return result
    
    def _generate_valuation_summary(self, metrics: Dict[str, Any]) -> str:
        """Generate a brief valuation summary based on calculated metrics."""
        pe = metrics.get('pe_ratio', {}).get('value')
        peg = metrics.get('peg_ratio', {}).get('value')
        pb = metrics.get('price_to_book', {}).get('value')
        
        signals = []
        
        if pe is not None:
            if pe < 15:
                signals.append("Low P/E suggests value opportunity or concerns")
            elif pe > 30:
                signals.append("High P/E indicates growth expectations")
        
        if peg is not None:
            if peg < 1:
                signals.append("PEG < 1 suggests undervaluation relative to growth")
            elif peg > 2:
                signals.append("PEG > 2 suggests premium pricing")
        
        if pb is not None:
            if pb < 1:
                signals.append("Trading below book value")
        
        if not signals:
            return "Fair valuation based on available metrics"
        
        return "; ".join(signals)
    
    def _log_calculation_summary(self, result: Dict[str, Any]) -> None:
        """Log a summary of calculated metrics."""
        metrics = result.get('metrics', {})
        total = len(metrics)
        successful = sum(1 for m in metrics.values() 
                        if m.get('status') == 'success' and m.get('value') is not None)
        
        logger.info(f"ValuationAgent: Calculated {successful}/{total} valuation metrics successfully")
    
    def get_llm_agent(self) -> LlmAgent:
        """Get the underlying LLM agent for use in orchestration."""
        return self.agent


def create_valuation_agent(model: str = "gemini-2.0-flash") -> ValuationAgent:
    """
    Factory function to create a Valuation Agent.
    
    Args:
        model: The Gemini model to use
        
    Returns:
        ValuationAgent: A configured Valuation Agent instance
    """
    return ValuationAgent(model=model)
