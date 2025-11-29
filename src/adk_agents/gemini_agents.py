"""
Gemini-Powered AI Agents for Stock Analytics

This module implements specialized AI agents using Google's Gemini 2.0 Flash model.
Each agent has a specific purpose and excellent prompts for their domain.

Agents:
1. ConversationalAgent - Long-term memory chat with stock context
2. SummarizationAgent - Generates insights for metrics sections
3. NewsAnalysisAgent - Analyzes news sentiment and market impact

Uses: google-genai SDK with Gemini 2.0 Flash model
"""

import os
import json
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

from google import genai
from google.genai import types

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from dotenv import load_dotenv
from pathlib import Path

# Load .env from project root
env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(env_path)

def get_env(key: str, default=None):
    return os.environ.get(key, default)

GEMINI_API_KEY = get_env("GEMINI_API_KEY")

if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)
else:
    client = None
    logger.warning("GEMINI_API_KEY not found. AI agents will use fallback responses.")


class ConversationalAgent:
    """
    Long-term conversational agent with memory for stock analytics discussions.
    Maintains conversation history and understands context from previous messages.
    Supports external history sync for persistence across Streamlit reruns.
    """
    
    SYSTEM_PROMPT = """You are an expert financial analyst assistant specializing in stock analytics and investment analysis. You have deep expertise in:

- Financial statement analysis (income statement, balance sheet, cash flow)
- Valuation metrics (P/E, P/B, EV/EBITDA, DCF analysis)
- Risk assessment (market risk, credit risk, liquidity risk)
- Technical analysis and market trends
- Investment recommendations based on fundamental analysis

CONVERSATION RULES:
1. Remember and reference previous messages in our conversation - this is critical
2. Build upon earlier discussions - don't repeat information unnecessarily
3. When the user asks follow-up questions, use context from ALL previous answers
4. Be conversational and natural, like talking to a knowledgeable friend
5. If asked about something you mentioned before, elaborate or clarify
6. Use the stock data provided to give specific, accurate answers
7. Always cite specific numbers and metrics when available
8. Provide actionable insights, not just data recitation
9. Reference what the user asked earlier and build on your previous responses
10. Maintain continuity - if you gave a recommendation, remember it for follow-up questions

RESPONSE STYLE:
- Be concise but comprehensive
- Use bullet points for multiple data points
- Explain technical terms in simple language
- Provide context for why metrics matter
- Give balanced perspectives on investment decisions
- Include relevant disclaimers for investment advice
- When answering follow-ups, briefly acknowledge what was discussed before

You are currently analyzing stock data that has been provided. Use this data to answer questions accurately and provide meaningful financial insights. Remember everything we've discussed in this conversation."""

    def __init__(self):
        self.conversation_history: List[Dict[str, str]] = []
        self.stock_context: Optional[Dict[str, Any]] = None
        self.ticker: str = ""
        self.company_name: str = ""
        self._context_initialized: bool = False
    
    def set_stock_context(self, stock_data: Dict[str, Any], preserve_history: bool = False):
        """Set the current stock data context for the conversation."""
        self.stock_context = stock_data
        meta = stock_data.get("meta", {})
        self.ticker = meta.get("ticker", "Unknown")
        self.company_name = meta.get("company_name", self.ticker)
        
        if not preserve_history:
            self.conversation_history = []
            self._context_initialized = False
        
        if not self._context_initialized:
            context_message = self._build_context_message()
            self.conversation_history.insert(0, {
                "role": "assistant", 
                "content": f"I've loaded the financial data for {self.company_name} ({self.ticker}). I can see the complete fundamental analysis including profitability metrics, liquidity ratios, valuation multiples, risk assessment, and growth metrics. What would you like to know about this stock?"
            })
            self.conversation_history.insert(0, {
                "role": "user",
                "content": f"I'm analyzing {self.company_name} ({self.ticker}). Here's the current data:\n\n{context_message}"
            })
            self._context_initialized = True
    
    def sync_history(self, external_history: List[Dict[str, str]]):
        """Sync conversation history from external source (e.g., session state)."""
        if external_history:
            base_count = 2 if self._context_initialized else 0
            self.conversation_history = self.conversation_history[:base_count] + external_history
    
    def get_user_history(self) -> List[Dict[str, str]]:
        """Get only user-visible conversation history (excludes initial context)."""
        if len(self.conversation_history) > 2:
            return self.conversation_history[2:]
        return []
    
    def _build_context_message(self) -> str:
        """Build a context message from stock data."""
        if not self.stock_context:
            return "No stock data loaded."
        
        calculated = self.stock_context.get("calculated", {})
        meta = self.stock_context.get("meta", {})
        
        context_parts = [
            f"Company: {meta.get('company_name', 'Unknown')} ({meta.get('ticker', 'Unknown')})",
            f"Exchange: {meta.get('exchange', 'Unknown')}",
            f"Currency: {meta.get('currency', 'USD')}",
            ""
        ]
        
        if "profitability" in calculated:
            prof = calculated["profitability"]
            context_parts.append("PROFITABILITY METRICS:")
            for key, val in prof.items():
                if isinstance(val, dict) and val.get("value") is not None:
                    context_parts.append(f"  - {key}: {val['value']:.2%}" if abs(val['value']) < 10 else f"  - {key}: {val['value']:.2f}")
        
        if "valuation" in calculated:
            val = calculated["valuation"]
            context_parts.append("\nVALUATION METRICS:")
            for key, v in val.items():
                if isinstance(v, dict) and v.get("value") is not None:
                    context_parts.append(f"  - {key}: {v['value']:.2f}")

        if "risk_market" in calculated:
            risk = calculated["risk_market"]
            context_parts.append("\nMARKET RISK:")
            for key in ["beta", "volatility", "sharpe_ratio", "var_95"]:
                if key in risk and isinstance(risk[key], dict) and risk[key].get("value") is not None:
                    context_parts.append(f"  - {key}: {risk[key]['value']:.4f}")
        
        if "risk_financial" in calculated:
            risk_f = calculated["risk_financial"]
            context_parts.append("\nFINANCIAL RISK:")
            for key in ["credit_risk", "liquidity_risk", "operational_risk", "composite_financial_health"]:
                if key in risk_f and isinstance(risk_f[key], dict):
                    score = risk_f[key].get("score")
                    if score is not None:
                        context_parts.append(f"  - {key}: {score}/100")
        
        return "\n".join(context_parts)
    
    def chat(self, user_message: str, max_retries: int = 3) -> str:
        """
        Send a message and get a response, maintaining full conversation history.
        Includes retry logic for rate limit errors.
        """
        if not client:
            return self._fallback_response(user_message)
        
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        for attempt in range(max_retries):
            try:
                contents = []
                
                for msg in self.conversation_history:
                    contents.append(types.Content(
                        role="user" if msg["role"] == "user" else "model",
                        parts=[types.Part(text=msg["content"])]
                    ))
                
                enhanced_prompt = self.SYSTEM_PROMPT
                if len(self.conversation_history) > 6:
                    enhanced_prompt += f"\n\nIMPORTANT: This is message #{len(self.conversation_history) - 2} in our conversation. Review the full conversation history above carefully before responding. Reference specific things we discussed earlier when relevant."
                
                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=enhanced_prompt,
                        temperature=0.7,
                        max_output_tokens=1500,
                    )
                )
                
                assistant_message = response.text if response.text else "I apologize, I couldn't generate a response. Please try again."
                
                self.conversation_history.append({
                    "role": "assistant",
                    "content": assistant_message
                })
                
                return assistant_message
                
            except Exception as e:
                error_msg = str(e).lower()
                logger.error(f"Gemini API error (attempt {attempt + 1}/{max_retries}): {str(e)}")
                
                is_rate_limit = any(x in error_msg for x in ["429", "quota", "rate", "limit", "resource exhausted", "overloaded"])
                
                if is_rate_limit and attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    logger.info(f"Rate limit hit, retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                
                if is_rate_limit:
                    self.conversation_history.pop()
                    return "I'm experiencing high demand right now. Please wait a few seconds and try again. Your conversation history is preserved."
                
                self.conversation_history.pop()
                return self._fallback_response(user_message)
        
        self.conversation_history.pop()
        return self._fallback_response(user_message)
    
    def _fallback_response(self, user_message: str) -> str:
        """Provide fallback response when API is unavailable."""
        query_lower = user_message.lower()
        
        if not self.stock_context:
            return "I don't have any stock data loaded. Please run an analysis first by clicking 'Fetch & Analyze'."
        
        calculated = self.stock_context.get("calculated", {})
        
        if "p/e" in query_lower or "pe ratio" in query_lower:
            pe = calculated.get("valuation", {}).get("pe_ratio", {})
            if isinstance(pe, dict) and pe.get("value"):
                return f"The P/E ratio for {self.company_name} is {pe['value']:.2f}. This measures how much investors are willing to pay per dollar of earnings. A higher P/E might indicate growth expectations, while a lower P/E could suggest undervaluation or concerns about future growth."
        
        if "profit" in query_lower or "margin" in query_lower:
            prof = calculated.get("profitability", {})
            parts = []
            for key in ["gross_margin", "operating_margin", "net_margin"]:
                val = prof.get(key, {})
                if isinstance(val, dict) and val.get("value") is not None:
                    parts.append(f"{key.replace('_', ' ').title()}: {val['value']:.2%}")
            if parts:
                return f"Here are the profitability metrics for {self.company_name}:\n" + "\n".join(f"- {p}" for p in parts)
        
        if "risk" in query_lower:
            risk_m = calculated.get("risk_market", {})
            risk_f = calculated.get("risk_financial", {})
            parts = []
            if risk_m.get("beta", {}).get("value"):
                parts.append(f"Beta: {risk_m['beta']['value']:.2f}")
            if risk_m.get("volatility", {}).get("value"):
                parts.append(f"Volatility: {risk_m['volatility']['value']:.2%}")
            if risk_f.get("composite_financial_health", {}).get("score"):
                parts.append(f"Financial Health: {risk_f['composite_financial_health']['score']}/100")
            if parts:
                return f"Risk assessment for {self.company_name}:\n" + "\n".join(f"- {p}" for p in parts)
        
        return f"I can help you analyze {self.company_name}. Try asking about:\n- P/E ratio and valuation\n- Profitability margins\n- Risk assessment\n- DCF valuation\n- Investment recommendation\n\nWhat would you like to know?"
    
    def get_history(self) -> List[Dict[str, str]]:
        """Get the conversation history."""
        return self.conversation_history[2:] if len(self.conversation_history) > 2 else []
    
    def clear_history(self):
        """Clear conversation history but keep stock context."""
        if self.stock_context:
            self.set_stock_context(self.stock_context)
        else:
            self.conversation_history = []


class SummarizationAgent:
    """
    Agent for generating AI-powered summaries of financial metrics sections.
    Provides plain-language explanations and investment insights.
    """
    
    PROFITABILITY_PROMPT = """You are a financial analyst expert. Analyze the following profitability metrics for {company_name} ({ticker}) and provide:

1. A 2-3 sentence summary of the company's profitability health
2. Key strengths or concerns based on the metrics
3. How these metrics compare to typical industry standards

PROFITABILITY METRICS:
{metrics}

Provide a clear, concise analysis in plain language that a retail investor can understand. Focus on what these numbers mean for the company's ability to generate profits."""

    VALUATION_PROMPT = """You are a financial analyst expert. Analyze the following valuation metrics and DCF analysis for {company_name} ({ticker}):

VALUATION METRICS:
{metrics}

DCF ANALYSIS:
{dcf}

Provide:
1. A 2-3 sentence summary of whether the stock appears undervalued, fairly valued, or overvalued
2. Key valuation insights based on P/E, P/B, and other multiples
3. An interpretation of the DCF intrinsic value vs market price

Be balanced and note any limitations in the valuation approach."""

    RISK_PROMPT = """You are a financial risk analyst. Analyze the following risk metrics for {company_name} ({ticker}):

MARKET RISK:
{market_risk}

FINANCIAL RISK:
{financial_risk}

Provide:
1. A 2-3 sentence overall risk assessment
2. Key risk factors investors should be aware of
3. The company's risk profile relative to typical market investments

Explain technical metrics like Beta and VaR in simple terms."""

    LIQUIDITY_PROMPT = """You are a financial analyst. Analyze these liquidity and leverage metrics for {company_name} ({ticker}):

LIQUIDITY METRICS:
{liquidity}

LEVERAGE METRICS:
{leverage}

Provide:
1. Assessment of the company's ability to meet short-term obligations
2. Analysis of the debt structure and financial leverage
3. Any concerns or strengths in the company's financial position"""

    def __init__(self):
        pass
    
    def summarize_profitability(self, stock_data: Dict[str, Any]) -> str:
        """Generate a summary for profitability metrics."""
        if not client:
            return self._fallback_profitability(stock_data)
        
        try:
            calculated = stock_data.get("calculated", {})
            meta = stock_data.get("meta", {})
            prof = calculated.get("profitability", {})
            
            metrics_str = self._format_metrics(prof)
            
            prompt = self.PROFITABILITY_PROMPT.format(
                company_name=meta.get("company_name", "Unknown"),
                ticker=meta.get("ticker", "Unknown"),
                metrics=metrics_str
            )
            
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.5,
                    max_output_tokens=512,
                )
            )
            
            return response.text if response.text else self._fallback_profitability(stock_data)
            
        except Exception as e:
            logger.error(f"Summarization error: {str(e)}")
            return self._fallback_profitability(stock_data)
    
    def summarize_valuation(self, stock_data: Dict[str, Any]) -> str:
        """Generate a summary for valuation metrics."""
        if not client:
            return self._fallback_valuation(stock_data)
        
        try:
            calculated = stock_data.get("calculated", {})
            meta = stock_data.get("meta", {})
            valuation = calculated.get("valuation", {})
            dcf = calculated.get("dcf", {})
            
            prompt = self.VALUATION_PROMPT.format(
                company_name=meta.get("company_name", "Unknown"),
                ticker=meta.get("ticker", "Unknown"),
                metrics=self._format_metrics(valuation),
                dcf=self._format_metrics(dcf)
            )
            
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.5,
                    max_output_tokens=512,
                )
            )
            
            return response.text if response.text else self._fallback_valuation(stock_data)
            
        except Exception as e:
            logger.error(f"Valuation summarization error: {str(e)}")
            return self._fallback_valuation(stock_data)
    
    def summarize_risk(self, stock_data: Dict[str, Any]) -> str:
        """Generate a summary for risk metrics."""
        if not client:
            return self._fallback_risk(stock_data)
        
        try:
            calculated = stock_data.get("calculated", {})
            meta = stock_data.get("meta", {})
            
            prompt = self.RISK_PROMPT.format(
                company_name=meta.get("company_name", "Unknown"),
                ticker=meta.get("ticker", "Unknown"),
                market_risk=self._format_metrics(calculated.get("risk_market", {})),
                financial_risk=self._format_metrics(calculated.get("risk_financial", {}))
            )
            
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.5,
                    max_output_tokens=512,
                )
            )
            
            return response.text if response.text else self._fallback_risk(stock_data)
            
        except Exception as e:
            logger.error(f"Risk summarization error: {str(e)}")
            return self._fallback_risk(stock_data)
    
    def summarize_liquidity_leverage(self, stock_data: Dict[str, Any]) -> str:
        """Generate a summary for liquidity and leverage metrics."""
        if not client:
            return self._fallback_liquidity(stock_data)
        
        try:
            calculated = stock_data.get("calculated", {})
            meta = stock_data.get("meta", {})
            
            prompt = self.LIQUIDITY_PROMPT.format(
                company_name=meta.get("company_name", "Unknown"),
                ticker=meta.get("ticker", "Unknown"),
                liquidity=self._format_metrics(calculated.get("liquidity", {})),
                leverage=self._format_metrics(calculated.get("leverage", {}))
            )
            
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.5,
                    max_output_tokens=512,
                )
            )
            
            return response.text if response.text else self._fallback_liquidity(stock_data)
            
        except Exception as e:
            logger.error(f"Liquidity summarization error: {str(e)}")
            return self._fallback_liquidity(stock_data)
    
    def _format_metrics(self, metrics: Dict) -> str:
        """Format metrics dictionary for prompt."""
        lines = []
        for key, val in metrics.items():
            if isinstance(val, dict):
                value = val.get("value")
                if value is not None:
                    if isinstance(value, float) and abs(value) < 10:
                        lines.append(f"- {key}: {value:.4f}")
                    else:
                        lines.append(f"- {key}: {value}")
                else:
                    lines.append(f"- {key}: N/A ({val.get('null_reason', 'unknown')})")
            elif val is not None:
                lines.append(f"- {key}: {val}")
        return "\n".join(lines) if lines else "No metrics available"
    
    def _fallback_profitability(self, stock_data: Dict[str, Any]) -> str:
        """Fallback profitability summary."""
        calculated = stock_data.get("calculated", {})
        meta = stock_data.get("meta", {})
        prof = calculated.get("profitability", {})
        
        company = meta.get("company_name", "This company")
        
        gross = prof.get("gross_margin", {}).get("value")
        net = prof.get("net_margin", {}).get("value")
        roe = prof.get("roe", {}).get("value")
        
        parts = [f"**Profitability Analysis for {company}**\n"]
        
        if gross:
            parts.append(f"The gross margin of {gross:.1%} indicates the profit retained after direct costs.")
        if net:
            parts.append(f"Net margin of {net:.1%} shows the final profit after all expenses.")
        if roe:
            parts.append(f"ROE of {roe:.1%} measures return generated on shareholder equity.")
        
        return " ".join(parts) if len(parts) > 1 else "Profitability metrics are being calculated..."
    
    def _fallback_valuation(self, stock_data: Dict[str, Any]) -> str:
        """Fallback valuation summary."""
        calculated = stock_data.get("calculated", {})
        meta = stock_data.get("meta", {})
        valuation = calculated.get("valuation", {})
        
        company = meta.get("company_name", "This company")
        pe = valuation.get("pe_ratio", {}).get("value")
        pb = valuation.get("price_to_book", {}).get("value")
        
        parts = [f"**Valuation Analysis for {company}**\n"]
        
        if pe:
            parts.append(f"P/E ratio of {pe:.2f}x.")
        if pb:
            parts.append(f"P/B ratio of {pb:.2f}x.")
        
        return " ".join(parts) if len(parts) > 1 else "Valuation metrics are being calculated..."
    
    def _fallback_risk(self, stock_data: Dict[str, Any]) -> str:
        """Fallback risk summary."""
        calculated = stock_data.get("calculated", {})
        meta = stock_data.get("meta", {})
        risk = calculated.get("risk_market", {})
        
        company = meta.get("company_name", "This company")
        beta = risk.get("beta", {}).get("value")
        vol = risk.get("volatility", {}).get("value")
        
        parts = [f"**Risk Analysis for {company}**\n"]
        
        if beta:
            parts.append(f"Beta of {beta:.2f} indicates {'higher' if beta > 1 else 'lower'} volatility than the market.")
        if vol:
            parts.append(f"Annualized volatility of {vol:.1%}.")
        
        return " ".join(parts) if len(parts) > 1 else "Risk metrics are being calculated..."
    
    def _fallback_liquidity(self, stock_data: Dict[str, Any]) -> str:
        """Fallback liquidity summary."""
        calculated = stock_data.get("calculated", {})
        meta = stock_data.get("meta", {})
        liquidity = calculated.get("liquidity", {})
        
        company = meta.get("company_name", "This company")
        current = liquidity.get("current_ratio", {}).get("value")
        quick = liquidity.get("quick_ratio", {}).get("value")
        
        parts = [f"**Liquidity Analysis for {company}**\n"]
        
        if current:
            parts.append(f"Current ratio of {current:.2f}.")
        if quick:
            parts.append(f"Quick ratio of {quick:.2f}.")
        
        return " ".join(parts) if len(parts) > 1 else "Liquidity metrics are being calculated..."


class NewsAnalysisAgent:
    """Agent for analyzing news sentiment and market impact."""
    
    def __init__(self):
        pass
    
    def analyze_news(self, news_articles: List[Dict[str, Any]], ticker: str) -> str:
        """Analyze news articles and provide sentiment summary."""
        if not news_articles:
            return "No recent news articles found for analysis."
        
        if not client:
            return self._fallback_news_analysis(news_articles, ticker)
        
        try:
            news_summary = []
            for article in news_articles[:10]:
                sentiment = article.get("sentiment", "N/A")
                title = article.get("title", "")
                source = article.get("source", article.get("publisher", "Unknown"))
                news_summary.append(f"- {title} (Source: {source}, Sentiment: {sentiment})")
            
            prompt = f"""Analyze the following recent news articles for {ticker} and provide:

1. Overall market sentiment (bullish, bearish, or neutral)
2. Key themes or events driving the news
3. Potential impact on stock price
4. Any notable concerns or positive developments

NEWS ARTICLES:
{chr(10).join(news_summary)}

Provide a concise 3-4 sentence analysis in plain language."""

            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.5,
                    max_output_tokens=512,
                )
            )
            
            return response.text if response.text else self._fallback_news_analysis(news_articles, ticker)
            
        except Exception as e:
            logger.error(f"News analysis error: {str(e)}")
            return self._fallback_news_analysis(news_articles, ticker)
    
    def _fallback_news_analysis(self, news_articles: List[Dict[str, Any]], ticker: str) -> str:
        """Fallback news analysis."""
        if not news_articles:
            return "No news articles available for analysis."
        
        sentiments = [a.get("sentiment", 0) for a in news_articles if a.get("sentiment") is not None]
        
        if sentiments:
            avg_sentiment = sum(sentiments) / len(sentiments)
            sentiment_label = "positive" if avg_sentiment > 0.5 else ("negative" if avg_sentiment < 0.3 else "neutral")
            return f"Based on {len(sentiments)} recent news articles, the overall market sentiment for {ticker} appears to be {sentiment_label} (average score: {avg_sentiment:.2f})."
        
        return f"Found {len(news_articles)} recent news articles for {ticker}. Sentiment data not available."


conversational_agent = ConversationalAgent()
summarization_agent = SummarizationAgent()
news_agent = NewsAnalysisAgent()
