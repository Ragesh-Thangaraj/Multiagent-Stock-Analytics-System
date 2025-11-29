"""
Yahoo Finance Data Client

Fetches stock data from Yahoo Finance using yfinance library.
Provides price history, fundamentals, and company information.
"""

import yfinance as yf
import math
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class YahooFinanceClient:
    """Client for fetching data from Yahoo Finance."""
    
    def __init__(self):
        self.version = "yfinance-0.2.x"
    
    def fetch_stock_data(self, ticker: str, period: str = "1y") -> Dict[str, Any]:
        """
        Fetch comprehensive stock data from Yahoo Finance.
        
        Args:
            ticker: Stock symbol (e.g., "AAPL")
            period: Historical period (default "1y")
            
        Returns:
            Dictionary containing price history, fundamentals, and metadata
        """
        try:
            stock = yf.Ticker(ticker)
            
            hist = stock.history(period=period)
            price_history = []
            for idx, row in hist.iterrows():
                try:
                    if hasattr(idx, 'strftime'):
                        date_str = idx.strftime("%Y-%m-%d")
                    elif hasattr(idx, 'isoformat'):
                        date_str = str(idx)[:10]
                    else:
                        date_str = str(idx)[:10]
                except Exception:
                    date_str = str(idx)[:10]
                
                price_history.append({
                    "date": date_str,
                    "open": float(row["Open"]) if row["Open"] is not None else None,
                    "high": float(row["High"]) if row["High"] is not None else None,
                    "low": float(row["Low"]) if row["Low"] is not None else None,
                    "close": float(row["Close"]) if row["Close"] is not None else None,
                    "volume": int(row["Volume"]) if row["Volume"] is not None else None
                })
            
            info = stock.info
            
            balance_sheet = stock.balance_sheet
            income_stmt = stock.income_stmt
            cashflow = stock.cashflow
            
            fundamentals = self._build_fundamentals(info, balance_sheet, income_stmt, cashflow)
            
            return {
                "success": True,
                "ticker": ticker.upper(),
                "company_name": info.get("longName", info.get("shortName", ticker)),
                "exchange": info.get("exchange", "UNKNOWN"),
                "currency": info.get("currency", "USD"),
                "price_history": price_history,
                "fundamentals": fundamentals,
                "info": info
            }
            
        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {str(e)}")
            return {
                "success": False,
                "ticker": ticker,
                "error": str(e),
                "null_reason": "yahoo_api_error"
            }
    
    def _build_fundamentals(
        self,
        info: Dict,
        balance_sheet: Any,
        income_stmt: Any,
        cashflow: Any
    ) -> Dict[str, Any]:
        """Build fundamentals dictionary from Yahoo Finance data."""
        
        fundamentals = {
            "shares_outstanding": info.get("sharesOutstanding"),
            "market_cap": info.get("marketCap"),
            "enterprise_value": info.get("enterpriseValue"),
            "income_statement": {},
            "balance_sheet": {},
            "cashflow_statement": {},
            "precomputed_ratios": {
                "trailing_pe": info.get("trailingPE"),
                "forward_pe": info.get("forwardPE"),
                "price_to_book": info.get("priceToBook"),
                "price_to_sales": info.get("priceToSalesTrailing12Months"),
                "ev_to_ebitda": info.get("enterpriseToEbitda"),
                "peg_ratio": info.get("pegRatio"),
                "return_on_equity": info.get("returnOnEquity"),
                "return_on_assets": info.get("returnOnAssets"),
                "profit_margin": info.get("profitMargins"),
                "gross_margin": info.get("grossMargins"),
                "operating_margin": info.get("operatingMargins"),
                "current_ratio": info.get("currentRatio"),
                "quick_ratio": info.get("quickRatio"),
                "debt_to_equity": info.get("debtToEquity"),
                "beta": info.get("beta"),
                "dividend_yield": info.get("dividendYield"),
                "payout_ratio": info.get("payoutRatio"),
                "book_value": info.get("bookValue"),
                "earnings_growth": info.get("earningsGrowth"),
                "revenue_growth": info.get("revenueGrowth"),
                "free_cashflow": info.get("freeCashflow"),
                "earnings_per_share": info.get("trailingEps"),
                "forward_eps": info.get("forwardEps"),
                "industry": info.get("industry"),
                "sector": info.get("sector"),
            }
        }
        
        if income_stmt is not None and not income_stmt.empty:
            latest_income = income_stmt.iloc[:, 0]
            fundamentals["income_statement"] = {
                "revenue": self._safe_get(latest_income, "Total Revenue"),
                "cogs": self._safe_get(latest_income, "Cost Of Revenue"),
                "gross_profit": self._safe_get(latest_income, "Gross Profit"),
                "operating_income": self._safe_get(latest_income, "Operating Income"),
                "ebit": self._safe_get(latest_income, "EBIT"),
                "ebitda": self._safe_get(latest_income, "EBITDA"),
                "net_income": self._safe_get(latest_income, "Net Income"),
                "interest_expense": abs(self._safe_get(latest_income, "Interest Expense", 0) or 0),
            }
            
            revenue = fundamentals["income_statement"].get("revenue")
            cogs = fundamentals["income_statement"].get("cogs")
            if revenue and cogs:
                fundamentals["income_statement"]["gross_profit"] = revenue - cogs
        
        if balance_sheet is not None and not balance_sheet.empty:
            latest_balance = balance_sheet.iloc[:, 0]
            fundamentals["balance_sheet"] = {
                "total_assets": self._safe_get(latest_balance, "Total Assets"),
                "current_assets": self._safe_get(latest_balance, "Current Assets"),
                "cash_and_equivalents": self._safe_get(latest_balance, "Cash And Cash Equivalents"),
                "accounts_receivable": self._safe_get(latest_balance, "Accounts Receivable"),
                "inventory": self._safe_get(latest_balance, "Inventory"),
                "total_liabilities": self._safe_get(latest_balance, "Total Liabilities Net Minority Interest"),
                "current_liabilities": self._safe_get(latest_balance, "Current Liabilities"),
                "accounts_payable": self._safe_get(latest_balance, "Accounts Payable"),
                "total_debt": self._safe_get(latest_balance, "Total Debt"),
                "shareholders_equity": self._safe_get(latest_balance, "Stockholders Equity"),
            }
        
        if cashflow is not None and not cashflow.empty:
            latest_cashflow = cashflow.iloc[:, 0]
            fundamentals["cashflow_statement"] = {
                "operating_cashflow": self._safe_get(latest_cashflow, "Operating Cash Flow"),
                "capital_expenditures": self._safe_get(latest_cashflow, "Capital Expenditure"),
                "free_cashflow": self._safe_get(latest_cashflow, "Free Cash Flow"),
            }
        
        return fundamentals
    
    def _safe_get(self, series: Any, key: str, default: Any = None) -> Optional[float]:
        """Safely get value from pandas Series, handling NaN values."""
        try:
            if key in series and series[key] is not None:
                value = series[key]
                if hasattr(value, 'item'):
                    float_val = float(value.item())
                else:
                    float_val = float(value)
                
                if math.isnan(float_val) or math.isinf(float_val):
                    return default
                return float_val
            return default
        except (KeyError, TypeError, ValueError):
            return default
    
    def fetch_market_index(self, symbol: str = "^GSPC", period: str = "1y") -> Dict[str, Any]:
        """
        Fetch market index data (S&P 500 by default) for Beta/Alpha calculations.
        """
        try:
            index = yf.Ticker(symbol)
            hist = index.history(period=period)
            
            price_history = []
            for idx, row in hist.iterrows():
                try:
                    if hasattr(idx, 'strftime'):
                        date_str = idx.strftime("%Y-%m-%d")
                    elif hasattr(idx, 'isoformat'):
                        date_str = str(idx)[:10]
                    else:
                        date_str = str(idx)[:10]
                except Exception:
                    date_str = str(idx)[:10]
                
                price_history.append({
                    "date": date_str,
                    "close": float(row["Close"]) if row["Close"] is not None else None,
                    "volume": int(row["Volume"]) if row["Volume"] is not None else None
                })
            
            return {
                "success": True,
                "symbol": symbol,
                "name": "S&P 500" if symbol == "^GSPC" else symbol,
                "price_history": price_history
            }
        except Exception as e:
            logger.error(f"Error fetching market index {symbol}: {str(e)}")
            return {
                "success": False,
                "symbol": symbol,
                "error": str(e)
            }
    
    def fetch_news(self, ticker: str, max_items: int = 10) -> List[Dict[str, Any]]:
        """Fetch recent news for a ticker."""
        try:
            stock = yf.Ticker(ticker)
            news = stock.news[:max_items] if hasattr(stock, 'news') else []
            
            formatted_news = []
            for item in news:
                formatted_news.append({
                    "title": item.get("title", ""),
                    "publisher": item.get("publisher", ""),
                    "link": item.get("link", ""),
                    "publish_time": item.get("providerPublishTime", ""),
                    "type": "yahoo_finance"
                })
            
            return formatted_news
        except Exception as e:
            logger.error(f"Error fetching news for {ticker}: {str(e)}")
            return []
