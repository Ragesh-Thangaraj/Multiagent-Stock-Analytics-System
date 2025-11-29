"""
Financial Ratio Calculation Tools for ADK Agents

These tools calculate profitability, liquidity, leverage, efficiency, growth, and cashflow metrics.
All calculations use verified formulas and prefer Yahoo Finance precomputed values when available.
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def calculate_gross_margin(stock_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates Gross Margin = (Revenue - Cost of Goods Sold) / Revenue * 100.
    Measures the percentage of revenue retained after direct production costs.

    Args:
        stock_data (dict): Stock data containing fundamentals and info from Yahoo Finance.

    Returns:
        dict: Contains value (percentage), formula, source, and interpretation.
    """
    try:
        info = stock_data.get('info', {})
        gross_margins = info.get('gross_margins')
        
        if gross_margins is not None:
            value = gross_margins * 100
            return {
                "status": "success",
                "metric": "gross_margin",
                "value": round(value, 2),
                "unit": "%",
                "formula": "(Revenue - COGS) / Revenue × 100",
                "source": "yahoo_finance.precomputed",
                "interpretation": _interpret_margin(value, "gross"),
            }
        
        fundamentals = stock_data.get('fundamentals', {})
        income = fundamentals.get('income_statement', {})
        
        if income:
            latest_period = list(income.keys())[0] if income else None
            if latest_period:
                data = income[latest_period]
                revenue = data.get('Total Revenue') or data.get('Operating Revenue')
                gross_profit = data.get('Gross Profit')
                
                if revenue and gross_profit and revenue > 0:
                    value = (gross_profit / revenue) * 100
                    return {
                        "status": "success",
                        "metric": "gross_margin",
                        "value": round(value, 2),
                        "unit": "%",
                        "formula": "(Gross Profit / Revenue) × 100",
                        "source": "calculated.fundamentals",
                        "interpretation": _interpret_margin(value, "gross"),
                    }
        
        return {
            "status": "error",
            "metric": "gross_margin",
            "value": None,
            "null_reason": "Gross margin data not available",
        }
        
    except Exception as e:
        logger.error(f"Error calculating gross margin: {e}")
        return {"status": "error", "metric": "gross_margin", "error": str(e)}


def calculate_operating_margin(stock_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates Operating Margin = Operating Income / Revenue * 100.
    Measures operational efficiency before interest and taxes.

    Args:
        stock_data (dict): Stock data containing fundamentals and info from Yahoo Finance.

    Returns:
        dict: Contains value (percentage), formula, source, and interpretation.
    """
    try:
        info = stock_data.get('info', {})
        operating_margins = info.get('operating_margins')
        
        if operating_margins is not None:
            value = operating_margins * 100
            return {
                "status": "success",
                "metric": "operating_margin",
                "value": round(value, 2),
                "unit": "%",
                "formula": "Operating Income / Revenue × 100",
                "source": "yahoo_finance.precomputed",
                "interpretation": _interpret_margin(value, "operating"),
            }
        
        return {
            "status": "error",
            "metric": "operating_margin",
            "value": None,
            "null_reason": "Operating margin data not available",
        }
        
    except Exception as e:
        logger.error(f"Error calculating operating margin: {e}")
        return {"status": "error", "metric": "operating_margin", "error": str(e)}


def calculate_net_margin(stock_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates Net Profit Margin = Net Income / Revenue * 100.
    Measures overall profitability after all expenses.

    Args:
        stock_data (dict): Stock data containing fundamentals and info from Yahoo Finance.

    Returns:
        dict: Contains value (percentage), formula, source, and interpretation.
    """
    try:
        info = stock_data.get('info', {})
        profit_margins = info.get('profit_margins')
        
        if profit_margins is not None:
            value = profit_margins * 100
            return {
                "status": "success",
                "metric": "net_margin",
                "value": round(value, 2),
                "unit": "%",
                "formula": "Net Income / Revenue × 100",
                "source": "yahoo_finance.precomputed",
                "interpretation": _interpret_margin(value, "net"),
            }
        
        return {
            "status": "error",
            "metric": "net_margin",
            "value": None,
            "null_reason": "Net margin data not available",
        }
        
    except Exception as e:
        logger.error(f"Error calculating net margin: {e}")
        return {"status": "error", "metric": "net_margin", "error": str(e)}


def calculate_roa(stock_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates Return on Assets (ROA) = Net Income / Total Assets * 100.
    Measures how efficiently a company uses its assets to generate profits.

    Args:
        stock_data (dict): Stock data containing fundamentals and info from Yahoo Finance.

    Returns:
        dict: Contains value (percentage), formula, source, and interpretation.
    """
    try:
        info = stock_data.get('info', {})
        roa = info.get('return_on_assets')
        
        if roa is not None:
            value = roa * 100
            return {
                "status": "success",
                "metric": "roa",
                "value": round(value, 2),
                "unit": "%",
                "formula": "Net Income / Total Assets × 100",
                "source": "yahoo_finance.precomputed",
                "interpretation": _interpret_roa(value),
            }
        
        return {
            "status": "error",
            "metric": "roa",
            "value": None,
            "null_reason": "ROA data not available",
        }
        
    except Exception as e:
        logger.error(f"Error calculating ROA: {e}")
        return {"status": "error", "metric": "roa", "error": str(e)}


def calculate_roe(stock_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates Return on Equity (ROE) = Net Income / Shareholders' Equity * 100.
    Measures profitability relative to shareholders' investment.

    Args:
        stock_data (dict): Stock data containing fundamentals and info from Yahoo Finance.

    Returns:
        dict: Contains value (percentage), formula, source, and interpretation.
    """
    try:
        info = stock_data.get('info', {})
        roe = info.get('return_on_equity')
        
        if roe is not None:
            value = roe * 100
            return {
                "status": "success",
                "metric": "roe",
                "value": round(value, 2),
                "unit": "%",
                "formula": "Net Income / Shareholders' Equity × 100",
                "source": "yahoo_finance.precomputed",
                "interpretation": _interpret_roe(value),
            }
        
        return {
            "status": "error",
            "metric": "roe",
            "value": None,
            "null_reason": "ROE data not available",
        }
        
    except Exception as e:
        logger.error(f"Error calculating ROE: {e}")
        return {"status": "error", "metric": "roe", "error": str(e)}


def calculate_roic(stock_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates Return on Invested Capital (ROIC) = NOPAT / Invested Capital * 100.
    Measures how well a company generates returns on capital invested.

    Args:
        stock_data (dict): Stock data containing fundamentals from Yahoo Finance.

    Returns:
        dict: Contains value (percentage), formula, source, and interpretation.
    """
    try:
        fundamentals = stock_data.get('fundamentals', {})
        income = fundamentals.get('income_statement', {})
        balance = fundamentals.get('balance_sheet', {})
        
        if income and balance:
            latest_income = list(income.keys())[0] if income else None
            latest_balance = list(balance.keys())[0] if balance else None
            
            if latest_income and latest_balance:
                income_data = income[latest_income]
                balance_data = balance[latest_balance]
                
                operating_income = income_data.get('Operating Income') or income_data.get('EBIT')
                tax_rate = 0.21
                
                total_debt = balance_data.get('Total Debt') or balance_data.get('Long Term Debt') or 0
                equity = balance_data.get('Stockholders Equity') or balance_data.get('Total Equity Gross Minority Interest')
                cash = balance_data.get('Cash And Cash Equivalents') or 0
                
                if operating_income and equity:
                    nopat = operating_income * (1 - tax_rate)
                    invested_capital = (total_debt or 0) + (equity or 0) - (cash or 0)
                    
                    if invested_capital > 0:
                        value = (nopat / invested_capital) * 100
                        return {
                            "status": "success",
                            "metric": "roic",
                            "value": round(value, 2),
                            "unit": "%",
                            "formula": "NOPAT / (Total Debt + Equity - Cash) × 100",
                            "source": "calculated.fundamentals",
                            "interpretation": _interpret_roic(value),
                        }
        
        return {
            "status": "error",
            "metric": "roic",
            "value": None,
            "null_reason": "ROIC calculation data not available",
        }
        
    except Exception as e:
        logger.error(f"Error calculating ROIC: {e}")
        return {"status": "error", "metric": "roic", "error": str(e)}


def calculate_current_ratio(stock_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates Current Ratio = Current Assets / Current Liabilities.
    Measures short-term liquidity and ability to pay near-term obligations.

    Args:
        stock_data (dict): Stock data containing fundamentals and info from Yahoo Finance.

    Returns:
        dict: Contains value (ratio), formula, source, and interpretation.
    """
    try:
        info = stock_data.get('info', {})
        current_ratio = info.get('current_ratio')
        
        if current_ratio is not None:
            return {
                "status": "success",
                "metric": "current_ratio",
                "value": round(current_ratio, 2),
                "unit": "x",
                "formula": "Current Assets / Current Liabilities",
                "source": "yahoo_finance.precomputed",
                "interpretation": _interpret_current_ratio(current_ratio),
            }
        
        return {
            "status": "error",
            "metric": "current_ratio",
            "value": None,
            "null_reason": "Current ratio data not available",
        }
        
    except Exception as e:
        logger.error(f"Error calculating current ratio: {e}")
        return {"status": "error", "metric": "current_ratio", "error": str(e)}


def calculate_quick_ratio(stock_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates Quick Ratio = (Current Assets - Inventory) / Current Liabilities.
    Measures liquidity excluding inventory (more conservative than current ratio).

    Args:
        stock_data (dict): Stock data containing fundamentals and info from Yahoo Finance.

    Returns:
        dict: Contains value (ratio), formula, source, and interpretation.
    """
    try:
        info = stock_data.get('info', {})
        quick_ratio = info.get('quick_ratio')
        
        if quick_ratio is not None:
            return {
                "status": "success",
                "metric": "quick_ratio",
                "value": round(quick_ratio, 2),
                "unit": "x",
                "formula": "(Current Assets - Inventory) / Current Liabilities",
                "source": "yahoo_finance.precomputed",
                "interpretation": _interpret_quick_ratio(quick_ratio),
            }
        
        return {
            "status": "error",
            "metric": "quick_ratio",
            "value": None,
            "null_reason": "Quick ratio data not available",
        }
        
    except Exception as e:
        logger.error(f"Error calculating quick ratio: {e}")
        return {"status": "error", "metric": "quick_ratio", "error": str(e)}


def calculate_cash_ratio(stock_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates Cash Ratio = Cash / Current Liabilities.
    The most conservative liquidity measure - only cash and equivalents.

    Args:
        stock_data (dict): Stock data containing fundamentals from Yahoo Finance.

    Returns:
        dict: Contains value (ratio), formula, source, and interpretation.
    """
    try:
        fundamentals = stock_data.get('fundamentals', {})
        balance = fundamentals.get('balance_sheet', {})
        
        if balance:
            latest = list(balance.keys())[0] if balance else None
            if latest:
                data = balance[latest]
                cash = data.get('Cash And Cash Equivalents') or data.get('Cash Cash Equivalents And Short Term Investments')
                current_liabilities = data.get('Current Liabilities')
                
                if cash and current_liabilities and current_liabilities > 0:
                    value = cash / current_liabilities
                    return {
                        "status": "success",
                        "metric": "cash_ratio",
                        "value": round(value, 2),
                        "unit": "x",
                        "formula": "Cash / Current Liabilities",
                        "source": "calculated.fundamentals",
                        "interpretation": _interpret_cash_ratio(value),
                    }
        
        return {
            "status": "error",
            "metric": "cash_ratio",
            "value": None,
            "null_reason": "Cash ratio data not available",
        }
        
    except Exception as e:
        logger.error(f"Error calculating cash ratio: {e}")
        return {"status": "error", "metric": "cash_ratio", "error": str(e)}


def calculate_working_capital(stock_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates Working Capital = Current Assets - Current Liabilities.
    Measures short-term financial health and operational efficiency.

    Args:
        stock_data (dict): Stock data containing fundamentals from Yahoo Finance.

    Returns:
        dict: Contains value (dollars), formula, source, and interpretation.
    """
    try:
        fundamentals = stock_data.get('fundamentals', {})
        balance = fundamentals.get('balance_sheet', {})
        
        if balance:
            latest = list(balance.keys())[0] if balance else None
            if latest:
                data = balance[latest]
                current_assets = data.get('Current Assets')
                current_liabilities = data.get('Current Liabilities')
                
                if current_assets is not None and current_liabilities is not None:
                    value = current_assets - current_liabilities
                    return {
                        "status": "success",
                        "metric": "working_capital",
                        "value": round(value / 1e9, 2),
                        "unit": "B USD",
                        "formula": "Current Assets - Current Liabilities",
                        "source": "calculated.fundamentals",
                        "interpretation": "Positive" if value > 0 else "Negative - potential liquidity concern",
                    }
        
        return {
            "status": "error",
            "metric": "working_capital",
            "value": None,
            "null_reason": "Working capital data not available",
        }
        
    except Exception as e:
        logger.error(f"Error calculating working capital: {e}")
        return {"status": "error", "metric": "working_capital", "error": str(e)}


def calculate_debt_to_equity(stock_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates Debt-to-Equity Ratio = Total Debt / Shareholders' Equity.
    Measures financial leverage and capital structure risk.

    Args:
        stock_data (dict): Stock data containing fundamentals and info from Yahoo Finance.

    Returns:
        dict: Contains value (ratio), formula, source, and interpretation.
    """
    try:
        info = stock_data.get('info', {})
        d_e = info.get('debt_to_equity')
        
        if d_e is not None:
            value = d_e / 100 if d_e > 10 else d_e
            return {
                "status": "success",
                "metric": "debt_to_equity",
                "value": round(value, 2),
                "unit": "x",
                "formula": "Total Debt / Shareholders' Equity",
                "source": "yahoo_finance.precomputed",
                "interpretation": _interpret_debt_to_equity(value),
            }
        
        return {
            "status": "error",
            "metric": "debt_to_equity",
            "value": None,
            "null_reason": "Debt-to-equity data not available",
        }
        
    except Exception as e:
        logger.error(f"Error calculating debt-to-equity: {e}")
        return {"status": "error", "metric": "debt_to_equity", "error": str(e)}


def calculate_debt_to_assets(stock_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates Debt-to-Assets Ratio = Total Debt / Total Assets.
    Measures the proportion of assets financed by debt.

    Args:
        stock_data (dict): Stock data containing fundamentals from Yahoo Finance.

    Returns:
        dict: Contains value (ratio), formula, source, and interpretation.
    """
    try:
        info = stock_data.get('info', {})
        total_debt = info.get('total_debt')
        total_assets = info.get('total_assets')
        
        if total_debt is not None and total_assets and total_assets > 0:
            value = total_debt / total_assets
            return {
                "status": "success",
                "metric": "debt_to_assets",
                "value": round(value, 2),
                "unit": "x",
                "formula": "Total Debt / Total Assets",
                "source": "calculated.info",
                "interpretation": _interpret_debt_to_assets(value),
            }
        
        fundamentals = stock_data.get('fundamentals', {})
        balance = fundamentals.get('balance_sheet', {})
        
        if balance:
            latest = list(balance.keys())[0] if balance else None
            if latest:
                data = balance[latest]
                debt = data.get('Total Debt') or data.get('Long Term Debt') or 0
                short_debt = data.get('Current Debt') or data.get('Short Long Term Debt') or 0
                total_debt_calc = debt + short_debt
                assets = data.get('Total Assets')
                
                if total_debt_calc and assets and assets > 0:
                    value = total_debt_calc / assets
                    return {
                        "status": "success",
                        "metric": "debt_to_assets",
                        "value": round(value, 2),
                        "unit": "x",
                        "formula": "Total Debt / Total Assets",
                        "source": "calculated.fundamentals",
                        "interpretation": _interpret_debt_to_assets(value),
                    }
        
        return {
            "status": "error",
            "metric": "debt_to_assets",
            "value": None,
            "null_reason": "Debt-to-assets data not available",
        }
        
    except Exception as e:
        logger.error(f"Error calculating debt-to-assets: {e}")
        return {"status": "error", "metric": "debt_to_assets", "error": str(e)}


def calculate_interest_coverage(stock_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates Interest Coverage Ratio = EBIT / Interest Expense.
    Measures ability to pay interest on outstanding debt.

    Args:
        stock_data (dict): Stock data containing fundamentals from Yahoo Finance.

    Returns:
        dict: Contains value (ratio), formula, source, and interpretation.
    """
    try:
        fundamentals = stock_data.get('fundamentals', {})
        income = fundamentals.get('income_statement', {})
        
        if income:
            latest = list(income.keys())[0] if income else None
            if latest:
                data = income[latest]
                ebit = data.get('EBIT') or data.get('Operating Income')
                interest = data.get('Interest Expense') or data.get('Interest Expense Non Operating')
                
                if not interest:
                    net_interest = data.get('Net Interest Income')
                    if net_interest and net_interest < 0:
                        interest = abs(net_interest)
                
                if ebit and interest and abs(interest) > 0:
                    value = abs(ebit / interest)
                    return {
                        "status": "success",
                        "metric": "interest_coverage",
                        "value": round(value, 2),
                        "unit": "x",
                        "formula": "EBIT / Interest Expense",
                        "source": "calculated.fundamentals",
                        "interpretation": _interpret_interest_coverage(value),
                    }
                elif ebit and (not interest or interest == 0):
                    return {
                        "status": "success",
                        "metric": "interest_coverage",
                        "value": None,
                        "null_reason": "No interest expense (debt-free company)",
                        "interpretation": "Company has no interest expense - excellent financial position",
                    }
        
        return {
            "status": "error",
            "metric": "interest_coverage",
            "value": None,
            "null_reason": "Interest coverage data not available",
        }
        
    except Exception as e:
        logger.error(f"Error calculating interest coverage: {e}")
        return {"status": "error", "metric": "interest_coverage", "error": str(e)}


def calculate_asset_turnover(stock_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates Asset Turnover = Revenue / Total Assets.
    Measures efficiency of asset utilization to generate revenue.

    Args:
        stock_data (dict): Stock data containing fundamentals from Yahoo Finance.

    Returns:
        dict: Contains value (ratio), formula, source, and interpretation.
    """
    try:
        info = stock_data.get('info', {})
        revenue = info.get('revenue') or info.get('totalRevenue')
        total_assets = info.get('total_assets') or info.get('totalAssets')
        
        if revenue and total_assets and total_assets > 0:
            value = revenue / total_assets
            return {
                "status": "success",
                "metric": "asset_turnover",
                "value": round(value, 2),
                "unit": "x",
                "formula": "Revenue / Total Assets",
                "source": "calculated.info",
                "interpretation": _interpret_asset_turnover(value),
            }
        
        fundamentals = stock_data.get('fundamentals', {})
        income = fundamentals.get('income_statement', {})
        balance = fundamentals.get('balance_sheet', {})
        
        if income and balance:
            latest_income = list(income.keys())[0] if income else None
            latest_balance = list(balance.keys())[0] if balance else None
            
            if latest_income and latest_balance:
                revenue = income[latest_income].get('Total Revenue') or income[latest_income].get('Operating Revenue')
                total_assets = balance[latest_balance].get('Total Assets')
                
                if revenue and total_assets and total_assets > 0:
                    value = revenue / total_assets
                    return {
                        "status": "success",
                        "metric": "asset_turnover",
                        "value": round(value, 2),
                        "unit": "x",
                        "formula": "Revenue / Total Assets",
                        "source": "calculated.fundamentals",
                        "interpretation": _interpret_asset_turnover(value),
                    }
        
        return {
            "status": "error",
            "metric": "asset_turnover",
            "value": None,
            "null_reason": "Asset turnover data not available",
        }
        
    except Exception as e:
        logger.error(f"Error calculating asset turnover: {e}")
        return {"status": "error", "metric": "asset_turnover", "error": str(e)}


def calculate_inventory_turnover(stock_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates Inventory Turnover = Cost of Goods Sold / Average Inventory.
    Measures how efficiently inventory is managed.

    Args:
        stock_data (dict): Stock data containing fundamentals from Yahoo Finance.

    Returns:
        dict: Contains value (ratio), formula, source, and interpretation.
    """
    try:
        info = stock_data.get('info', {})
        fundamentals = stock_data.get('fundamentals', {})
        income = fundamentals.get('income_statement', {})
        balance = fundamentals.get('balance_sheet', {})
        
        sector = info.get('sector', '')
        industry = info.get('industry', '')
        
        service_sectors = ['Communication Services', 'Financial Services', 'Technology', 
                          'Healthcare', 'Real Estate', 'Utilities']
        service_industries = ['Entertainment', 'Software', 'Banks', 'Insurance', 
                             'Broadcasting', 'Media', 'Consulting', 'Services']
        
        if income and balance:
            latest_income = list(income.keys())[0] if income else None
            latest_balance = list(balance.keys())[0] if balance else None
            
            if latest_income and latest_balance:
                cogs = income[latest_income].get('Cost Of Revenue')
                inventory = balance[latest_balance].get('Inventory')
                
                if cogs and inventory and inventory > 0:
                    value = cogs / inventory
                    return {
                        "status": "success",
                        "metric": "inventory_turnover",
                        "value": round(value, 2),
                        "unit": "x",
                        "formula": "COGS / Inventory",
                        "source": "calculated.fundamentals",
                        "interpretation": f"Inventory cycles {round(value, 1)} times per year",
                    }
                elif not inventory:
                    if sector in service_sectors or any(ind in industry for ind in service_industries):
                        return {
                            "status": "success",
                            "metric": "inventory_turnover",
                            "value": None,
                            "null_reason": f"Not applicable - {industry or sector} companies don't hold physical inventory",
                        }
                    return {
                        "status": "success",
                        "metric": "inventory_turnover",
                        "value": None,
                        "null_reason": "Company has no inventory on balance sheet",
                    }
        
        if sector in service_sectors or any(ind in industry for ind in service_industries):
            return {
                "status": "success",
                "metric": "inventory_turnover",
                "value": None,
                "null_reason": f"Not applicable - {industry or sector} companies don't hold physical inventory",
            }
        
        return {
            "status": "error",
            "metric": "inventory_turnover",
            "value": None,
            "null_reason": "Inventory turnover data not available",
        }
        
    except Exception as e:
        logger.error(f"Error calculating inventory turnover: {e}")
        return {"status": "error", "metric": "inventory_turnover", "error": str(e)}


def calculate_receivables_turnover(stock_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates Receivables Turnover = Revenue / Accounts Receivable.
    Measures how efficiently the company collects receivables.

    Args:
        stock_data (dict): Stock data containing fundamentals from Yahoo Finance.

    Returns:
        dict: Contains value (ratio), formula, source, and interpretation.
    """
    try:
        info = stock_data.get('info', {})
        fundamentals = stock_data.get('fundamentals', {})
        balance = fundamentals.get('balance_sheet', {})
        
        revenue = info.get('revenue')
        
        if balance and revenue:
            latest = list(balance.keys())[0] if balance else None
            if latest:
                receivables = balance[latest].get('Accounts Receivable') or balance[latest].get('Net Receivables')
                
                if receivables and receivables > 0:
                    value = revenue / receivables
                    return {
                        "status": "success",
                        "metric": "receivables_turnover",
                        "value": round(value, 2),
                        "unit": "x",
                        "formula": "Revenue / Accounts Receivable",
                        "source": "calculated.fundamentals",
                        "interpretation": f"Collects receivables {round(value, 1)} times per year",
                    }
        
        return {
            "status": "error",
            "metric": "receivables_turnover",
            "value": None,
            "null_reason": "Receivables turnover data not available",
        }
        
    except Exception as e:
        logger.error(f"Error calculating receivables turnover: {e}")
        return {"status": "error", "metric": "receivables_turnover", "error": str(e)}


def calculate_revenue_growth(stock_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates Year-over-Year Revenue Growth = (Current Revenue - Prior Revenue) / Prior Revenue * 100.
    Measures the rate of revenue expansion.

    Args:
        stock_data (dict): Stock data containing fundamentals and info from Yahoo Finance.

    Returns:
        dict: Contains value (percentage), formula, source, and interpretation.
    """
    try:
        info = stock_data.get('info', {})
        revenue_growth = info.get('revenue_growth')
        
        if revenue_growth is not None:
            value = revenue_growth * 100
            return {
                "status": "success",
                "metric": "revenue_growth",
                "value": round(value, 2),
                "unit": "%",
                "formula": "(Current Revenue - Prior Revenue) / Prior Revenue × 100",
                "source": "yahoo_finance.precomputed",
                "interpretation": _interpret_growth(value, "Revenue"),
            }
        
        return {
            "status": "error",
            "metric": "revenue_growth",
            "value": None,
            "null_reason": "Revenue growth data not available",
        }
        
    except Exception as e:
        logger.error(f"Error calculating revenue growth: {e}")
        return {"status": "error", "metric": "revenue_growth", "error": str(e)}


def calculate_net_income_growth(stock_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates Year-over-Year Net Income Growth.
    Measures the rate of profit expansion.

    Args:
        stock_data (dict): Stock data containing fundamentals and info from Yahoo Finance.

    Returns:
        dict: Contains value (percentage), formula, source, and interpretation.
    """
    try:
        info = stock_data.get('info', {})
        earnings_growth = info.get('earnings_growth')
        
        if earnings_growth is not None:
            value = earnings_growth * 100
            return {
                "status": "success",
                "metric": "net_income_growth",
                "value": round(value, 2),
                "unit": "%",
                "formula": "(Current Net Income - Prior Net Income) / Prior Net Income × 100",
                "source": "yahoo_finance.precomputed",
                "interpretation": _interpret_growth(value, "Net Income"),
            }
        
        return {
            "status": "error",
            "metric": "net_income_growth",
            "value": None,
            "null_reason": "Net income growth data not available",
        }
        
    except Exception as e:
        logger.error(f"Error calculating net income growth: {e}")
        return {"status": "error", "metric": "net_income_growth", "error": str(e)}


def calculate_eps_growth(stock_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates Earnings Per Share Growth.
    Measures the rate of EPS expansion.

    Args:
        stock_data (dict): Stock data containing info from Yahoo Finance.

    Returns:
        dict: Contains value (percentage), formula, source, and interpretation.
    """
    try:
        info = stock_data.get('info', {})
        trailing_eps = info.get('earnings_per_share')
        forward_eps = info.get('forward_eps')
        
        if trailing_eps and forward_eps and trailing_eps != 0:
            growth = ((forward_eps - trailing_eps) / abs(trailing_eps)) * 100
            return {
                "status": "success",
                "metric": "eps_growth",
                "value": round(growth, 2),
                "unit": "%",
                "formula": "(Forward EPS - Trailing EPS) / Trailing EPS × 100",
                "source": "calculated.info",
                "interpretation": _interpret_growth(growth, "EPS"),
            }
        
        return {
            "status": "error",
            "metric": "eps_growth",
            "value": None,
            "null_reason": "EPS growth data not available",
        }
        
    except Exception as e:
        logger.error(f"Error calculating EPS growth: {e}")
        return {"status": "error", "metric": "eps_growth", "error": str(e)}


def calculate_fcf_growth(stock_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates Free Cash Flow Growth.
    Measures the rate of FCF expansion.

    Args:
        stock_data (dict): Stock data containing fundamentals from Yahoo Finance.

    Returns:
        dict: Contains value (percentage), formula, source, and interpretation.
    """
    try:
        fundamentals = stock_data.get('fundamentals', {})
        cashflow = fundamentals.get('cashflow', {})
        
        if cashflow and len(cashflow) >= 2:
            periods = list(cashflow.keys())
            current = cashflow[periods[0]]
            prior = cashflow[periods[1]]
            
            current_fcf = current.get('Free Cash Flow')
            prior_fcf = prior.get('Free Cash Flow')
            
            if current_fcf and prior_fcf and prior_fcf != 0:
                growth = ((current_fcf - prior_fcf) / abs(prior_fcf)) * 100
                return {
                    "status": "success",
                    "metric": "fcf_growth",
                    "value": round(growth, 2),
                    "unit": "%",
                    "formula": "(Current FCF - Prior FCF) / Prior FCF × 100",
                    "source": "calculated.fundamentals",
                    "interpretation": _interpret_growth(growth, "Free Cash Flow"),
                }
        
        return {
            "status": "error",
            "metric": "fcf_growth",
            "value": None,
            "null_reason": "FCF growth data not available",
        }
        
    except Exception as e:
        logger.error(f"Error calculating FCF growth: {e}")
        return {"status": "error", "metric": "fcf_growth", "error": str(e)}


def calculate_operating_income_growth(stock_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates Operating Income (EBIT) Growth YoY.
    Measures the rate of operating profit expansion.

    Args:
        stock_data (dict): Stock data containing fundamentals from Yahoo Finance.

    Returns:
        dict: Contains value (percentage), formula, source, and interpretation.
    """
    try:
        fundamentals = stock_data.get('fundamentals', {})
        income = fundamentals.get('income_statement', {})
        
        if income and len(income) >= 2:
            periods = list(income.keys())
            current = income[periods[0]]
            prior = income[periods[1]]
            
            current_oi = current.get('Operating Income') or current.get('EBIT')
            prior_oi = prior.get('Operating Income') or prior.get('EBIT')
            
            if current_oi and prior_oi and prior_oi != 0:
                growth = ((current_oi - prior_oi) / abs(prior_oi)) * 100
                return {
                    "status": "success",
                    "metric": "operating_income_growth",
                    "value": round(growth, 2),
                    "unit": "%",
                    "formula": "(Current EBIT - Prior EBIT) / Prior EBIT × 100",
                    "source": "calculated.fundamentals",
                    "interpretation": _interpret_growth(growth, "Operating Income"),
                }
        
        return {
            "status": "error",
            "metric": "operating_income_growth",
            "value": None,
            "null_reason": "Operating income growth data not available",
        }
        
    except Exception as e:
        logger.error(f"Error calculating operating income growth: {e}")
        return {"status": "error", "metric": "operating_income_growth", "error": str(e)}


def calculate_free_cash_flow(stock_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Gets Free Cash Flow = Operating Cash Flow - Capital Expenditures.
    Measures cash available for distribution after maintaining assets.

    Args:
        stock_data (dict): Stock data containing info from Yahoo Finance.

    Returns:
        dict: Contains value (dollars), formula, source, and interpretation.
    """
    try:
        info = stock_data.get('info', {})
        fcf = info.get('free_cash_flow')
        
        if fcf is not None:
            value_b = fcf / 1e9
            return {
                "status": "success",
                "metric": "free_cash_flow",
                "value": round(value_b, 2),
                "unit": "B USD",
                "formula": "Operating Cash Flow - Capital Expenditures",
                "source": "yahoo_finance.precomputed",
                "interpretation": "Positive" if fcf > 0 else "Negative - cash burn",
            }
        
        return {
            "status": "error",
            "metric": "free_cash_flow",
            "value": None,
            "null_reason": "Free cash flow data not available",
        }
        
    except Exception as e:
        logger.error(f"Error getting free cash flow: {e}")
        return {"status": "error", "metric": "free_cash_flow", "error": str(e)}


def calculate_operating_cash_flow_ratio(stock_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates Operating Cash Flow Ratio = Operating Cash Flow / Current Liabilities.
    Measures ability to pay short-term obligations from operations.

    Args:
        stock_data (dict): Stock data containing fundamentals from Yahoo Finance.

    Returns:
        dict: Contains value (ratio), formula, source, and interpretation.
    """
    try:
        info = stock_data.get('info', {})
        fundamentals = stock_data.get('fundamentals', {})
        balance = fundamentals.get('balance_sheet', {})
        
        ocf = info.get('operating_cash_flow')
        
        if balance and ocf:
            latest = list(balance.keys())[0] if balance else None
            if latest:
                current_liabilities = balance[latest].get('Current Liabilities')
                
                if current_liabilities and current_liabilities > 0:
                    value = ocf / current_liabilities
                    return {
                        "status": "success",
                        "metric": "operating_cash_flow_ratio",
                        "value": round(value, 2),
                        "unit": "x",
                        "formula": "Operating Cash Flow / Current Liabilities",
                        "source": "calculated.info",
                        "interpretation": "Strong" if value > 1 else "Weak cash coverage",
                    }
        
        return {
            "status": "error",
            "metric": "operating_cash_flow_ratio",
            "value": None,
            "null_reason": "Operating cash flow ratio data not available",
        }
        
    except Exception as e:
        logger.error(f"Error calculating OCF ratio: {e}")
        return {"status": "error", "metric": "operating_cash_flow_ratio", "error": str(e)}


def calculate_cash_flow_margin(stock_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates Cash Flow Margin = Operating Cash Flow / Revenue * 100.
    Measures cash generation efficiency relative to sales.

    Args:
        stock_data (dict): Stock data containing info from Yahoo Finance.

    Returns:
        dict: Contains value (percentage), formula, source, and interpretation.
    """
    try:
        info = stock_data.get('info', {})
        ocf = info.get('operating_cash_flow')
        revenue = info.get('revenue')
        
        if ocf and revenue and revenue > 0:
            value = (ocf / revenue) * 100
            return {
                "status": "success",
                "metric": "cash_flow_margin",
                "value": round(value, 2),
                "unit": "%",
                "formula": "Operating Cash Flow / Revenue × 100",
                "source": "calculated.info",
                "interpretation": _interpret_margin(value, "cash flow"),
            }
        
        return {
            "status": "error",
            "metric": "cash_flow_margin",
            "value": None,
            "null_reason": "Cash flow margin data not available",
        }
        
    except Exception as e:
        logger.error(f"Error calculating cash flow margin: {e}")
        return {"status": "error", "metric": "cash_flow_margin", "error": str(e)}


def _interpret_margin(value: float, margin_type: str) -> str:
    if margin_type == "gross":
        if value > 50:
            return "Excellent - strong pricing power"
        elif value > 30:
            return "Good - healthy margins"
        elif value > 20:
            return "Moderate - competitive industry"
        else:
            return "Low - may indicate pricing pressure"
    elif margin_type == "operating":
        if value > 25:
            return "Excellent - efficient operations"
        elif value > 15:
            return "Good - well-managed costs"
        elif value > 10:
            return "Moderate"
        else:
            return "Low - may need cost improvements"
    else:
        if value > 20:
            return "Excellent"
        elif value > 10:
            return "Good"
        elif value > 5:
            return "Moderate"
        else:
            return "Low"


def _interpret_roa(value: float) -> str:
    if value > 15:
        return "Excellent - highly efficient asset utilization"
    elif value > 10:
        return "Good - efficient use of assets"
    elif value > 5:
        return "Moderate"
    else:
        return "Low - may indicate inefficiency"


def _interpret_roe(value: float) -> str:
    if value > 20:
        return "Excellent - strong returns for shareholders"
    elif value > 15:
        return "Good"
    elif value > 10:
        return "Moderate"
    else:
        return "Low"


def _interpret_roic(value: float) -> str:
    if value > 15:
        return "Excellent - creating significant value"
    elif value > 10:
        return "Good - creating value"
    elif value > 5:
        return "Moderate"
    else:
        return "Low - may be destroying value"


def _interpret_current_ratio(value: float) -> str:
    if value > 2:
        return "Strong liquidity"
    elif value > 1.5:
        return "Adequate liquidity"
    elif value > 1:
        return "Acceptable"
    else:
        return "Potential liquidity risk"


def _interpret_quick_ratio(value: float) -> str:
    if value > 1.5:
        return "Strong liquidity"
    elif value > 1:
        return "Adequate liquidity"
    else:
        return "May face short-term challenges"


def _interpret_cash_ratio(value: float) -> str:
    if value > 1:
        return "Very strong cash position"
    elif value > 0.5:
        return "Adequate cash"
    else:
        return "Limited cash cushion"


def _interpret_debt_to_equity(value: float) -> str:
    if value < 0.5:
        return "Conservative - low leverage"
    elif value < 1:
        return "Moderate leverage"
    elif value < 2:
        return "Higher leverage"
    else:
        return "High leverage - potential risk"


def _interpret_debt_to_assets(value: float) -> str:
    if value < 0.3:
        return "Conservative - low debt reliance"
    elif value < 0.5:
        return "Moderate"
    else:
        return "High debt reliance"


def _interpret_interest_coverage(value: float) -> str:
    if value > 10:
        return "Excellent - easily covers interest"
    elif value > 5:
        return "Good"
    elif value > 2:
        return "Adequate"
    else:
        return "Low - potential debt service risk"


def _interpret_asset_turnover(value: float) -> str:
    if value > 1.5:
        return "Efficient asset utilization"
    elif value > 1:
        return "Moderate efficiency"
    else:
        return "Lower efficiency - capital intensive"


def _interpret_growth(value: float, metric_name: str) -> str:
    if value > 20:
        return f"Strong {metric_name} growth"
    elif value > 10:
        return f"Healthy {metric_name} growth"
    elif value > 0:
        return f"Modest {metric_name} growth"
    elif value > -10:
        return f"Slight {metric_name} decline"
    else:
        return f"Significant {metric_name} decline"
