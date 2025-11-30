# Stock Analytics Agent

A multi-agent, multi-tool, deterministic stock analytics system featuring comprehensive financial analysis, AI-powered insights, multi-agent orchestration, and CI/CD automation.

This project uses Google ADK (Agent Development Kit) to build a fully deterministic, testable, and production-ready financial analytics pipeline.

## Project Overview

This system implements a three-layer agent architecture using Google ADK (Agent Development Kit) for deterministic stock analysis:

- **Layer 1 (DeterministicDataAgent)**: Fetches data from Yahoo Finance and MarketAux APIs
- **Layer 2 (ParallelAgent)**: DeterministicRatioAgent, DeterministicValuationAgent, and DeterministicRiskAgent compute 30+ financial metrics concurrently
- **Layer 3 (DeterministicPresentationAgent)**: Generates comprehensive reports and summaries

### ADK Deterministic Orchestration

The system uses ADK's `SequentialAgent` and `ParallelAgent` for workflow orchestration, with custom `BaseAgent` subclasses for deterministic execution. This pattern allows:

- **ADK-driven workflow**: `Runner.run_async` executes the agent pipeline
- **Deterministic calculations**: Each agent calls existing calculation functions directly (no LLM inference for math)
- **State persistence**: Results flow between agents through explicit ADK session state updates using the session service
- **Tool-Based Agents**: All calculations run through ADK tools for deterministic, structured execution.
- **MCP Server**: Exposes the pipeline via an MCP endpoint with guardrails, input validation, rate-limiting, and safe output filtering.

```
SequentialAgent (StockAnalyticsPipeline)
├── Layer 1: DeterministicDataAgent
│     ├── Tools:
│     │     ├── YahooFinanceClient
│     │     └── MarketAuxClient
│     └── Output: Canonical JSON (Layer 1)
│
├── Layer 2: ParallelAgent (Layer2ParallelAgent)
│     ├── DeterministicRatioAgent
│     ├── DeterministicValuationAgent
│     └── DeterministicRiskAgent
│
│     Tools (python-function tools):
│       - Profitability Tools  
│       - Liquidity Tools  
│       - Valuation Tools  
│       - Market Risk Tools  
│       - Financial Risk Tools  
│       - Efficiency Tools  
│
│     Output: Enriched calculated metrics (Layer 2)
│
└── Layer 3: DeterministicPresentationAgent 
      ├── Report generator tools (PDF/HTML)
      ├── Summary tools
      └── AI Chattool (Gemini)

```

## Key Features

### Financial Analysis
- **30+ Metrics(python function tool)** across 9 categories:
  - Profitability (gross/operating/net margins, ROA, ROE, ROIC)
  - Liquidity (current/quick/cash ratios, working capital)
  - Leverage (debt-to-equity, debt-to-assets, interest coverage)
  - Efficiency (asset turnover, inventory turnover, receivables turnover)
  - Growth (revenue, net income, EPS, FCF, operating income growth)
  - Cash Flow (free cash flow, operating cash flow ratio, cash flow margin)
  - Valuation (P/E, forward P/E, P/B, P/S, EV/EBITDA, PEG, dividend yield)
  - Market Risk (beta, alpha, volatility, Sharpe ratio, VaR, max drawdown)
  - Financial Risk (Altman Z-score, credit/liquidity/operational risk scores)

### AI-Powered Chat
- ChatGPT-style conversational interface
- Gemini 2.0 Flash for intelligent analysis
- Long-term memory for context retention
- Natural language stock queries

### Report Generation
- Professional PDF reports via ReportLab
- HTML reports with styling
- Delete functionality for report management
- Executive summaries and investment recommendations

### Data Sources
- **Yahoo Finance**: Price history, fundamentals, precomputed ratios, company info
- **MarketAux API**: News articles with sentiment analysis

### MCP Guardrails & Validation
- Input validation (ticker format, required fundamentals) enforced before running pipelines.
- Rate limiting and execution time caps enforced by the MCP server’s guardrail policy.
- Output filtering applied before returning results.

### CI/CD Pipeline (GitHub Actions)
- This project uses a production-grade CI/CD pipeline located at `github/workflows/ci.yml`
- **Setup & Install**: Python 3.11 environment and Python 3.11 environment
- **Code Quality**: Linting with Ruff and Formatting check with Black
- **Automated Testing**: Runs unit, integration, and end-to-end tests and Generates coverage report
- **Packaging**: Builds the agent_engine_package bundle for deployment
- **Docker Build**: Builds a production-ready Docker image

## Quick Start

### Prerequisites
- Python 3.11+
- API Keys:
  - `GEMINI_API_KEY` - For AI chat and summarization
  - `MARKETAUX_API_KEY` - For news data (optional)

### Running the Application

```bash
streamlit run app.py

### Usage Example

```python
from src.adk_agents.orchestrator import run_stock_analysis, get_orchestrator

# Run comprehensive stock analysis via ADK Runner
result = run_stock_analysis("AAPL", period_days=252)

# Access calculated metrics
profitability = result['calculated']['profitability']
valuation = result['calculated']['valuation']
risk = result['calculated']['risk_market']
overall_risk = result["overall_risk"]

# Get the generated report
report = result['report']

# Access ADK components
orchestrator = get_orchestrator()
pipeline = orchestrator.get_pipeline()      # SequentialAgent
parallel = orchestrator.get_parallel_agent()  # ParallelAgent
runner = orchestrator.get_runner()          # Runner
```

## Streamlit UI Features

### Tabs

1. **Overview**: Company info, interactive price chart, recent news with sentiment
2. **Metrics**: All 30+ calculated financial metrics with AI analysis
3. **Valuation**: P/E, P/B, EV/EBITDA, PEG ratio analysis
4. **Risk**: Market risk (beta, alpha, volatility) and financial risk (Z-score)
5. **Reports**: Generate and download PDF/HTML reports with delete functionality
6. **Chat**: ChatGPT-style conversational AI for stock questions

## Data Storage

- `runs/` - Canonical JSON files: `<TICKER>_<TIMESTAMP>.json` and `<TICKER>_<TIMESTAMP>_calculated.json`
- `reports/` - Generated PDF/HTML reports
- `logs/agents/` - Agent execution logs and metrics

## Testing

Run the test suite:
```bash
pytest src/tests/
```

Run specific tests:
```bash
pytest src/tests/unit/test_profitability.py
pytest src/tests/integration/test_data_fetch.py
pytest src/tests/e2e/test_full_pipeline.py
```

## Environment Variables

- `GEMINI_API_KEY` - Google Gemini API key for AI agents
- `MARKETAUX_API_KEY` - MarketAux API key for news
- `DATABASE_URL` - PostgreSQL connection (for future use)

## Dependencies

**Google ADK & AI**:
- google-adk - Agent Development Kit (SequentialAgent, ParallelAgent, BaseAgent, Runner)
- google-genai - Gemini 2.0 Flash for conversational AI

**Financial Data**:
- yfinance - Yahoo Finance API for price history and fundamentals
- MarketAux API - News articles and sentiment analysis

**Frontend & Reporting**:
- Streamlit - Web framework for interactive dashboard
- ReportLab - Professional PDF report generation
- Plotly - Interactive charts

**Data Processing**:
- NumPy - Statistical calculations for risk metrics
- Pandas - Time series data handling

## License

MIT License
