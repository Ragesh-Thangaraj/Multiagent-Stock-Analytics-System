"""
Data Fetching Tools for ADK Agents

These tools fetch stock data from Yahoo Finance and MarketAux APIs.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import pandas as pd
import yfinance as yf
import requests

from pathlib import Path

# Load .env from project root
env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(env_path)

def get_env(key: str, default=None):
    return os.environ.get(key, default)

logger = logging.getLogger(__name__)


def fetch_yahoo_finance_data(ticker: str, period_days: int = 252) -> Dict[str, Any]:
    """
    Fetches comprehensive stock data from Yahoo Finance including price history,
    fundamentals, and company information.

    Args:
        ticker (str): The stock ticker symbol (e.g., "AAPL", "MSFT", "GOOGL").
        period_days (int): Number of trading days of price history to fetch. Default is 252 (1 year).

    Returns:
        dict: A dictionary containing:
            - meta: Company metadata (name, sector, industry, etc.)
            - price_history: List of daily prices with date, open, high, low, close, volume
            - fundamentals: Income statement, balance sheet, and cash flow data
            - info: Precomputed ratios and metrics from Yahoo Finance
            - status: "success" or "error"
            - error_message: Error details if status is "error"
    """
    try:
        ticker = ticker.upper().strip()
        
        if period_days is None:
            period_days = 252
        try:
            period_days = int(period_days)
        except (TypeError, ValueError):
            period_days = 252
        
        stock = yf.Ticker(ticker)
        
        info = stock.info
        if not info or info.get('regularMarketPrice') is None:
            return {
                "status": "error",
                "error_message": f"Could not find valid data for ticker: {ticker}",
                "ticker": ticker
            }
        
        company_name = info.get('longName') or info.get('shortName') or ticker
        sector = info.get('sector', 'Unknown')
        industry = info.get('industry', 'Unknown')
        
        period_map = {
            21: "1mo",
            42: "2mo",  
            63: "3mo",
            126: "6mo",
            252: "1y",
            504: "2y",
            756: "3y",
            1260: "5y",
        }
        
        closest_period = "1y"
        for days, period_str in sorted(period_map.items()):
            if period_days <= days:
                closest_period = period_str
                break
        else:
            closest_period = "5y"
        
        hist = stock.history(period=closest_period)
        
        price_history = []
        if not hist.empty:
            hist = hist.tail(period_days)
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
                
                def safe_float(val):
                    try:
                        if val is None or (hasattr(pd, 'isna') and pd.isna(val)):
                            return None
                        return float(val)
                    except (TypeError, ValueError):
                        return None
                
                def safe_int(val):
                    try:
                        if val is None or (hasattr(pd, 'isna') and pd.isna(val)):
                            return None
                        return int(val)
                    except (TypeError, ValueError):
                        return None
                
                price_history.append({
                    "date": date_str,
                    "open": safe_float(row['Open']),
                    "high": safe_float(row['High']),
                    "low": safe_float(row['Low']),
                    "close": safe_float(row['Close']),
                    "volume": safe_int(row['Volume']),
                })
        
        income_stmt = stock.income_stmt
        balance_sheet = stock.balance_sheet
        cashflow = stock.cashflow
        
        def df_to_dict(df):
            if df is None or df.empty:
                return {}
            result = {}
            for col in df.columns:
                col_key = col.strftime("%Y-%m-%d") if hasattr(col, 'strftime') else str(col)
                result[col_key] = {}
                for idx in df.index:
                    val = df.loc[idx, col]
                    if pd.notna(val):
                        result[col_key][str(idx)] = float(val) if isinstance(val, (int, float)) else val
            return result
        
        fundamentals = {
            "income_statement": df_to_dict(income_stmt),
            "balance_sheet": df_to_dict(balance_sheet),
            "cashflow": df_to_dict(cashflow),
        }
        
        precomputed_ratios = {
            "trailing_pe": info.get('trailingPE'),
            "forward_pe": info.get('forwardPE'),
            "price_to_book": info.get('priceToBook'),
            "price_to_sales": info.get('priceToSalesTrailing12Months'),
            "enterprise_to_ebitda": info.get('enterpriseToEbitda'),
            "peg_ratio": info.get('pegRatio'),
            "enterprise_value": info.get('enterpriseValue'),
            "market_cap": info.get('marketCap'),
            "book_value": info.get('bookValue'),
            "earnings_per_share": info.get('trailingEps'),
            "forward_eps": info.get('forwardEps'),
            "dividend_yield": info.get('dividendYield'),
            "dividend_rate": info.get('dividendRate'),
            "beta": info.get('beta'),
            "return_on_equity": info.get('returnOnEquity'),
            "return_on_assets": info.get('returnOnAssets'),
            "profit_margins": info.get('profitMargins'),
            "operating_margins": info.get('operatingMargins'),
            "gross_margins": info.get('grossMargins'),
            "current_ratio": info.get('currentRatio'),
            "quick_ratio": info.get('quickRatio'),
            "debt_to_equity": info.get('debtToEquity'),
            "total_debt": info.get('totalDebt'),
            "total_cash": info.get('totalCash'),
            "free_cash_flow": info.get('freeCashflow'),
            "operating_cash_flow": info.get('operatingCashflow'),
            "revenue": info.get('totalRevenue'),
            "revenue_growth": info.get('revenueGrowth'),
            "earnings_growth": info.get('earningsGrowth'),
            "current_price": info.get('currentPrice') or info.get('regularMarketPrice'),
            "previous_close": info.get('previousClose'),
            "fifty_two_week_high": info.get('fiftyTwoWeekHigh'),
            "fifty_two_week_low": info.get('fiftyTwoWeekLow'),
            "shares_outstanding": info.get('sharesOutstanding'),
            "total_assets": info.get('totalAssets'),
            "total_liabilities": info.get('totalDebt'),
        }
        
        return {
            "status": "success",
            "ticker": ticker,
            "meta": {
                "ticker": ticker,
                "company_name": company_name,
                "sector": sector,
                "industry": industry,
                "exchange": info.get('exchange', 'N/A'),
                "currency": info.get('currency', 'USD'),
                "market_cap": info.get('marketCap'),
                "fetch_timestamp": datetime.now().isoformat(),
            },
            "price_history": price_history,
            "fundamentals": fundamentals,
            "info": precomputed_ratios,
        }
        
    except Exception as e:
        logger.error(f"Error fetching Yahoo Finance data for {ticker}: {str(e)}")
        return {
            "status": "error",
            "error_message": str(e),
            "ticker": ticker
        }


def fetch_marketaux_news(ticker: str, limit: int = 10) -> Dict[str, Any]:
    """
    Fetches recent news articles for a stock from MarketAux API.

    Args:
        ticker (str): The stock ticker symbol (e.g., "AAPL", "MSFT").
        limit (int): Maximum number of news articles to fetch. Default is 10.

    Returns:
        dict: A dictionary containing:
            - status: "success" or "error"
            - articles: List of news articles with title, description, source, url, published_at
            - sentiment: Overall sentiment analysis if available
            - error_message: Error details if status is "error"
    """
    try:
        api_key = get_env('MARKETAUX_API_KEY')
        if not api_key:
            return {
                "status": "error",
                "error_message": "MARKETAUX_API_KEY not configured",
                "ticker": ticker,
                "articles": []
            }
        
        ticker = ticker.upper().strip()
        
        url = "https://api.marketaux.com/v1/news/all"
        params = {
            "api_token": api_key,
            "symbols": ticker,
            "filter_entities": "true",
            "language": "en",
            "limit": limit,
        }
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        articles = []
        for item in data.get('data', []):
            title = item.get('title', '').strip()
            description = item.get('description', '').strip()
            
            if not title or title.lower() == 'not found':
                continue
            
            sentiment_value = None
            entities = item.get('entities', [])
            for entity in entities:
                if entity.get('symbol', '').upper() == ticker:
                    sentiment_value = entity.get('sentiment_score')
                    break
            
            if sentiment_value is None:
                sentiment_value = item.get('sentiment_score')
                
            articles.append({
                "title": title,
                "description": description,
                "source": item.get('source', 'Unknown'),
                "url": item.get('url', ''),
                "published_at": item.get('published_at', ''),
                "sentiment": sentiment_value,
                "type": "marketaux",
            })
        
        return {
            "status": "success",
            "ticker": ticker,
            "articles": articles,
            "article_count": len(articles),
        }
        
    except Exception as e:
        logger.error(f"Error fetching MarketAux news for {ticker}: {str(e)}")
        return {
            "status": "error",
            "error_message": str(e),
            "ticker": ticker,
            "articles": []
        }


def get_stock_info(ticker: str) -> Dict[str, Any]:
    """
    Gets basic stock information including current price, market cap, and sector.

    Args:
        ticker (str): The stock ticker symbol (e.g., "AAPL", "MSFT").

    Returns:
        dict: A dictionary containing:
            - status: "success" or "error"
            - ticker: The stock ticker
            - company_name: Full company name
            - current_price: Current stock price
            - market_cap: Market capitalization
            - sector: Company sector
            - industry: Company industry
            - error_message: Error details if status is "error"
    """
    try:
        ticker = ticker.upper().strip()
        stock = yf.Ticker(ticker)
        info = stock.info
        
        if not info or info.get('regularMarketPrice') is None:
            return {
                "status": "error",
                "error_message": f"Could not find valid data for ticker: {ticker}",
                "ticker": ticker
            }
        
        return {
            "status": "success",
            "ticker": ticker,
            "company_name": info.get('longName') or info.get('shortName') or ticker,
            "current_price": info.get('currentPrice') or info.get('regularMarketPrice'),
            "market_cap": info.get('marketCap'),
            "sector": info.get('sector', 'Unknown'),
            "industry": info.get('industry', 'Unknown'),
            "currency": info.get('currency', 'USD'),
        }
        
    except Exception as e:
        logger.error(f"Error getting stock info for {ticker}: {str(e)}")
        return {
            "status": "error",
            "error_message": str(e),
            "ticker": ticker
        }
