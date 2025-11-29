"""
Risk Analysis Calculation Tools for ADK Agents

These tools calculate market risk metrics (beta, volatility, Sharpe ratio, VaR, max drawdown)
and financial risk metrics (Altman Z-Score, credit risk, liquidity risk, operational risk).
"""

import logging
import numpy as np
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


def calculate_beta(stock_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Gets Beta - measures stock's volatility relative to the market.
    Beta > 1 means more volatile than market, Beta < 1 means less volatile.

    Args:
        stock_data (dict): Stock data containing info from Yahoo Finance.

    Returns:
        dict: Contains value (ratio), formula, source, and interpretation.
    """
    try:
        info = stock_data.get('info', {})
        beta = info.get('beta')
        
        if beta is not None:
            return {
                "status": "success",
                "metric": "beta",
                "value": round(beta, 2),
                "unit": "",
                "formula": "Covariance(Stock, Market) / Variance(Market)",
                "source": "yahoo_finance.precomputed",
                "interpretation": _interpret_beta(beta),
            }
        
        return {
            "status": "error",
            "metric": "beta",
            "value": None,
            "null_reason": "Beta not available",
        }
        
    except Exception as e:
        logger.error(f"Error getting beta: {e}")
        return {"status": "error", "metric": "beta", "error": str(e)}


def calculate_alpha(stock_data: Dict[str, Any], market_return: float = 0.10, risk_free_rate: float = 0.05) -> Dict[str, Any]:
    """
    Calculates Alpha (Jensen's Alpha) - excess return above expected based on beta.
    Alpha = Actual Return - [Risk-Free Rate + Beta × (Market Return - Risk-Free Rate)]
    
    Uses compounded daily returns for accurate annualization.
    Note: Uses price returns only (dividend-adjusted prices assumed if available from data source).

    Args:
        stock_data (dict): Stock data containing price_history and info.
        market_return (float): Expected annual market return (default 10%).
        risk_free_rate (float): Annual risk-free rate (default 5%).

    Returns:
        dict: Contains value (percentage), formula, source, and interpretation.
    """
    try:
        info = stock_data.get('info', {})
        beta = info.get('beta')
        price_history = stock_data.get('price_history', [])
        
        if beta is not None and len(price_history) >= 30:
            sorted_history = sorted(
                [p for p in price_history if p.get('close') and p.get('close') > 0 and p.get('date')],
                key=lambda x: x['date']
            )
            
            if len(sorted_history) < 30:
                return {
                    "status": "error",
                    "metric": "alpha",
                    "value": None,
                    "null_reason": "Insufficient valid price data for alpha calculation",
                }
            
            closes = [p['close'] for p in sorted_history]
            
            daily_returns = []
            for i in range(1, len(closes)):
                if closes[i-1] > 0:
                    daily_return = (closes[i] / closes[i-1]) - 1
                    if abs(daily_return) < 0.5:
                        daily_returns.append(1 + daily_return)
            
            if len(daily_returns) < 20:
                return {
                    "status": "error",
                    "metric": "alpha",
                    "value": None,
                    "null_reason": "Insufficient valid daily returns for alpha calculation",
                }
            
            compounded_return = 1.0
            for r in daily_returns:
                compounded_return *= r
            
            trading_days = len(daily_returns)
            years = trading_days / 252.0
            
            if years <= 0:
                return {
                    "status": "error",
                    "metric": "alpha",
                    "value": None,
                    "null_reason": "Insufficient time period for alpha calculation",
                }
            
            stock_return = (compounded_return ** (1 / years)) - 1
            
            expected_return = risk_free_rate + beta * (market_return - risk_free_rate)
            alpha = (stock_return - expected_return) * 100
            
            if abs(alpha) > 200:
                return {
                    "status": "error",
                    "metric": "alpha",
                    "value": None,
                    "null_reason": "Alpha calculation yielded unrealistic value",
                }
            
            return {
                "status": "success",
                "metric": "alpha",
                "value": round(alpha, 2),
                "unit": "%",
                "formula": "Annualized(∏(1+r_daily)) - [Rf + β × (Rm - Rf)]",
                "source": "calculated.price_history.compounded_daily",
                "interpretation": _interpret_alpha(alpha),
            }
        
        return {
            "status": "error",
            "metric": "alpha",
            "value": None,
            "null_reason": "Insufficient data for alpha calculation (requires beta and 30+ days of prices)",
        }
        
    except Exception as e:
        logger.error(f"Error calculating alpha: {e}")
        return {"status": "error", "metric": "alpha", "error": str(e)}


def calculate_volatility(stock_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates Annualized Volatility from daily returns.
    Standard deviation of returns annualized (x sqrt(252)).

    Args:
        stock_data (dict): Stock data containing price_history.

    Returns:
        dict: Contains value (percentage), formula, source, and interpretation.
    """
    try:
        price_history = stock_data.get('price_history', [])
        
        if len(price_history) >= 30:
            closes = [p['close'] for p in price_history if p.get('close')]
            
            if len(closes) >= 30:
                returns = []
                for i in range(1, len(closes)):
                    if closes[i-1] and closes[i-1] > 0:
                        ret = (closes[i] - closes[i-1]) / closes[i-1]
                        returns.append(ret)
                
                if returns:
                    daily_vol = np.std(returns)
                    annual_vol = daily_vol * np.sqrt(252) * 100
                    
                    return {
                        "status": "success",
                        "metric": "volatility",
                        "value": round(annual_vol, 2),
                        "unit": "%",
                        "formula": "StdDev(Daily Returns) × √252 × 100",
                        "source": "calculated.price_history",
                        "interpretation": _interpret_volatility(annual_vol),
                    }
        
        return {
            "status": "error",
            "metric": "volatility",
            "value": None,
            "null_reason": "Insufficient price data for volatility calculation",
        }
        
    except Exception as e:
        logger.error(f"Error calculating volatility: {e}")
        return {"status": "error", "metric": "volatility", "error": str(e)}


def calculate_sharpe_ratio(stock_data: Dict[str, Any], risk_free_rate: float = 0.05) -> Dict[str, Any]:
    """
    Calculates Sharpe Ratio = (Return - Risk-Free Rate) / Volatility.
    Measures risk-adjusted return.

    Args:
        stock_data (dict): Stock data containing price_history.
        risk_free_rate (float): Annual risk-free rate (default 5%).

    Returns:
        dict: Contains value (ratio), formula, source, and interpretation.
    """
    try:
        price_history = stock_data.get('price_history', [])
        
        if len(price_history) >= 30:
            closes = [p['close'] for p in price_history if p.get('close')]
            
            if len(closes) >= 30:
                annual_return = (closes[-1] / closes[0] - 1) * (252 / len(closes))
                
                returns = []
                for i in range(1, len(closes)):
                    if closes[i-1] and closes[i-1] > 0:
                        ret = (closes[i] - closes[i-1]) / closes[i-1]
                        returns.append(ret)
                
                if returns:
                    daily_vol = np.std(returns)
                    annual_vol = daily_vol * np.sqrt(252)
                    
                    if annual_vol > 0:
                        sharpe = (annual_return - risk_free_rate) / annual_vol
                        
                        return {
                            "status": "success",
                            "metric": "sharpe_ratio",
                            "value": round(sharpe, 2),
                            "unit": "",
                            "formula": "(Annual Return - Risk-Free Rate) / Annual Volatility",
                            "source": "calculated.price_history",
                            "interpretation": _interpret_sharpe(sharpe),
                        }
        
        return {
            "status": "error",
            "metric": "sharpe_ratio",
            "value": None,
            "null_reason": "Insufficient data for Sharpe ratio calculation",
        }
        
    except Exception as e:
        logger.error(f"Error calculating Sharpe ratio: {e}")
        return {"status": "error", "metric": "sharpe_ratio", "error": str(e)}


def calculate_max_drawdown(stock_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates Maximum Drawdown - the largest peak-to-trough decline.
    Measures worst-case loss from a peak.

    Args:
        stock_data (dict): Stock data containing price_history.

    Returns:
        dict: Contains value (percentage), formula, source, and interpretation.
    """
    try:
        price_history = stock_data.get('price_history', [])
        
        if len(price_history) >= 20:
            closes = [p['close'] for p in price_history if p.get('close')]
            
            if len(closes) >= 20:
                peak = closes[0]
                max_dd = 0
                
                for price in closes:
                    if price > peak:
                        peak = price
                    drawdown = (peak - price) / peak
                    if drawdown > max_dd:
                        max_dd = drawdown
                
                value = max_dd * 100
                
                return {
                    "status": "success",
                    "metric": "max_drawdown",
                    "value": round(value, 2),
                    "unit": "%",
                    "formula": "(Peak - Trough) / Peak × 100",
                    "source": "calculated.price_history",
                    "interpretation": _interpret_max_drawdown(value),
                }
        
        return {
            "status": "error",
            "metric": "max_drawdown",
            "value": None,
            "null_reason": "Insufficient price data for max drawdown calculation",
        }
        
    except Exception as e:
        logger.error(f"Error calculating max drawdown: {e}")
        return {"status": "error", "metric": "max_drawdown", "error": str(e)}


def calculate_var_95(stock_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates Value at Risk (95%) - potential loss at 95% confidence.
    Estimates worst expected daily loss 95% of the time.

    Args:
        stock_data (dict): Stock data containing price_history.

    Returns:
        dict: Contains value (percentage), formula, source, and interpretation.
    """
    try:
        price_history = stock_data.get('price_history', [])
        
        if len(price_history) >= 30:
            closes = [p['close'] for p in price_history if p.get('close')]
            
            if len(closes) >= 30:
                returns = []
                for i in range(1, len(closes)):
                    if closes[i-1] and closes[i-1] > 0:
                        ret = (closes[i] - closes[i-1]) / closes[i-1]
                        returns.append(ret)
                
                if returns:
                    var_95 = np.percentile(returns, 5) * 100
                    
                    return {
                        "status": "success",
                        "metric": "var_95",
                        "value": round(abs(var_95), 2),
                        "unit": "%",
                        "formula": "5th percentile of daily returns × 100",
                        "source": "calculated.price_history",
                        "interpretation": f"95% confident daily loss won't exceed {round(abs(var_95), 2)}%",
                    }
        
        return {
            "status": "error",
            "metric": "var_95",
            "value": None,
            "null_reason": "Insufficient data for VaR calculation",
        }
        
    except Exception as e:
        logger.error(f"Error calculating VaR: {e}")
        return {"status": "error", "metric": "var_95", "error": str(e)}


def calculate_altman_z_score(stock_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates Altman Z-Score - bankruptcy prediction model.
    Z = 1.2*A + 1.4*B + 3.3*C + 0.6*D + 1.0*E where A-E are financial ratios.

    Args:
        stock_data (dict): Stock data containing fundamentals.

    Returns:
        dict: Contains value (score), formula, source, and interpretation.
    """
    try:
        fundamentals = stock_data.get('fundamentals', {})
        balance = fundamentals.get('balance_sheet', {})
        income = fundamentals.get('income_statement', {})
        info = stock_data.get('info', {})
        
        if balance and income:
            latest_balance = list(balance.keys())[0] if balance else None
            latest_income = list(income.keys())[0] if income else None
            
            if latest_balance and latest_income:
                b_data = balance[latest_balance]
                i_data = income[latest_income]
                
                total_assets = b_data.get('Total Assets')
                current_assets = b_data.get('Current Assets')
                current_liabilities = b_data.get('Current Liabilities')
                retained_earnings = b_data.get('Retained Earnings')
                ebit = i_data.get('EBIT') or i_data.get('Operating Income')
                total_liabilities = b_data.get('Total Liabilities Net Minority Interest') or b_data.get('Total Liabilities')
                revenue = i_data.get('Total Revenue')
                market_cap = info.get('market_cap')
                
                if total_assets and total_assets > 0:
                    working_capital = (current_assets or 0) - (current_liabilities or 0)
                    
                    A = working_capital / total_assets
                    B = (retained_earnings or 0) / total_assets
                    C = (ebit or 0) / total_assets
                    D = (market_cap or 0) / (total_liabilities or 1) if total_liabilities else 0
                    E = (revenue or 0) / total_assets
                    
                    z_score = 1.2*A + 1.4*B + 3.3*C + 0.6*D + 1.0*E
                    
                    return {
                        "status": "success",
                        "metric": "altman_z_score",
                        "value": round(z_score, 2),
                        "unit": "",
                        "formula": "1.2×(WC/TA) + 1.4×(RE/TA) + 3.3×(EBIT/TA) + 0.6×(MC/TL) + 1.0×(Rev/TA)",
                        "source": "calculated.fundamentals",
                        "interpretation": _interpret_z_score(z_score),
                    }
        
        return {
            "status": "error",
            "metric": "altman_z_score",
            "value": None,
            "null_reason": "Insufficient data for Altman Z-Score calculation",
        }
        
    except Exception as e:
        logger.error(f"Error calculating Altman Z-Score: {e}")
        return {"status": "error", "metric": "altman_z_score", "error": str(e)}


def calculate_credit_risk_score(stock_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates a Credit Risk Score (0-100) based on debt metrics.
    Higher score = higher risk.

    Args:
        stock_data (dict): Stock data containing fundamentals and info.

    Returns:
        dict: Contains value (score), formula, source, and interpretation.
    """
    try:
        info = stock_data.get('info', {})
        
        debt_to_equity = info.get('debt_to_equity')
        current_ratio = info.get('current_ratio')
        
        risk_score = 50
        
        if debt_to_equity is not None:
            d_e = debt_to_equity / 100 if debt_to_equity > 10 else debt_to_equity
            if d_e < 0.5:
                risk_score -= 20
            elif d_e < 1:
                risk_score -= 10
            elif d_e < 2:
                risk_score += 10
            else:
                risk_score += 25
        
        if current_ratio is not None:
            if current_ratio > 2:
                risk_score -= 15
            elif current_ratio > 1.5:
                risk_score -= 5
            elif current_ratio < 1:
                risk_score += 20
        
        risk_score = max(0, min(100, risk_score))
        
        return {
            "status": "success",
            "metric": "credit_risk_score",
            "value": round(risk_score),
            "unit": "/100",
            "formula": "Composite of D/E ratio and current ratio",
            "source": "calculated.composite",
            "interpretation": _interpret_risk_score(risk_score, "credit"),
        }
        
    except Exception as e:
        logger.error(f"Error calculating credit risk score: {e}")
        return {"status": "error", "metric": "credit_risk_score", "error": str(e)}


def calculate_liquidity_risk_score(stock_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates a Liquidity Risk Score (0-100) based on liquidity metrics.
    Higher score = higher risk.

    Args:
        stock_data (dict): Stock data containing fundamentals and info.

    Returns:
        dict: Contains value (score), formula, source, and interpretation.
    """
    try:
        info = stock_data.get('info', {})
        
        current_ratio = info.get('current_ratio')
        quick_ratio = info.get('quick_ratio')
        
        risk_score = 50
        
        if current_ratio is not None:
            if current_ratio > 2:
                risk_score -= 25
            elif current_ratio > 1.5:
                risk_score -= 15
            elif current_ratio > 1:
                risk_score -= 5
            elif current_ratio < 0.8:
                risk_score += 25
        
        if quick_ratio is not None:
            if quick_ratio > 1.5:
                risk_score -= 15
            elif quick_ratio > 1:
                risk_score -= 5
            elif quick_ratio < 0.5:
                risk_score += 15
        
        risk_score = max(0, min(100, risk_score))
        
        return {
            "status": "success",
            "metric": "liquidity_risk_score",
            "value": round(risk_score),
            "unit": "/100",
            "formula": "Composite of current ratio and quick ratio",
            "source": "calculated.composite",
            "interpretation": _interpret_risk_score(risk_score, "liquidity"),
        }
        
    except Exception as e:
        logger.error(f"Error calculating liquidity risk score: {e}")
        return {"status": "error", "metric": "liquidity_risk_score", "error": str(e)}


def calculate_operational_risk_score(stock_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates an Operational Risk Score (0-100) based on profitability volatility.
    Higher score = higher risk.

    Args:
        stock_data (dict): Stock data containing fundamentals and info.

    Returns:
        dict: Contains value (score), formula, source, and interpretation.
    """
    try:
        info = stock_data.get('info', {})
        
        operating_margins = info.get('operating_margins')
        profit_margins = info.get('profit_margins')
        
        risk_score = 50
        
        if operating_margins is not None:
            om = operating_margins * 100
            if om > 20:
                risk_score -= 20
            elif om > 10:
                risk_score -= 10
            elif om > 5:
                risk_score -= 5
            elif om < 0:
                risk_score += 25
        
        if profit_margins is not None:
            pm = profit_margins * 100
            if pm > 15:
                risk_score -= 15
            elif pm > 5:
                risk_score -= 5
            elif pm < 0:
                risk_score += 20
        
        risk_score = max(0, min(100, risk_score))
        
        return {
            "status": "success",
            "metric": "operational_risk_score",
            "value": round(risk_score),
            "unit": "/100",
            "formula": "Composite of operating and profit margins",
            "source": "calculated.composite",
            "interpretation": _interpret_risk_score(risk_score, "operational"),
        }
        
    except Exception as e:
        logger.error(f"Error calculating operational risk score: {e}")
        return {"status": "error", "metric": "operational_risk_score", "error": str(e)}


def _interpret_beta(value: float) -> str:
    if value < 0.8:
        return "Low volatility - defensive stock"
    elif value < 1.2:
        return "Average market volatility"
    elif value < 1.5:
        return "Above average volatility"
    else:
        return "High volatility - aggressive stock"


def _interpret_alpha(value: float) -> str:
    if value > 10:
        return "Strong outperformance vs market"
    elif value > 5:
        return "Moderate outperformance"
    elif value > 0:
        return "Slight outperformance"
    elif value > -5:
        return "Slight underperformance"
    else:
        return "Underperforming market expectations"


def _interpret_volatility(value: float) -> str:
    if value < 20:
        return "Low volatility"
    elif value < 30:
        return "Moderate volatility"
    elif value < 50:
        return "High volatility"
    else:
        return "Very high volatility"


def _interpret_sharpe(value: float) -> str:
    if value > 1.5:
        return "Excellent risk-adjusted return"
    elif value > 1:
        return "Good risk-adjusted return"
    elif value > 0.5:
        return "Moderate risk-adjusted return"
    elif value > 0:
        return "Low but positive risk-adjusted return"
    else:
        return "Negative risk-adjusted return"


def _interpret_max_drawdown(value: float) -> str:
    if value < 10:
        return "Low drawdown - stable"
    elif value < 20:
        return "Moderate drawdown"
    elif value < 30:
        return "Significant drawdown"
    else:
        return "Severe drawdown - high risk"


def _interpret_z_score(value: float) -> str:
    if value > 2.99:
        return "Safe Zone - low bankruptcy risk"
    elif value > 1.81:
        return "Grey Zone - moderate risk, needs monitoring"
    else:
        return "Distress Zone - high bankruptcy risk"


def _interpret_risk_score(value: float, risk_type: str) -> str:
    if value < 30:
        return f"Low {risk_type} risk"
    elif value < 50:
        return f"Moderate {risk_type} risk"
    elif value < 70:
        return f"Elevated {risk_type} risk"
    else:
        return f"High {risk_type} risk"
