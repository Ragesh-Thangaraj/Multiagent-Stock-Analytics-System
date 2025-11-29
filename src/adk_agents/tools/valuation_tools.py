"""
Valuation Calculation Tools for ADK Agents

These tools calculate valuation metrics like P/E, P/B, EV/EBITDA, PEG, etc.
All calculations use verified formulas and prefer Yahoo Finance precomputed values when available.
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def calculate_pe_ratio(stock_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates Price-to-Earnings (P/E) Ratio = Stock Price / Earnings Per Share.
    Measures how much investors pay per dollar of earnings.

    Args:
        stock_data (dict): Stock data containing info from Yahoo Finance.

    Returns:
        dict: Contains value (ratio), formula, source, and interpretation.
    """
    try:
        info = stock_data.get('info', {})
        pe = info.get('trailing_pe')
        
        if pe is not None and pe > 0:
            return {
                "status": "success",
                "metric": "pe_ratio",
                "value": round(pe, 2),
                "unit": "x",
                "formula": "Stock Price / Earnings Per Share (TTM)",
                "source": "yahoo_finance.precomputed",
                "interpretation": _interpret_pe(pe),
            }
        
        current_price = info.get('current_price')
        eps = info.get('earnings_per_share')
        
        if current_price and eps and eps > 0:
            pe = current_price / eps
            return {
                "status": "success",
                "metric": "pe_ratio",
                "value": round(pe, 2),
                "unit": "x",
                "formula": "Stock Price / Earnings Per Share",
                "source": "calculated.info",
                "interpretation": _interpret_pe(pe),
            }
        
        if eps is not None and eps < 0:
            forward_pe = info.get('forward_pe')
            if forward_pe and forward_pe > 0:
                return {
                    "status": "error",
                    "metric": "pe_ratio",
                    "value": None,
                    "null_reason": f"Company has negative earnings (EPS: ${eps:.2f}). See Forward P/E ({forward_pe:.1f}x) for future outlook.",
                }
            return {
                "status": "error",
                "metric": "pe_ratio",
                "value": None,
                "null_reason": f"Company has negative earnings (EPS: ${eps:.2f}) - P/E ratio not meaningful",
            }
        
        return {
            "status": "error",
            "metric": "pe_ratio",
            "value": None,
            "null_reason": "P/E ratio not available (earnings data missing)",
        }
        
    except Exception as e:
        logger.error(f"Error calculating P/E ratio: {e}")
        return {"status": "error", "metric": "pe_ratio", "error": str(e)}


def calculate_forward_pe(stock_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates Forward P/E Ratio = Stock Price / Forward EPS.
    Measures valuation based on expected future earnings.

    Args:
        stock_data (dict): Stock data containing info from Yahoo Finance.

    Returns:
        dict: Contains value (ratio), formula, source, and interpretation.
    """
    try:
        info = stock_data.get('info', {})
        forward_pe = info.get('forward_pe')
        
        if forward_pe is not None and forward_pe > 0:
            return {
                "status": "success",
                "metric": "forward_pe",
                "value": round(forward_pe, 2),
                "unit": "x",
                "formula": "Stock Price / Forward Earnings Per Share",
                "source": "yahoo_finance.precomputed",
                "interpretation": _interpret_forward_pe(forward_pe),
            }
        
        return {
            "status": "error",
            "metric": "forward_pe",
            "value": None,
            "null_reason": "Forward P/E not available",
        }
        
    except Exception as e:
        logger.error(f"Error calculating forward P/E: {e}")
        return {"status": "error", "metric": "forward_pe", "error": str(e)}


def calculate_price_to_book(stock_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates Price-to-Book (P/B) Ratio = Stock Price / Book Value Per Share.
    Measures how much investors pay per dollar of book value.

    Args:
        stock_data (dict): Stock data containing info from Yahoo Finance.

    Returns:
        dict: Contains value (ratio), formula, source, and interpretation.
    """
    try:
        info = stock_data.get('info', {})
        pb = info.get('price_to_book')
        
        if pb is not None and pb > 0:
            return {
                "status": "success",
                "metric": "price_to_book",
                "value": round(pb, 2),
                "unit": "x",
                "formula": "Stock Price / Book Value Per Share",
                "source": "yahoo_finance.precomputed",
                "interpretation": _interpret_pb(pb),
            }
        
        return {
            "status": "error",
            "metric": "price_to_book",
            "value": None,
            "null_reason": "P/B ratio not available",
        }
        
    except Exception as e:
        logger.error(f"Error calculating P/B ratio: {e}")
        return {"status": "error", "metric": "price_to_book", "error": str(e)}


def calculate_price_to_sales(stock_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates Price-to-Sales (P/S) Ratio = Market Cap / Revenue.
    Measures how much investors pay per dollar of sales.

    Args:
        stock_data (dict): Stock data containing info from Yahoo Finance.

    Returns:
        dict: Contains value (ratio), formula, source, and interpretation.
    """
    try:
        info = stock_data.get('info', {})
        ps = info.get('price_to_sales')
        
        if ps is not None and ps > 0:
            return {
                "status": "success",
                "metric": "price_to_sales",
                "value": round(ps, 2),
                "unit": "x",
                "formula": "Market Cap / Revenue (TTM)",
                "source": "yahoo_finance.precomputed",
                "interpretation": _interpret_ps(ps),
            }
        
        return {
            "status": "error",
            "metric": "price_to_sales",
            "value": None,
            "null_reason": "P/S ratio not available",
        }
        
    except Exception as e:
        logger.error(f"Error calculating P/S ratio: {e}")
        return {"status": "error", "metric": "price_to_sales", "error": str(e)}


def calculate_ev_to_ebitda(stock_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates Enterprise Value to EBITDA ratio.
    Measures valuation relative to operating earnings.

    Args:
        stock_data (dict): Stock data containing info from Yahoo Finance.

    Returns:
        dict: Contains value (ratio), formula, source, and interpretation.
    """
    try:
        info = stock_data.get('info', {})
        ev_ebitda = info.get('enterprise_to_ebitda')
        
        if ev_ebitda is not None and ev_ebitda > 0:
            return {
                "status": "success",
                "metric": "ev_to_ebitda",
                "value": round(ev_ebitda, 2),
                "unit": "x",
                "formula": "Enterprise Value / EBITDA",
                "source": "yahoo_finance.precomputed",
                "interpretation": _interpret_ev_ebitda(ev_ebitda),
            }
        
        return {
            "status": "error",
            "metric": "ev_to_ebitda",
            "value": None,
            "null_reason": "EV/EBITDA not available",
        }
        
    except Exception as e:
        logger.error(f"Error calculating EV/EBITDA: {e}")
        return {"status": "error", "metric": "ev_to_ebitda", "error": str(e)}


def calculate_peg_ratio(stock_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates PEG Ratio = P/E Ratio / EPS Growth Rate.
    Measures valuation relative to earnings growth.

    Args:
        stock_data (dict): Stock data containing info from Yahoo Finance.

    Returns:
        dict: Contains value (ratio), formula, source, and interpretation.
    """
    try:
        info = stock_data.get('info', {})
        peg = info.get('peg_ratio')
        
        if peg is not None and peg > 0:
            return {
                "status": "success",
                "metric": "peg_ratio",
                "value": round(peg, 2),
                "unit": "x",
                "formula": "P/E Ratio / EPS Growth Rate",
                "source": "yahoo_finance.precomputed",
                "interpretation": _interpret_peg(peg),
            }
        
        pe = info.get('trailing_pe')
        earnings_growth = info.get('earnings_growth')
        
        if pe and pe > 0 and earnings_growth and earnings_growth > 0:
            growth_pct = earnings_growth * 100
            if growth_pct > 0:
                peg = pe / growth_pct
                return {
                    "status": "success",
                    "metric": "peg_ratio",
                    "value": round(peg, 2),
                    "unit": "x",
                    "formula": "P/E Ratio / EPS Growth Rate",
                    "source": "calculated.info",
                    "interpretation": _interpret_peg(peg),
                }
        
        forward_pe = info.get('forward_pe')
        if forward_pe and forward_pe > 0:
            trailing_eps = info.get('earnings_per_share')
            forward_eps = info.get('forward_eps')
            
            if trailing_eps and forward_eps and trailing_eps > 0:
                implied_growth = ((forward_eps - trailing_eps) / abs(trailing_eps)) * 100
                if implied_growth > 0:
                    peg = forward_pe / implied_growth
                    return {
                        "status": "success",
                        "metric": "peg_ratio",
                        "value": round(peg, 2),
                        "unit": "x",
                        "formula": "Forward P/E / Implied EPS Growth",
                        "source": "calculated.info",
                        "interpretation": _interpret_peg(peg),
                    }
            
            if earnings_growth and earnings_growth > 0:
                growth_pct = earnings_growth * 100
                peg = forward_pe / growth_pct
                return {
                    "status": "success",
                    "metric": "peg_ratio",
                    "value": round(peg, 2),
                    "unit": "x",
                    "formula": "Forward P/E / Earnings Growth Rate",
                    "source": "calculated.forward",
                    "interpretation": _interpret_peg(peg),
                }
        
        trailing_eps = info.get('earnings_per_share')
        if trailing_eps is not None and trailing_eps < 0:
            return {
                "status": "error",
                "metric": "peg_ratio",
                "value": None,
                "null_reason": "Company has negative earnings - PEG ratio not meaningful",
            }
        
        return {
            "status": "error",
            "metric": "peg_ratio",
            "value": None,
            "null_reason": "PEG ratio not available (requires positive P/E and growth data)",
        }
        
    except Exception as e:
        logger.error(f"Error calculating PEG ratio: {e}")
        return {"status": "error", "metric": "peg_ratio", "error": str(e)}


def calculate_enterprise_value(stock_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Gets Enterprise Value = Market Cap + Total Debt - Cash.
    Measures total company value including debt.

    Args:
        stock_data (dict): Stock data containing info from Yahoo Finance.

    Returns:
        dict: Contains value (dollars), formula, source, and interpretation.
    """
    try:
        info = stock_data.get('info', {})
        ev = info.get('enterprise_value')
        
        if ev is not None:
            value_b = ev / 1e9
            return {
                "status": "success",
                "metric": "enterprise_value",
                "value": round(value_b, 2),
                "unit": "B USD",
                "formula": "Market Cap + Total Debt - Cash",
                "source": "yahoo_finance.precomputed",
                "interpretation": f"Total enterprise value of ${round(value_b, 1)}B",
            }
        
        return {
            "status": "error",
            "metric": "enterprise_value",
            "value": None,
            "null_reason": "Enterprise value not available",
        }
        
    except Exception as e:
        logger.error(f"Error getting enterprise value: {e}")
        return {"status": "error", "metric": "enterprise_value", "error": str(e)}


def calculate_earnings_yield(stock_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates Earnings Yield = EPS / Stock Price * 100.
    Inverse of P/E ratio, shows earnings relative to price.

    Args:
        stock_data (dict): Stock data containing info from Yahoo Finance.

    Returns:
        dict: Contains value (percentage), formula, source, and interpretation.
    """
    try:
        info = stock_data.get('info', {})
        eps = info.get('earnings_per_share')
        price = info.get('current_price')
        
        if eps and price and price > 0:
            value = (eps / price) * 100
            return {
                "status": "success",
                "metric": "earnings_yield",
                "value": round(value, 2),
                "unit": "%",
                "formula": "EPS / Stock Price × 100",
                "source": "calculated.info",
                "interpretation": _interpret_earnings_yield(value),
            }
        
        return {
            "status": "error",
            "metric": "earnings_yield",
            "value": None,
            "null_reason": "Earnings yield not available",
        }
        
    except Exception as e:
        logger.error(f"Error calculating earnings yield: {e}")
        return {"status": "error", "metric": "earnings_yield", "error": str(e)}


def calculate_book_value_per_share(stock_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Gets Book Value Per Share = Shareholders' Equity / Shares Outstanding.
    Measures net asset value per share.

    Args:
        stock_data (dict): Stock data containing info from Yahoo Finance.

    Returns:
        dict: Contains value (dollars), formula, source, and interpretation.
    """
    try:
        info = stock_data.get('info', {})
        bvps = info.get('book_value')
        
        if bvps is not None:
            return {
                "status": "success",
                "metric": "book_value_per_share",
                "value": round(bvps, 2),
                "unit": "USD",
                "formula": "Shareholders' Equity / Shares Outstanding",
                "source": "yahoo_finance.precomputed",
                "interpretation": f"Net asset value of ${round(bvps, 2)} per share",
            }
        
        return {
            "status": "error",
            "metric": "book_value_per_share",
            "value": None,
            "null_reason": "Book value per share not available",
        }
        
    except Exception as e:
        logger.error(f"Error getting book value per share: {e}")
        return {"status": "error", "metric": "book_value_per_share", "error": str(e)}


def calculate_dividend_yield(stock_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Gets Dividend Yield = Annual Dividend / Stock Price * 100.
    Measures income return from dividends.

    Args:
        stock_data (dict): Stock data containing info from Yahoo Finance.

    Returns:
        dict: Contains value (percentage), formula, source, and interpretation.
    """
    try:
        info = stock_data.get('info', {})
        div_yield = info.get('dividend_yield')
        
        if div_yield is not None:
            if div_yield > 1:
                value = div_yield
            else:
                value = div_yield * 100
            
            if value > 20:
                value = value / 100
            
            return {
                "status": "success",
                "metric": "dividend_yield",
                "value": round(value, 2),
                "unit": "%",
                "formula": "Annual Dividend / Stock Price × 100",
                "source": "yahoo_finance.precomputed",
                "interpretation": _interpret_dividend_yield(value),
            }
        
        div_rate = info.get('dividend_rate')
        price = info.get('current_price')
        
        if div_rate and price and price > 0:
            value = (div_rate / price) * 100
            return {
                "status": "success",
                "metric": "dividend_yield",
                "value": round(value, 2),
                "unit": "%",
                "formula": "Annual Dividend / Stock Price × 100",
                "source": "calculated.info",
                "interpretation": _interpret_dividend_yield(value),
            }
        
        return {
            "status": "success",
            "metric": "dividend_yield",
            "value": 0,
            "unit": "%",
            "formula": "Annual Dividend / Stock Price × 100",
            "source": "yahoo_finance.info",
            "interpretation": "Company does not pay dividends",
        }
        
    except Exception as e:
        logger.error(f"Error calculating dividend yield: {e}")
        return {"status": "error", "metric": "dividend_yield", "error": str(e)}


def _interpret_pe(value: float) -> str:
    if value < 15:
        return "Low valuation - potentially undervalued or low growth"
    elif value < 25:
        return "Moderate valuation"
    elif value < 40:
        return "High valuation - high growth expected"
    else:
        return "Very high valuation - requires exceptional growth"


def _interpret_forward_pe(value: float) -> str:
    if value < 15:
        return "Low forward valuation"
    elif value < 20:
        return "Moderate forward valuation"
    elif value < 30:
        return "High forward valuation"
    else:
        return "Very high forward valuation"


def _interpret_pb(value: float) -> str:
    if value < 1:
        return "Trading below book value - potentially undervalued"
    elif value < 3:
        return "Moderate valuation relative to assets"
    elif value < 5:
        return "Premium valuation"
    else:
        return "High premium - asset-light or intangible-heavy business"


def _interpret_ps(value: float) -> str:
    if value < 2:
        return "Low valuation relative to sales"
    elif value < 5:
        return "Moderate valuation"
    elif value < 10:
        return "High valuation"
    else:
        return "Very high valuation relative to sales"


def _interpret_ev_ebitda(value: float) -> str:
    if value < 10:
        return "Low valuation - potentially undervalued"
    elif value < 15:
        return "Moderate valuation"
    elif value < 20:
        return "High valuation"
    else:
        return "Very high valuation"


def _interpret_peg(value: float) -> str:
    if value < 1:
        return "Potentially undervalued relative to growth"
    elif value < 1.5:
        return "Fair valuation relative to growth"
    elif value < 2:
        return "Premium valuation relative to growth"
    else:
        return "High valuation relative to growth rate"


def _interpret_earnings_yield(value: float) -> str:
    if value > 8:
        return "High earnings yield - potentially undervalued"
    elif value > 5:
        return "Moderate earnings yield"
    elif value > 2:
        return "Low earnings yield - growth stock characteristics"
    else:
        return "Very low earnings yield"


def _interpret_dividend_yield(value: float) -> str:
    if value > 5:
        return "High yield - income stock"
    elif value > 2:
        return "Moderate yield"
    elif value > 0:
        return "Low yield - growth focused"
    else:
        return "No dividend"
