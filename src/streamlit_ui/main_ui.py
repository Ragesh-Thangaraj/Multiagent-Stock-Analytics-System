"""
Stock Analytics Agent - Tabbed Interface with ChatGPT-Style Chat

Features:
- Multi-tab interface for organized analysis
- Google ADK three-layer agent architecture
- ChatGPT-style conversational AI with long-term memory using Gemini 2.0 Flash
- AI-powered summaries for each section
- Professional PDF/HTML reports
- 30+ financial metrics with provenance
"""

import streamlit as st
import json
from pathlib import Path
from datetime import datetime
import sys
import os
import logging

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.adk_agents.orchestrator import StockAnalyticsOrchestrator, get_orchestrator
from src.adk_agents.data.fetcher import DataFetcher
from src.adk_agents.gemini_agents import conversational_agent, summarization_agent, news_agent
from src.utils.sandbox_runner import SandboxRunner

logger = logging.getLogger(__name__)


@st.cache_data(ttl=300)
def load_report_data(data_path: str) -> dict:
    """Load and cache report data for faster subsequent report generation."""
    calculated_path = data_path.replace('.json', '_calculated.json')
    if Path(calculated_path).exists():
        with open(calculated_path, 'r') as f:
            return json.load(f)
    else:
        with open(data_path, 'r') as f:
            return json.load(f)


def build_pdf_report(data: dict, output_path: Path) -> bool:
    """Build PDF report from data - no UI dependencies for background generation."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib import colors
        from reportlab.lib.units import inch
    except ImportError:
        return False

    try:
        meta = data.get('meta', {})
        ticker = meta.get('ticker', 'UNKNOWN')
        company_name = meta.get('company_name', ticker)
        calculated = data.get('calculated', {})

        doc = SimpleDocTemplate(str(output_path), pagesize=letter,
                                leftMargin=0.75*inch, rightMargin=0.75*inch,
                                topMargin=0.75*inch, bottomMargin=0.75*inch)
        styles = getSampleStyleSheet()
        story = []

        title_style = ParagraphStyle('Title', parent=styles['Title'], fontSize=24, spaceAfter=30)
        subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'], fontSize=12, spaceAfter=20)
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ])

        story.append(Paragraph(f"{company_name} ({ticker})", title_style))
        story.append(Paragraph("Stock Analysis Report", styles['Heading2']))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", subtitle_style))
        story.append(Spacer(1, 0.5 * inch))

        prof = calculated.get('profitability', {})
        story.append(Paragraph("Profitability Metrics", styles['Heading2']))
        prof_data = [['Metric', 'Value'],
                     ['Gross Margin', format_metric_value(prof.get('gross_margin'))],
                     ['Operating Margin', format_metric_value(prof.get('operating_margin'))],
                     ['Net Margin', format_metric_value(prof.get('net_margin'))],
                     ['ROE', format_metric_value(prof.get('roe'))],
                     ['ROA', format_metric_value(prof.get('roa'))],
                     ['ROIC', format_metric_value(prof.get('roic'))]]
        table = Table(prof_data, colWidths=[2.5 * inch, 2 * inch])
        table.setStyle(table_style)
        story.append(table)
        story.append(Spacer(1, 0.3 * inch))

        val = calculated.get('valuation', {})
        story.append(Paragraph("Valuation Metrics", styles['Heading2']))
        val_data = [['Metric', 'Value'],
                    ['P/E Ratio', format_metric_value(val.get('pe_ratio'))],
                    ['P/B Ratio', format_metric_value(val.get('price_to_book'))],
                    ['P/S Ratio', format_metric_value(val.get('price_to_sales'))],
                    ['EV/EBITDA', format_metric_value(val.get('ev_to_ebitda'))],
                    ['Dividend Yield', format_metric_value(val.get('dividend_yield'))],
                    ['PEG Ratio', format_metric_value(val.get('peg_ratio'))],
                    ['Enterprise Value', format_metric_value(val.get('enterprise_value'))]]
        table = Table(val_data, colWidths=[2.5 * inch, 2 * inch])
        table.setStyle(table_style)
        story.append(table)
        story.append(Spacer(1, 0.3 * inch))

        risk = calculated.get('risk_market', {})
        story.append(Paragraph("Risk Metrics", styles['Heading2']))
        risk_data = [['Metric', 'Value'],
                     ['Volatility', format_metric_value(risk.get('volatility'))],
                     ['Beta', format_metric_value(risk.get('beta'))],
                     ['Sharpe Ratio', format_metric_value(risk.get('sharpe_ratio'))],
                     ['Max Drawdown', format_metric_value(risk.get('max_drawdown'))]]
        table = Table(risk_data, colWidths=[2.5 * inch, 2 * inch])
        table.setStyle(table_style)
        story.append(table)

        story.append(Spacer(1, 0.5 * inch))
        story.append(Paragraph("Disclaimer: This report is for informational purposes only.", styles['Normal']))

        doc.build(story)
        return True
    except Exception as e:
        logger.error(f"PDF generation error: {e}")
        return False


def build_html_report(data: dict, output_path: Path) -> bool:
    """Build HTML report from data - no UI dependencies for background generation."""
    try:
        meta = data.get('meta', {})
        ticker = meta.get('ticker', 'UNKNOWN')
        company_name = meta.get('company_name', ticker)
        calculated = data.get('calculated', {})

        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>{company_name} ({ticker}) - Stock Analysis Report</title>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
        .container {{ max-width: 1000px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #1a1a2e; border-bottom: 3px solid #4a90d9; padding-bottom: 10px; }}
        h2 {{ color: #16213e; margin-top: 30px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        th {{ background: #4a90d9; color: white; padding: 12px; text-align: left; }}
        td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
        tr:hover {{ background: #f5f5f5; }}
        .value {{ font-weight: bold; color: #1a1a2e; }}
        .footer {{ text-align: center; margin-top: 40px; color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{company_name} ({ticker})</h1>
        <p>Stock Analysis Report | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
        
        <h2>Profitability Metrics</h2>
        <table>
            <tr><th>Metric</th><th>Value</th><th>Formula</th></tr>
            {generate_metric_rows(calculated.get('profitability', {}))}
        </table>
        
        <h2>Valuation Metrics</h2>
        <table>
            <tr><th>Metric</th><th>Value</th><th>Formula</th></tr>
            {generate_metric_rows(calculated.get('valuation', {}))}
        </table>
        
        <h2>Liquidity Metrics</h2>
        <table>
            <tr><th>Metric</th><th>Value</th><th>Formula</th></tr>
            {generate_metric_rows(calculated.get('liquidity', {}))}
        </table>
        
        <h2>Leverage Metrics</h2>
        <table>
            <tr><th>Metric</th><th>Value</th><th>Formula</th></tr>
            {generate_metric_rows(calculated.get('leverage', {}))}
        </table>
        
        <h2>Growth Metrics</h2>
        <table>
            <tr><th>Metric</th><th>Value</th><th>Formula</th></tr>
            {generate_metric_rows(calculated.get('growth', {}))}
        </table>
        
        <h2>Risk Assessment</h2>
        <table>
            <tr><th>Risk Type</th><th>Level</th><th>Score</th></tr>
            {generate_risk_rows(calculated.get('risk_financial', {}))}
        </table>
        
        <div class="footer">
            <p>Generated by Stock Analytics Agent</p>
            <p>Disclaimer: This report is for informational purposes only and should not be considered financial advice.</p>
        </div>
    </div>
</body>
</html>"""

        with open(output_path, 'w') as f:
            f.write(html_content)
        return True
    except Exception as e:
        logger.error(f"HTML generation error: {e}")
        return False


def pre_generate_reports(data: dict, ticker: str, timestamp: str):
    """Pre-generate PDF and HTML reports during analysis for instant downloads."""
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    
    pdf_path = reports_dir / f"{ticker}_{timestamp}_report.pdf"
    html_path = reports_dir / f"{ticker}_{timestamp}_report.html"
    
    pdf_success = build_pdf_report(data, pdf_path)
    html_success = build_html_report(data, html_path)
    
    return {
        'pdf_path': str(pdf_path) if pdf_success else None,
        'html_path': str(html_path) if html_success else None,
        'pdf_content': pdf_path.read_bytes() if pdf_success else None,
        'html_content': html_path.read_text() if html_success else None,
    }


def main():
    """Main UI entry point with sidebar navigation for view mode selection."""
    
    st.title("📊 Stock Analytics Agent")
    st.markdown("---")

    if 'view_mode' not in st.session_state:
        st.session_state.view_mode = "Analysis"

    with st.sidebar:
        st.header("⚙️ Configuration")

        ticker_input = st.text_input(
            "Stock Ticker",
            value="AAPL",
            help="Enter stock symbol (e.g., aapl, GOOGL, msft)")
        ticker = ticker_input.strip().upper()

        period = st.selectbox("Historical Period",
                              ["1mo", "3mo", "6mo", "1y", "2y", "5y"],
                              index=3)

        st.markdown("---")
        if st.button("🔄 Fetch & Analyze",
                     type="primary",
                     use_container_width=True):
            if ticker:
                with st.spinner(f"Fetching data for {ticker}..."):
                    fetch_and_analyze(ticker, period)
            else:
                st.error("Please enter a valid ticker symbol")
        
        st.markdown("---")
        st.subheader("📌 View Mode")
        view_mode = st.radio(
            "Select view:",
            ["Analysis", "Chat"],
            index=0 if st.session_state.view_mode == "Analysis" else 1,
            key="view_mode_radio",
            horizontal=True
        )
        st.session_state.view_mode = view_mode

    if st.session_state.view_mode == "Analysis":
        show_analysis_tabs()
    else:
        show_chat_page()


def show_analysis_tabs():
    """Show the analysis tabs (Overview, Metrics, Valuation, Risk, Reports)."""
    tab_names = [
        "📝 Overview", "📈 Metrics", "💰 Valuation", "⚠️ Risk", "📄 Reports"
    ]

    tabs = st.tabs(tab_names)

    with tabs[0]:
        show_overview()

    with tabs[1]:
        show_metrics()

    with tabs[2]:
        show_valuation()

    with tabs[3]:
        show_risk()

    with tabs[4]:
        show_reports()


def show_chat_page():
    """Show the chat page with chat input (separate from tabs)."""
    st.header("💬 Chat with AI Analyst")

    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    if 'current_data_path' not in st.session_state:
        st.info("👈 Run analysis first to enable chat about your stock data")
        return

    data_path = st.session_state.get('current_data_path')
    calculated_path = data_path.replace('.json', '_calculated.json') if data_path else None

    stock_data = None
    if calculated_path and Path(calculated_path).exists():
        with open(calculated_path, 'r') as f:
            stock_data = json.load(f)

    if stock_data:
        if 'conversational_agent_initialized' not in st.session_state:
            conversational_agent.set_stock_context(stock_data, preserve_history=False)
            st.session_state['conversational_agent_initialized'] = True
            st.session_state.chat_history = []
        else:
            conversational_agent.set_stock_context(stock_data, preserve_history=True)
            conversational_agent.sync_history(st.session_state.chat_history)

    ticker = stock_data.get('meta', {}).get('ticker', 'Unknown') if stock_data else 'Unknown'
    company_name = stock_data.get('meta', {}).get('company_name', ticker) if stock_data else 'Unknown'

    st.markdown(f"**Analyzing: {company_name} ({ticker})**")

    msg_count = len(st.session_state.chat_history) // 2
    if msg_count > 0:
        st.markdown(f"*Conversation history: {msg_count} exchanges - I remember everything we've discussed!*")
    else:
        st.markdown("*Ask questions about the stock - I'll remember our entire conversation for in-depth analysis!*")

    st.markdown("---")

    chat_container = st.container()

    with chat_container:
        for msg in st.session_state.chat_history:
            if msg['role'] == 'user':
                with st.chat_message("user"):
                    st.write(msg['content'])
            else:
                with st.chat_message("assistant"):
                    st.write(msg['content'])

    if prompt := st.chat_input("Ask about the stock (e.g., What is the P/E ratio? Is this stock undervalued?)"):
        if stock_data:
            st.session_state.chat_history.append({'role': 'user', 'content': prompt})

            with st.chat_message("user"):
                st.write(prompt)

            conversational_agent.sync_history(st.session_state.chat_history[:-1])

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = conversational_agent.chat(prompt)
                st.write(response)

            st.session_state.chat_history.append({'role': 'assistant', 'content': response})

            st.rerun()

    st.markdown("---")

    with st.expander("📝 Example Questions"):
        st.markdown("""
        **Valuation:**
        - "What is the P/E ratio and is it high or low?"
        - "Is this stock undervalued or overvalued?"
        - "How does the PEG ratio look?"
        
        **Profitability:**
        - "Tell me about the company's profitability"
        - "What are the profit margins?"
        - "How efficient is the company?"
        
        **Risk:**
        - "What are the main risk factors?"
        - "How volatile is this stock?"
        - "What's the Altman Z-Score?"
        
        **Follow-up (memory test):**
        - "Can you explain that more?"
        - "Based on what you just said, what should I do?"
        - "You mentioned X earlier - can you elaborate?"
        - "Summarize everything we've discussed"
        """)

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("🗑️ Clear Chat History", use_container_width=True):
            st.session_state.chat_history = []
            conversational_agent.clear_history()
            st.rerun()
    with col2:
        st.caption(f"Long-term memory active ({len(st.session_state.chat_history)} messages)")


def fetch_and_analyze(ticker: str, period: str):
    """Fetch data and run all analysis using ADK orchestrator."""
    try:
        ticker = ticker.upper()

        period_days_map = {
            "1mo": 21,
            "3mo": 63,
            "6mo": 126,
            "1y": 252,
            "2y": 504,
            "5y": 1260,
        }
        period_days = period_days_map.get(period, 252)

        orchestrator = get_orchestrator()

        result = orchestrator.analyze_stock(ticker, period_days)

        if result.get('status') == 'error':
            st.error(
                f"Failed to fetch data: {result.get('error_message', 'Unknown error')}"
            )
            return

        runs_dir = Path("runs")
        runs_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_path = runs_dir / f"{ticker}_{timestamp}.json"
        calculated_path = runs_dir / f"{ticker}_{timestamp}_calculated.json"

        canonical_data = {
            "meta": result.get('meta', {}),
            "price_history": result.get('price_history', []),
            "fundamentals": {},
            "news": result.get('news', []),
        }

        with open(json_path, 'w') as f:
            json.dump(canonical_data, f, indent=2)

        calculated_data = {
            "meta": result.get('meta', {}),
            "info": result.get('info', {}),
            "calculated": result.get('calculated', {}),
            "overall_risk": result.get('overall_risk', {}),
            "timing": result.get('timing', {}),
        }

        with open(calculated_path, 'w') as f:
            json.dump(calculated_data, f, indent=2)

        st.session_state['current_ticker'] = ticker
        st.session_state['current_data_path'] = str(json_path)
        st.session_state['analysis_results'] = result
        st.session_state['adk_result'] = result
        st.session_state['last_analysis_time'] = datetime.now()

        st.session_state['chat_history'] = []
        if 'conversational_agent_initialized' in st.session_state:
            del st.session_state['conversational_agent_initialized']

        report_data = {
            'meta': result.get('meta', {}),
            'calculated': result.get('calculated', {}),
        }
        pre_gen = pre_generate_reports(report_data, ticker, timestamp)
        st.session_state['pregenerated_reports'] = pre_gen

        timing = result.get('timing', {})
        total_time = timing.get('total_ms', 0) / 1000

        st.success(f"Analysis complete for {ticker} in {total_time:.1f}s!")
        st.rerun()

    except Exception as e:
        logger.error(f"Error during analysis: {str(e)}")
        st.error(f"Error during analysis: {str(e)}")
        import traceback
        st.code(traceback.format_exc())


def show_overview():
    """Show overview tab with news and sentiment."""
    st.header("📝 Company Overview")

    if 'current_data_path' not in st.session_state:
        st.info("👈 Enter a ticker and click 'Fetch & Analyze' to get started")
        return

    with open(st.session_state['current_data_path'], 'r') as f:
        data = json.load(f)

    meta = data.get('meta', {})
    fundamentals = data.get('fundamentals', {})
    ticker = meta.get('ticker', 'Unknown')

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Company", meta.get('company_name', 'N/A'))
    with col2:
        st.metric("Exchange", meta.get('exchange', 'N/A'))
    with col3:
        st.metric("Currency", meta.get('currency', 'N/A'))
    with col4:
        market_cap = meta.get('market_cap')
        if market_cap:
            if market_cap >= 1e12:
                st.metric("Market Cap", f"${market_cap/1e12:.2f}T")
            elif market_cap >= 1e9:
                st.metric("Market Cap", f"${market_cap/1e9:.2f}B")
            elif market_cap >= 1e6:
                st.metric("Market Cap", f"${market_cap/1e6:.2f}M")
            else:
                st.metric("Market Cap", f"${market_cap:,.0f}")
        else:
            st.metric("Market Cap", "N/A")

    st.markdown("---")

    st.subheader("📈 Price History")
    price_history = data.get('price_history', [])
    if price_history:
        import pandas as pd
        df = pd.DataFrame(price_history)
        df['date'] = pd.to_datetime(df['date'])
        st.line_chart(df.set_index('date')['close'])

    st.markdown("---")

    st.subheader(f"📰 News & Sentiment Analysis for {ticker}")
    news = data.get('news', [])

    if news:
        valid_news = []
        for article in news:
            title = article.get('title', '').strip()
            if title and title != 'No title' and len(title) > 5:
                valid_news.append(article)

        marketaux_news = [
            n for n in valid_news if n.get('type') == 'marketaux'
        ]

        if marketaux_news:
            sentiments = [
                n.get('sentiment', 0) for n in marketaux_news
                if n.get('sentiment') is not None
            ]
            if sentiments:
                avg_sentiment = sum(sentiments) / len(sentiments)
                if avg_sentiment > 0.6:
                    sentiment_label = "🟢 Bullish"
                elif avg_sentiment < 0.4:
                    sentiment_label = "🔴 Bearish"
                else:
                    sentiment_label = "🟡 Neutral"

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Average Sentiment", f"{avg_sentiment:.2f}")
                with col2:
                    st.metric("Sentiment Label", sentiment_label)
                with col3:
                    st.metric("News Articles", len(marketaux_news))

        calculated_path = st.session_state['current_data_path'].replace(
            '.json', '_calculated.json')
        if Path(calculated_path).exists():
            with open(calculated_path, 'r') as f:
                calc_data = json.load(f)

            with st.expander("🤖 AI News Analysis", expanded=True):
                news_summary = news_agent.analyze_news(valid_news, ticker)
                st.markdown(news_summary)

        st.subheader(f"📄 Recent Articles for {ticker}")
        displayed_count = 0
        for article in valid_news[:15]:
            if displayed_count >= 10:
                break

            title = article.get('title', '').strip()
            description = article.get('description', '').strip()
            source = article.get('source', '').strip()
            url = article.get('url', '').strip()
            published_at = article.get('published_at', '')

            if not title or title == 'No title':
                continue

            sentiment = article.get('sentiment')
            sentiment_icon = ""
            if sentiment is not None:
                sentiment_icon = "🟢" if sentiment > 0.6 else (
                    "🔴" if sentiment < 0.4 else "🟡")

            source_type = article.get('type', 'unknown')
            source_badge = "📰 MarketAux" if source_type == 'marketaux' else (
                "📡 Yahoo" if source_type == 'yahoo_finance' else "📋 Sample")

            display_title = title[:80] + "..." if len(title) > 80 else title

            with st.expander(f"{sentiment_icon} {display_title}"):
                if description:
                    st.write(description)

                info_cols = []
                info_items = []

                if source:
                    info_items.append(("Source", f"{source} ({source_badge})"))
                if published_at:
                    pub_display = published_at[:10] if len(
                        published_at) > 10 else published_at
                    info_items.append(("Published", pub_display))
                if sentiment is not None:
                    info_items.append(("Sentiment", f"{sentiment:.2f}"))

                if info_items:
                    cols = st.columns(len(info_items))
                    for i, (label, value) in enumerate(info_items):
                        with cols[i]:
                            st.caption(f"{label}: {value}")

                if url and url.startswith('http'):
                    st.link_button("Read more", url)

            displayed_count += 1

        if displayed_count == 0:
            st.info("No valid news articles available for this stock.")
    else:
        st.info("No news articles available for this stock.")


def show_metrics():
    """Show metrics tab with AI summaries."""
    st.header("📈 Financial Metrics")

    if 'current_data_path' not in st.session_state:
        st.info("👈 Run analysis first")
        return

    calculated_path = st.session_state['current_data_path'].replace(
        '.json', '_calculated.json')
    if not Path(calculated_path).exists():
        st.warning("No calculated metrics found. Run analysis first.")
        return

    with open(calculated_path, 'r') as f:
        data = json.load(f)

    calculated = data.get('calculated', {})

    st.subheader("💼 Profitability Metrics")

    with st.expander("🤖 AI Profitability Analysis", expanded=True):
        prof_summary = summarization_agent.summarize_profitability(data)
        st.markdown(prof_summary)

    st.markdown("**What these metrics mean:**")
    st.caption("""
    - **Gross Margin**: Profit after direct costs (higher is better, >40% is excellent)
    - **Operating Margin**: Profit after operating expenses (>15% is good)
    - **Net Margin**: Final profit margin after all costs (>10% is healthy)
    - **ROE**: Return generated on shareholder equity (>15% is attractive)
    - **ROA**: Efficiency in using assets to generate profit (>5% is decent)
    - **ROIC**: Return on capital invested in the business (>10% indicates value creation)
    """)

    prof = calculated.get('profitability', {})
    col1, col2, col3 = st.columns(3)
    with col1:
        show_metric_with_provenance("Gross Margin", prof.get('gross_margin'))
        show_metric_with_provenance("Operating Margin",
                                    prof.get('operating_margin'))
    with col2:
        show_metric_with_provenance("Net Margin", prof.get('net_margin'))
        show_metric_with_provenance("ROA", prof.get('roa'))
    with col3:
        show_metric_with_provenance("ROE", prof.get('roe'))
        show_metric_with_provenance("ROIC", prof.get('roic'))

    st.markdown("---")

    st.subheader("💧 Liquidity Metrics")

    with st.expander("🤖 AI Liquidity & Leverage Analysis", expanded=True):
        liq_summary = summarization_agent.summarize_liquidity_leverage(data)
        st.markdown(liq_summary)

    st.markdown("**What these metrics mean:**")
    st.caption("""
    - **Current Ratio**: Ability to pay short-term debts (>1.5 is comfortable, >2 is strong)
    - **Quick Ratio**: Liquid assets vs short-term debts (>1 is good)
    - **Cash Ratio**: Cash available for immediate obligations
    - **OCF Ratio**: Operating cash flow relative to current liabilities (>1 is healthy)
    """)

    liq = calculated.get('liquidity', {})
    cashflow = calculated.get('cashflow', {})
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        show_metric_with_provenance("Current Ratio", liq.get('current_ratio'))
    with col2:
        show_metric_with_provenance("Quick Ratio", liq.get('quick_ratio'))
    with col3:
        show_metric_with_provenance("Cash Ratio", liq.get('cash_ratio'))
    with col4:
        show_metric_with_provenance("OCF Ratio",
                                    cashflow.get('operating_cash_flow_ratio'))

    st.markdown("---")

    st.subheader("⚖️ Leverage Metrics")
    st.markdown("**What these metrics mean:**")
    st.caption("""
    - **Debt to Equity**: Total debt relative to shareholder equity (<1 is conservative)
    - **Debt to Assets**: Portion of assets financed by debt (<0.5 is low leverage)
    - **Interest Coverage**: Ability to pay interest (>3x is comfortable, >5x is strong)
    - **Altman Z-Score**: Bankruptcy prediction (>2.99 safe, 1.81-2.99 grey zone, <1.81 distress)
    """)

    lev = calculated.get('leverage', {})
    risk_financial = calculated.get('risk_financial', {})
    col1, col2, col3 = st.columns(3)
    with col1:
        show_metric_with_provenance("Debt to Equity",
                                    lev.get('debt_to_equity'))
        show_metric_with_provenance("Debt to Assets",
                                    lev.get('debt_to_assets'))
    with col2:
        show_metric_with_provenance("Interest Coverage",
                                    lev.get('interest_coverage'))
    with col3:
        z_score_data = risk_financial.get('altman_z_score', {})
        if z_score_data and z_score_data.get('value') is not None:
            st.metric("Altman Z-Score",
                      f"{z_score_data.get('value'):.2f}",
                      help=f"{z_score_data.get('interpretation', '')}")
        else:
            st.metric("Altman Z-Score", "N/A")

    st.markdown("---")

    st.subheader("⚡ Efficiency Metrics")
    st.markdown("**What these metrics mean:**")
    st.caption("""
    - **Asset Turnover**: Revenue generated per dollar of assets (higher is more efficient)
    - **Inventory Turnover**: How quickly inventory is sold (N/A for tech/service companies)
    - **Receivables Turnover**: How quickly receivables are collected
    - **Days Sales Outstanding (DSO)**: Average days to collect payment
    - **Working Capital Turnover**: Efficiency of working capital usage
    """)

    eff = calculated.get('efficiency', {})
    col1, col2, col3 = st.columns(3)
    with col1:
        show_metric_with_provenance("Asset Turnover",
                                    eff.get('asset_turnover'))
        show_metric_with_provenance("Inventory Turnover",
                                    eff.get('inventory_turnover'))
    with col2:
        show_metric_with_provenance("Receivables Turnover",
                                    eff.get('receivables_turnover'))
    with col3:
        pass

    st.markdown("---")

    st.subheader("📈 Growth Metrics")
    st.markdown("**What these metrics mean:**")
    st.caption("""
    - **Revenue Growth YoY**: Year-over-year revenue change
    - **Net Income Growth YoY**: Year-over-year profit change
    - **EPS Growth YoY**: Earnings per share growth
    - **FCF Growth YoY**: Free cash flow growth
    - **Operating Income Growth**: Operating profit growth rate
    """)

    growth = calculated.get('growth', {})
    col1, col2, col3 = st.columns(3)
    with col1:
        show_metric_with_provenance("Revenue Growth",
                                    growth.get('revenue_growth'))
        show_metric_with_provenance("Net Income Growth",
                                    growth.get('net_income_growth'))
    with col2:
        show_metric_with_provenance("EPS Growth", growth.get('eps_growth'))
        show_metric_with_provenance("FCF Growth", growth.get('fcf_growth'))
    with col3:
        show_metric_with_provenance("Operating Income Growth",
                                    growth.get('operating_income_growth'))

    st.markdown("---")

    st.subheader("💵 Cash Flow Metrics")
    st.markdown("**What these metrics mean:**")
    st.caption("""
    - **Free Cash Flow**: Cash available after capital expenditures
    - **FCF Yield**: FCF relative to market cap (higher is better value)
    - **Cash Flow Margin**: Operating cash flow as % of revenue
    - **Cash Conversion Cycle**: Days to convert investments back to cash
    """)

    cf = calculated.get('cashflow', {})
    col1, col2, col3 = st.columns(3)
    with col1:
        show_metric_with_provenance("Free Cash Flow", cf.get('free_cash_flow'))
    with col2:
        show_metric_with_provenance("Cash Flow Margin",
                                    cf.get('cash_flow_margin'))
    with col3:
        show_metric_with_provenance("OCF Ratio",
                                    cf.get('operating_cash_flow_ratio'))


def show_valuation():
    """Show valuation tab with valuation multiples."""
    st.header("💰 Valuation Analysis")

    if 'current_data_path' not in st.session_state:
        st.info("👈 Run analysis first")
        return

    calculated_path = st.session_state['current_data_path'].replace(
        '.json', '_calculated.json')
    if not Path(calculated_path).exists():
        st.warning("No calculated metrics found.")
        return

    with open(calculated_path, 'r') as f:
        data = json.load(f)

    calculated = data.get('calculated', {})
    val = calculated.get('valuation', {})

    with st.expander("🤖 AI Valuation Analysis", expanded=True):
        val_summary = summarization_agent.summarize_valuation(data)
        st.markdown(val_summary)

    st.subheader("📊 Valuation Multiples")
    st.markdown("**What these metrics mean:**")
    st.caption("""
    - **P/E Ratio**: Price relative to earnings (lower may indicate value, but context matters)
    - **P/B Ratio**: Price relative to book value (<1 may indicate undervaluation)
    - **P/S Ratio**: Price relative to sales
    - **EV/EBITDA**: Enterprise value to EBITDA (lower is generally cheaper)
    - **PEG Ratio**: P/E adjusted for growth (<1 suggests undervalued growth)
    - **Dividend Yield**: Annual dividend as percentage of stock price
    """)

    col1, col2, col3 = st.columns(3)
    with col1:
        show_metric_with_provenance("P/E Ratio", val.get('pe_ratio'))
        show_metric_with_provenance("Forward P/E", val.get('forward_pe'))
    with col2:
        show_metric_with_provenance("P/B Ratio", val.get('price_to_book'))
        show_metric_with_provenance("P/S Ratio", val.get('price_to_sales'))
    with col3:
        show_metric_with_provenance("EV/EBITDA", val.get('ev_to_ebitda'))
        show_metric_with_provenance("Dividend Yield",
                                    val.get('dividend_yield'))

    st.markdown("---")

    st.subheader("📊 Additional Valuation Metrics")
    col1, col2, col3 = st.columns(3)
    with col1:
        show_metric_with_provenance("PEG Ratio", val.get('peg_ratio'))
        show_metric_with_provenance("Enterprise Value",
                                    val.get('enterprise_value'))
    with col2:
        show_metric_with_provenance("Book Value Per Share",
                                    val.get('book_value_per_share'))
    with col3:
        show_metric_with_provenance("Earnings Yield",
                                    val.get('earnings_yield'))


def show_risk():
    """Show risk analysis tab with AI summary."""
    st.header("⚠️ Risk Analysis")

    if 'current_data_path' not in st.session_state:
        st.info("👈 Run analysis first")
        return

    calculated_path = st.session_state['current_data_path'].replace(
        '.json', '_calculated.json')
    if not Path(calculated_path).exists():
        st.warning("No calculated metrics found.")
        return

    with open(calculated_path, 'r') as f:
        data = json.load(f)

    calculated = data.get('calculated', {})

    with st.expander("🤖 AI Risk Analysis", expanded=True):
        risk_summary = summarization_agent.summarize_risk(data)
        st.markdown(risk_summary)

    st.subheader("📉 Market Risk")
    st.markdown("**What these metrics mean:**")
    st.caption("""
    - **Volatility**: Annualized standard deviation of returns (higher = more risky)
    - **Beta**: Stock movement relative to market (>1 = more volatile than market)
    - **Alpha**: Excess return above expected (positive = outperformance)
    - **Sharpe Ratio**: Risk-adjusted return (>1 is good, >2 is excellent)
    - **VaR 95%**: Maximum expected daily loss 95% of the time
    - **Max Drawdown**: Largest peak-to-trough decline
    """)

    market_risk = calculated.get('risk_market', {})

    col1, col2, col3 = st.columns(3)
    with col1:
        show_metric_with_provenance("Volatility",
                                    market_risk.get('volatility'))
        show_metric_with_provenance("Beta", market_risk.get('beta'))
    with col2:
        show_metric_with_provenance("Alpha", market_risk.get('alpha'))
        show_metric_with_provenance("Sharpe Ratio",
                                    market_risk.get('sharpe_ratio'))
    with col3:
        show_metric_with_provenance("Max Drawdown",
                                    market_risk.get('max_drawdown'))
        show_metric_with_provenance("VaR 95%", market_risk.get('var_95'))

    composite = market_risk.get('composite_risk_score', {})
    if composite.get('value') is not None:
        risk_level = composite.get('interpretation', 'Unknown')
        risk_color = {
            "low": "🟢",
            "medium": "🟡",
            "high": "🔴"
        }.get(risk_level, "⚪")
        st.metric(
            "Market Risk Score",
            f"{risk_color} {composite['value']}/100 ({risk_level.title()})")

    st.markdown("---")

    st.subheader("💼 Financial Risk")
    st.markdown("**What these metrics mean:**")
    st.caption("""
    - **Credit Risk**: Risk of debt default (lower score = lower risk)
    - **Liquidity Risk**: Risk of not meeting short-term obligations
    - **Operational Risk**: Risk from business operations inefficiency
    - **Financial Health Score**: Overall financial stability (higher = healthier)
    """)

    financial_risk = calculated.get('risk_financial', {})

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        credit = financial_risk.get('credit_risk_score', {})
        if credit and credit.get('value') is not None:
            interpretation = credit.get('interpretation', 'N/A')
            level = interpretation.lower() if interpretation else 'n/a'
            color = "🟢" if "low" in level else (
                "🟡" if "moderate" in level else "🔴")
            st.metric(
                "Credit Risk",
                f"{color} {credit.get('value', 0)}/100",
                help=
                f"Level: {interpretation}\nFormula: {credit.get('formula', '')}"
            )
        else:
            st.metric("Credit Risk", "N/A")
    with col2:
        liquidity = financial_risk.get('liquidity_risk_score', {})
        if liquidity and liquidity.get('value') is not None:
            interpretation = liquidity.get('interpretation', 'N/A')
            level = interpretation.lower() if interpretation else 'n/a'
            color = "🟢" if "low" in level else (
                "🟡" if "moderate" in level else "🔴")
            st.metric(
                "Liquidity Risk",
                f"{color} {liquidity.get('value', 0)}/100",
                help=
                f"Level: {interpretation}\nFormula: {liquidity.get('formula', '')}"
            )
        else:
            st.metric("Liquidity Risk", "N/A")
    with col3:
        operational = financial_risk.get('operational_risk_score', {})
        if operational and operational.get('value') is not None:
            interpretation = operational.get('interpretation', 'N/A')
            level = interpretation.lower() if interpretation else 'n/a'
            color = "🟢" if "low" in level else (
                "🟡" if "moderate" in level else "🔴")
            st.metric(
                "Operational Risk",
                f"{color} {operational.get('value', 0)}/100",
                help=
                f"Level: {interpretation}\nFormula: {operational.get('formula', '')}"
            )
        else:
            st.metric("Operational Risk", "N/A")
    with col4:
        z_score = financial_risk.get('altman_z_score', {})
        if z_score and z_score.get('value') is not None:
            interpretation = z_score.get('interpretation', 'N/A')
            level = interpretation.lower() if interpretation else 'n/a'
            color = "🟢" if "safe" in level else (
                "🟡" if "grey" in level else "🔴")
            st.metric(
                "Altman Z-Score",
                f"{color} {z_score.get('value', 0):.2f}",
                help=
                f"Level: {interpretation}\nFormula: {z_score.get('formula', '')}"
            )
        else:
            st.metric("Altman Z-Score", "N/A")


def show_reports():
    """Show reports tab with instant downloads from pre-generated reports."""
    st.header("📄 Reports")

    if 'current_data_path' not in st.session_state:
        st.info("👈 Run analysis first")
        return

    pre_gen = st.session_state.get('pregenerated_reports', {})
    current_ticker = st.session_state.get('current_ticker', '')
    
    st.subheader("📥 Download Reports (Instant)")
    
    col1, col2 = st.columns(2)
    with col1:
        if pre_gen.get('pdf_content'):
            pdf_name = Path(pre_gen['pdf_path']).name if pre_gen.get('pdf_path') else f"{current_ticker}_report.pdf"
            st.download_button(
                label="📄 Download PDF Report",
                data=pre_gen['pdf_content'],
                file_name=pdf_name,
                mime="application/pdf",
                use_container_width=True,
                type="primary",
                key="instant_pdf_dl"
            )
        else:
            if st.button("📄 Generate PDF Report", use_container_width=True, type="primary"):
                generate_pdf_report()
    
    with col2:
        if pre_gen.get('html_content'):
            html_name = Path(pre_gen['html_path']).name if pre_gen.get('html_path') else f"{current_ticker}_report.html"
            st.download_button(
                label="🌐 Download HTML Report",
                data=pre_gen['html_content'],
                file_name=html_name,
                mime="text/html",
                use_container_width=True,
                type="primary",
                key="instant_html_dl"
            )
        else:
            if st.button("🌐 Generate HTML Report", use_container_width=True, type="primary"):
                generate_html_report()

    st.markdown("---")
    st.subheader("📂 All Reports")

    if 'reports_list' not in st.session_state:
        st.session_state['reports_list'] = None
    
    reports_dir = Path("reports")
    if reports_dir.exists():
        html_reports = list(reports_dir.glob(f"{current_ticker}_*.html"))
        pdf_reports = list(reports_dir.glob(f"{current_ticker}_*.pdf"))
        all_reports = sorted(html_reports + pdf_reports,
                             key=lambda x: x.stat().st_mtime if x.exists() else 0,
                             reverse=True)
    else:
        all_reports = []

    if all_reports:
        for i, report in enumerate(all_reports[:10]):
            if not report.exists():
                continue
            col1, col2, col3 = st.columns([3, 1, 1])

            with col1:
                st.text(f"📄 {report.name}")

            with col2:
                try:
                    if report.suffix == '.html':
                        content = report.read_text()
                        st.download_button(label="📥", data=content,
                                           file_name=report.name, mime="text/html",
                                           key=f"dl_{report.name}_{i}")
                    else:
                        content = report.read_bytes()
                        st.download_button(label="📥", data=content,
                                           file_name=report.name, mime="application/pdf",
                                           key=f"dl_{report.name}_{i}")
                except:
                    st.text("Error")

            with col3:
                if st.button("🗑️", key=f"del_{report.name}_{i}"):
                    report.unlink()
                    if pre_gen.get('pdf_path') == str(report) or pre_gen.get('html_path') == str(report):
                        st.session_state['pregenerated_reports'] = {}
                    st.rerun()

        st.markdown("---")
        if st.button("🗑️ Delete All", type="secondary"):
            for report in all_reports:
                try:
                    report.unlink()
                except:
                    pass
            st.session_state['pregenerated_reports'] = {}
            st.rerun()
    else:
        st.info("No reports available yet.")


def generate_pdf_report():
    """Generate a PDF report for the current analysis - optimized for speed."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib import colors
        from reportlab.lib.units import inch
    except ImportError:
        st.error("PDF generation library not available. Please use HTML report instead.")
        return

    data_path = st.session_state.get('current_data_path')
    if not data_path:
        st.error("No analysis data available")
        return

    with st.spinner("Generating PDF report..."):
        try:
            data = load_report_data(data_path)

            meta = data.get('meta', {})
            ticker = meta.get('ticker', 'UNKNOWN')
            company_name = meta.get('company_name', ticker)
            calculated = data.get('calculated', {})

            reports_dir = Path("reports")
            reports_dir.mkdir(exist_ok=True)

            safe_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            pdf_path = reports_dir / f"{ticker}_{safe_timestamp}_report.pdf"

            doc = SimpleDocTemplate(str(pdf_path), pagesize=letter,
                                    leftMargin=0.75*inch, rightMargin=0.75*inch,
                                    topMargin=0.75*inch, bottomMargin=0.75*inch)
            styles = getSampleStyleSheet()
            story = []

            title_style = ParagraphStyle('Title', parent=styles['Title'],
                                         fontSize=24, spaceAfter=30)
            subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'],
                                            fontSize=12, spaceAfter=20)
            
            table_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ])

            story.append(Paragraph(f"{company_name} ({ticker})", title_style))
            story.append(Paragraph("Stock Analysis Report", styles['Heading2']))
            story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", subtitle_style))
            story.append(Spacer(1, 0.5 * inch))

            prof = calculated.get('profitability', {})
            story.append(Paragraph("Profitability Metrics", styles['Heading2']))
            prof_data = [['Metric', 'Value'],
                         ['Gross Margin', format_metric_value(prof.get('gross_margin'))],
                         ['Operating Margin', format_metric_value(prof.get('operating_margin'))],
                         ['Net Margin', format_metric_value(prof.get('net_margin'))],
                         ['ROE', format_metric_value(prof.get('roe'))],
                         ['ROA', format_metric_value(prof.get('roa'))],
                         ['ROIC', format_metric_value(prof.get('roic'))]]
            table = Table(prof_data, colWidths=[2.5 * inch, 2 * inch])
            table.setStyle(table_style)
            story.append(table)
            story.append(Spacer(1, 0.3 * inch))

            val = calculated.get('valuation', {})
            story.append(Paragraph("Valuation Metrics", styles['Heading2']))
            val_data = [['Metric', 'Value'],
                        ['P/E Ratio', format_metric_value(val.get('pe_ratio'))],
                        ['P/B Ratio', format_metric_value(val.get('price_to_book'))],
                        ['P/S Ratio', format_metric_value(val.get('price_to_sales'))],
                        ['EV/EBITDA', format_metric_value(val.get('ev_to_ebitda'))],
                        ['Dividend Yield', format_metric_value(val.get('dividend_yield'))],
                        ['PEG Ratio', format_metric_value(val.get('peg_ratio'))],
                        ['Enterprise Value', format_metric_value(val.get('enterprise_value'))]]
            table = Table(val_data, colWidths=[2.5 * inch, 2 * inch])
            table.setStyle(table_style)
            story.append(table)
            story.append(Spacer(1, 0.3 * inch))

            risk = calculated.get('risk_market', {})
            story.append(Paragraph("Risk Metrics", styles['Heading2']))
            risk_data = [['Metric', 'Value'],
                         ['Volatility', format_metric_value(risk.get('volatility'))],
                         ['Beta', format_metric_value(risk.get('beta'))],
                         ['Sharpe Ratio', format_metric_value(risk.get('sharpe_ratio'))],
                         ['Max Drawdown', format_metric_value(risk.get('max_drawdown'))]]
            table = Table(risk_data, colWidths=[2.5 * inch, 2 * inch])
            table.setStyle(table_style)
            story.append(table)

            story.append(Spacer(1, 0.5 * inch))
            story.append(Paragraph("Disclaimer: This report is for informational purposes only.", styles['Normal']))

            doc.build(story)

        except Exception as e:
            st.error(f"Error generating PDF: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
            return

    st.success(f"Report generated: {pdf_path.name}")
    with open(pdf_path, 'rb') as f:
        st.download_button(label="📥 Download PDF Report",
                           data=f.read(),
                           file_name=pdf_path.name,
                           mime="application/pdf",
                           key=f"dl_pdf_{safe_timestamp}")


def generate_html_report():
    """Generate an HTML report for the current analysis - optimized for speed."""
    data_path = st.session_state.get('current_data_path')
    if not data_path:
        st.error("No analysis data available")
        return

    with st.spinner("Generating HTML report..."):
        try:
            data = load_report_data(data_path)

            meta = data.get('meta', {})
            ticker = meta.get('ticker', 'UNKNOWN')
            company_name = meta.get('company_name', ticker)
            calculated = data.get('calculated', {})

            safe_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>{company_name} ({ticker}) - Stock Analysis Report</title>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
        .container {{ max-width: 1000px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #1a1a2e; border-bottom: 3px solid #4a90d9; padding-bottom: 10px; }}
        h2 {{ color: #16213e; margin-top: 30px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        th {{ background: #4a90d9; color: white; padding: 12px; text-align: left; }}
        td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
        tr:hover {{ background: #f5f5f5; }}
        .value {{ font-weight: bold; color: #1a1a2e; }}
        .footer {{ text-align: center; margin-top: 40px; color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{company_name} ({ticker})</h1>
        <p>Stock Analysis Report | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
        
        <h2>Profitability Metrics</h2>
        <table>
            <tr><th>Metric</th><th>Value</th><th>Formula</th></tr>
            {generate_metric_rows(calculated.get('profitability', {}))}
        </table>
        
        <h2>Valuation Metrics</h2>
        <table>
            <tr><th>Metric</th><th>Value</th><th>Formula</th></tr>
            {generate_metric_rows(calculated.get('valuation', {}))}
        </table>
        
        <h2>Liquidity Metrics</h2>
        <table>
            <tr><th>Metric</th><th>Value</th><th>Formula</th></tr>
            {generate_metric_rows(calculated.get('liquidity', {}))}
        </table>
        
        <h2>Leverage Metrics</h2>
        <table>
            <tr><th>Metric</th><th>Value</th><th>Formula</th></tr>
            {generate_metric_rows(calculated.get('leverage', {}))}
        </table>
        
        <h2>Growth Metrics</h2>
        <table>
            <tr><th>Metric</th><th>Value</th><th>Formula</th></tr>
            {generate_metric_rows(calculated.get('growth', {}))}
        </table>
        
        <h2>Risk Assessment</h2>
        <table>
            <tr><th>Risk Type</th><th>Level</th><th>Score</th></tr>
            {generate_risk_rows(calculated.get('risk_financial', {}))}
        </table>
        
        <div class="footer">
            <p>Generated by Stock Analytics Agent</p>
            <p>Disclaimer: This report is for informational purposes only and should not be considered financial advice.</p>
        </div>
    </div>
</body>
</html>"""

            reports_dir = Path("reports")
            reports_dir.mkdir(exist_ok=True)
            html_path = reports_dir / f"{ticker}_{safe_timestamp}_report.html"

            with open(html_path, 'w') as f:
                f.write(html_content)

        except Exception as e:
            st.error(f"Error generating HTML: {str(e)}")
            return

    st.success(f"Report generated: {html_path.name}")
    st.download_button(label="📥 Download HTML Report",
                       data=html_content,
                       file_name=html_path.name,
                       mime="text/html",
                       key=f"dl_html_{safe_timestamp}")


def format_metric_value(metric_data):
    """Format metric value for display."""
    if metric_data is None:
        return "N/A"

    if isinstance(metric_data, dict):
        value = metric_data.get('value')
        if value is None:
            return f"N/A ({metric_data.get('null_reason', 'unknown')})"
        unit = metric_data.get('unit', '')
        if unit in ['decimal', 'ratio']:
            return f"{value * 100:.2f}%"
        elif unit == 'percentage':
            return f"{value:.2f}%"
        elif unit == 'percentage_decimal':
            return f"{value:.2f}%"
        elif unit == 'currency':
            if abs(value) >= 1e12:
                return f"${value/1e12:.2f}T"
            elif abs(value) >= 1e9:
                return f"${value/1e9:.2f}B"
            elif abs(value) >= 1e6:
                return f"${value/1e6:.2f}M"
            else:
                return f"${value:,.2f}"
        elif unit == 'days':
            return f"{value:.1f} days"
        elif unit == 'score':
            return f"{value:.2f}"
        else:
            return f"{value:.2f}"
    return f"{metric_data:.2f}" if isinstance(metric_data,
                                              (int,
                                               float)) else str(metric_data)


def generate_metric_rows(metrics_dict):
    """Generate HTML table rows for metrics."""
    rows = []
    for key, metric in metrics_dict.items():
        if isinstance(metric, dict) and 'value' in metric:
            value = format_metric_value(metric)
            formula = metric.get('formula', '-')
            rows.append(
                f"<tr><td>{key.replace('_', ' ').title()}</td><td class='value'>{value}</td><td>{formula}</td></tr>"
            )
    return '\n'.join(
        rows) if rows else "<tr><td colspan='3'>No data available</td></tr>"


def generate_risk_rows(metrics_dict):
    """Generate HTML table rows for risk metrics."""
    rows = []
    for key, metric in metrics_dict.items():
        if isinstance(metric, dict):
            if 'score' in metric:
                score = metric.get('score', 'N/A')
                interp = metric.get('interpretation', '-')
                rows.append(
                    f"<tr><td>{key.replace('_', ' ').title()}</td><td class='value'>{interp}</td><td>{score}/100</td></tr>"
                )
    return '\n'.join(
        rows) if rows else "<tr><td colspan='3'>No data available</td></tr>"


def show_metric_with_provenance(label: str, metric_data):
    """Display a metric with provenance information."""
    if metric_data is None:
        st.metric(label, "N/A")
        return

    if isinstance(metric_data, dict):
        value = metric_data.get('value')
        null_reason = metric_data.get('null_reason')
        provenance = metric_data.get('provenance', '')
        formula = metric_data.get('formula', '')
        interpretation = metric_data.get('interpretation', '')

        if value is not None:
            unit = metric_data.get('unit', '')
            if unit == 'decimal' or unit == 'ratio':
                if abs(value) < 10:
                    display_value = f"{value*100:.2f}%"
                else:
                    display_value = f"{value:.2f}"
            elif unit == 'percentage':
                display_value = f"{value:.2f}%"
            elif unit == 'percentage_decimal':
                display_value = f"{value:.2f}%"
            elif unit == 'currency':
                if abs(value) >= 1e12:
                    display_value = f"${value/1e12:.2f}T"
                elif abs(value) >= 1e9:
                    display_value = f"${value/1e9:.2f}B"
                elif abs(value) >= 1e6:
                    display_value = f"${value/1e6:.2f}M"
                else:
                    display_value = f"${value:,.2f}"
            elif unit == 'days':
                display_value = f"{value:.1f} days"
            elif unit == 'score':
                display_value = f"{value:.2f}"
            else:
                display_value = f"{value:.2f}"

            help_text = f"Formula: {formula}\nSource: {provenance}"
            if interpretation:
                help_text += f"\nInterpretation: {interpretation}"

            st.metric(label, display_value, help=help_text)
        else:
            help_text = f"Reason: {null_reason}"
            if null_reason and 'not_applicable' in null_reason:
                st.metric(label, "N/A*", help=help_text)
            else:
                st.metric(label, "N/A", help=help_text)
    else:
        st.metric(label, f"{metric_data:.2f}")


if __name__ == "__main__":
    main()
