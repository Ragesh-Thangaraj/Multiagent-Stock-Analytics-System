"""
GCP Agent Engine Entrypoint

This is the main entry point for the GCP Agent Engine deployment.
Orchestrates the three-layer execution model.
"""

import json
import logging
from typing import Dict, Any
from pathlib import Path
from src.adk_agents.orchestrator import run_stock_analysis


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main(event: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
    """
    Cloud Function entry point.

    Args:
        event: {
            "ticker": "AAPL",
            "period_days": 252
        }
        context: GCP context (unused)

    Returns:
        Dict with status, results, execution logs, etc.
    """

    # Extract inputs safely
    ticker = event.get("ticker", "AAPL")
    period_days = int(event.get("period_days", 252))

    logger.info(f"GCF execution started for ticker={ticker}, period_days={period_days}")

    # Run analysis using the existing ADK-based orchestrator
    result = run_stock_analysis(ticker, period_days)

    logger.info(f"GCF execution finished for ticker={ticker}")

    return result


# For local testing
if __name__ == "__main__":
    test_event = {
        "ticker": "AAPL",
        "period_days": 252
    }
    out = main(test_event)
    print(json.dumps(out, indent=2))