"""
Risk Analysis Agent - Part of Layer 2 (Parallel Execution)

This agent is responsible for calculating risk metrics including:
- Market Risk: Beta, volatility, Sharpe ratio, max drawdown, VaR
- Financial Risk: Altman Z-Score, credit risk, liquidity risk, operational risk
"""

import logging
from typing import Dict, Any

from google.adk.agents import LlmAgent

from .tools.risk_tools import (
    calculate_beta,
    calculate_alpha,
    calculate_volatility,
    calculate_sharpe_ratio,
    calculate_max_drawdown,
    calculate_var_95,
    calculate_altman_z_score,
    calculate_credit_risk_score,
    calculate_liquidity_risk_score,
    calculate_operational_risk_score,
)

logger = logging.getLogger(__name__)


RISK_AGENT_INSTRUCTION = """You are a Risk Analysis Agent specializing in comprehensive risk assessment.

Your primary responsibility is to calculate ALL risk metrics for a given stock using the tools provided.

MARKET RISK METRICS:
1. BETA: Stock's volatility relative to the market (S&P 500)
2. ALPHA: Jensen's alpha (excess return vs market)
3. VOLATILITY: Annualized standard deviation of returns
4. SHARPE RATIO: Risk-adjusted return
5. MAX DRAWDOWN: Largest peak-to-trough decline
6. VALUE AT RISK (95%): Daily loss at 95% confidence

FINANCIAL RISK METRICS:
1. ALTMAN Z-SCORE: Bankruptcy prediction
2. CREDIT RISK SCORE: Based on debt and liquidity (0-100)
3. LIQUIDITY RISK SCORE: Based on current/quick ratios (0-100)
4. OPERATIONAL RISK SCORE: Based on profitability stability (0-100)

Call each calculation tool with the canonical_data to compute the metrics.

CRITICAL: Your final response MUST be valid JSON summarizing the calculations:
```json
{
  "status": "success",
  "market_risk_count": 6,
  "financial_risk_count": 4,
  "overall_assessment": "moderate"
}
```

IMPORTANT:
- Use historical price data for market risk calculations
- Use fundamental data for financial risk calculations
- Your output MUST be valid JSON only - no additional text
"""


class RiskAnalysisAgent:
    """
    Risk Analysis Agent for Layer 2 of the stock analytics pipeline.
    Calculates market risk and financial risk metrics.
    """
    
    def __init__(self, model: str = "gemini-2.0-flash"):
        """
        Initialize the Risk Analysis Agent.
        
        Args:
            model: The Gemini model to use for the agent.
        """
        self.model = model
        self.agent = self._create_agent()
        
    def _create_agent(self) -> LlmAgent:
        """Create the LLM agent with risk calculation tools."""
        return LlmAgent(
            name="RiskAnalysisAgent",
            model=self.model,
            instruction=RISK_AGENT_INSTRUCTION,
            description="Calculates comprehensive risk metrics including market risk (beta, volatility, VaR) and financial risk (Z-score, credit risk).",
            tools=[
                calculate_beta,
                calculate_alpha,
                calculate_volatility,
                calculate_sharpe_ratio,
                calculate_max_drawdown,
                calculate_var_95,
                calculate_altman_z_score,
                calculate_credit_risk_score,
                calculate_liquidity_risk_score,
                calculate_operational_risk_score,
            ],
            output_key="risk_metrics",
        )
    
    def calculate_all_risks(self, stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate all risk metrics for the given stock data.
        
        This is a direct calculation method that bypasses the LLM for efficiency and accuracy.
        
        Args:
            stock_data: Canonical stock data from DataAgent
            
        Returns:
            dict: All calculated risk metrics organized by category
        """
        ticker = stock_data.get('meta', {}).get('ticker', 'Unknown')
        logger.info(f"RiskAnalysisAgent: Calculating risks for {ticker}...")
        
        market_risk = {
            "beta": calculate_beta(stock_data),
            "alpha": calculate_alpha(stock_data),
            "volatility": calculate_volatility(stock_data),
            "sharpe_ratio": calculate_sharpe_ratio(stock_data),
            "max_drawdown": calculate_max_drawdown(stock_data),
            "var_95": calculate_var_95(stock_data),
        }
        
        financial_risk = {
            "altman_z_score": calculate_altman_z_score(stock_data),
            "credit_risk_score": calculate_credit_risk_score(stock_data),
            "liquidity_risk_score": calculate_liquidity_risk_score(stock_data),
            "operational_risk_score": calculate_operational_risk_score(stock_data),
        }
        
        overall_risk = self._calculate_overall_risk(market_risk, financial_risk)
        
        result = {
            "ticker": ticker,
            "market_risk": market_risk,
            "financial_risk": financial_risk,
            "overall_risk": overall_risk,
            "status": "success",
        }
        
        self._log_calculation_summary(result)
        
        return result
    
    def _calculate_overall_risk(self, market_risk: Dict, financial_risk: Dict) -> Dict[str, Any]:
        """Calculate an overall risk assessment."""
        risk_flags = []
        
        beta = market_risk.get('beta', {}).get('value')
        if beta is not None and beta > 1.5:
            risk_flags.append("High beta - above-market volatility")
        
        volatility = market_risk.get('volatility', {}).get('value')
        if volatility is not None and volatility > 40:
            risk_flags.append("High volatility")
        
        z_score = financial_risk.get('altman_z_score', {}).get('value')
        if z_score is not None and z_score < 1.81:
            risk_flags.append("Distress zone - elevated bankruptcy risk")
        elif z_score is not None and z_score < 2.99:
            risk_flags.append("Grey zone - monitor financial health")
        
        credit_risk = financial_risk.get('credit_risk_score', {}).get('value')
        if credit_risk is not None and credit_risk > 70:
            risk_flags.append("High credit risk")
        
        max_dd = market_risk.get('max_drawdown', {}).get('value')
        if max_dd is not None and max_dd > 30:
            risk_flags.append("Significant historical drawdown")
        
        if not risk_flags:
            overall = "Low to Moderate Risk"
            level = "moderate"
        elif len(risk_flags) <= 2:
            overall = "Moderate to Elevated Risk"
            level = "elevated"
        else:
            overall = "High Risk"
            level = "high"
        
        return {
            "assessment": overall,
            "level": level,
            "flags": risk_flags,
            "flag_count": len(risk_flags),
        }
    
    def _log_calculation_summary(self, result: Dict[str, Any]) -> None:
        """Log a summary of calculated metrics."""
        market = result.get('market_risk', {})
        financial = result.get('financial_risk', {})
        
        total = len(market) + len(financial)
        successful = (
            sum(1 for m in market.values() if m.get('status') == 'success' and m.get('value') is not None) +
            sum(1 for m in financial.values() if m.get('status') == 'success' and m.get('value') is not None)
        )
        
        logger.info(f"RiskAnalysisAgent: Calculated {successful}/{total} risk metrics successfully")
        logger.info(f"RiskAnalysisAgent: Overall assessment - {result.get('overall_risk', {}).get('assessment')}")
    
    def get_llm_agent(self) -> LlmAgent:
        """Get the underlying LLM agent for use in orchestration."""
        return self.agent


def create_risk_agent(model: str = "gemini-2.0-flash") -> RiskAnalysisAgent:
    """
    Factory function to create a Risk Analysis Agent.
    
    Args:
        model: The Gemini model to use
        
    Returns:
        RiskAnalysisAgent: A configured Risk Analysis Agent instance
    """
    return RiskAnalysisAgent(model=model)
