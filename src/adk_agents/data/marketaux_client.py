"""
MarketAux API Client

Fetches financial news and market data from MarketAux API.
Provides news articles, sentiment analysis, and market events.
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging
import os

from pathlib import Path

# Load .env from project root
env_path = Path(__file__).resolve().parents[2] / ".env"

def get_env(key: str, default=None):
    return os.environ.get(key, default)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MarketAuxClient:
    """Client for fetching data from MarketAux API."""
    
    BASE_URL = "https://api.marketaux.com/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or get_env("MARKETAUX_API_KEY")
        self.version = "v1"
        
        if not self.api_key:
            logger.warning("MarketAux API key not found. Set MARKETAUX_API_KEY environment variable.")
    
    def fetch_news(
        self,
        ticker: str,
        limit: int = 10,
        language: str = "en"
    ) -> List[Dict[str, Any]]:
        """
        Fetch news articles for a specific ticker.
        
        Args:
            ticker: Stock symbol (e.g., "AAPL")
            limit: Maximum number of articles (default 10)
            language: News language (default "en")
            
        Returns:
            List of news articles with metadata
        """
        if not self.api_key:
            return self._mock_news(ticker, limit)
        
        try:
            params = {
                "api_token": self.api_key,
                "symbols": ticker.upper(),
                "limit": limit,
                "language": language,
                "filter_entities": "true"
            }
            
            response = requests.get(f"{self.BASE_URL}/news/all", params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            news_articles = []
            
            for article in data.get("data", []):
                news_articles.append({
                    "title": article.get("title", ""),
                    "description": article.get("description", ""),
                    "url": article.get("url", ""),
                    "published_at": article.get("published_at", ""),
                    "source": article.get("source", ""),
                    "sentiment": article.get("entities", [{}])[0].get("sentiment_score") if article.get("entities") else None,
                    "relevance": article.get("entities", [{}])[0].get("relevance_score") if article.get("entities") else None,
                    "type": "marketaux"
                })
            
            logger.info(f"Fetched {len(news_articles)} news articles for {ticker}")
            return news_articles
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching MarketAux news for {ticker}: {str(e)}")
            return self._mock_news(ticker, limit)
        except Exception as e:
            logger.error(f"Unexpected error in MarketAux client: {str(e)}")
            return self._mock_news(ticker, limit)
    
    def _mock_news(self, ticker: str, limit: int) -> List[Dict[str, Any]]:
        """Return mock news data when API is unavailable."""
        logger.info(f"Using mock news data for {ticker}")
        
        mock_articles = [
            {
                "title": f"{ticker} Stock Analysis - Market Update",
                "description": f"Latest market analysis and performance review for {ticker}.",
                "url": f"https://example.com/news/{ticker.lower()}-analysis",
                "published_at": datetime.now().isoformat(),
                "source": "Mock Financial News",
                "sentiment": 0.5,
                "relevance": 0.8,
                "type": "mock"
            },
            {
                "title": f"{ticker} Quarterly Earnings Report",
                "description": f"Detailed quarterly earnings analysis for {ticker} stock.",
                "url": f"https://example.com/news/{ticker.lower()}-earnings",
                "published_at": (datetime.now() - timedelta(days=1)).isoformat(),
                "source": "Mock Business Wire",
                "sentiment": 0.7,
                "relevance": 0.9,
                "type": "mock"
            }
        ]
        
        return mock_articles[:limit]
    
    def fetch_market_sentiment(self, ticker: str) -> Dict[str, Any]:
        """
        Fetch aggregated market sentiment for a ticker.
        
        Returns:
            Dictionary with sentiment metrics
        """
        news = self.fetch_news(ticker, limit=50)
        
        if not news:
            return {
                "average_sentiment": None,
                "sentiment_count": 0,
                "null_reason": "no_news_available"
            }
        
        sentiments = [n.get("sentiment", 0) for n in news if n.get("sentiment") is not None]
        
        if not sentiments:
            return {
                "average_sentiment": None,
                "sentiment_count": 0,
                "null_reason": "no_sentiment_scores"
            }
        
        return {
            "average_sentiment": round(sum(sentiments) / len(sentiments), 4),
            "sentiment_count": len(sentiments),
            "positive_count": len([s for s in sentiments if s > 0.5]),
            "neutral_count": len([s for s in sentiments if 0.3 <= s <= 0.5]),
            "negative_count": len([s for s in sentiments if s < 0.3]),
            "null_reason": None
        }
