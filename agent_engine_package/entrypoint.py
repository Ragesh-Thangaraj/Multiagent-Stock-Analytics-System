"""
GCP Agent Engine Entrypoint

This is the main entry point for the GCP Agent Engine deployment.
Orchestrates the three-layer execution model.
"""

import json
import logging
from typing import Dict, Any
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentEngineOrchestrator:
    """
    Orchestrates the multi-agent execution pipeline.
    
    Execution Model:
    - Layer 1: Data Fetch (sequential)
    - Layer 2: Calculations (parallel)
    - Layer 3: Presentation (sequential)
    """
    
    def __init__(self):
        self.execution_log = []
    
    def execute(self, ticker: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute full agent pipeline.
        
        Args:
            ticker: Stock symbol to analyze
            config: Optional configuration parameters
            
        Returns:
            Complete analysis results
        """
        logger.info(f"Starting agent engine execution for {ticker}")
        
        config = config or {}
        
        try:
            # Layer 1: Data Fetch
            logger.info("Layer 1: Data Fetch")
            canonical_data = self._execute_layer1(ticker, config)
            
            # Layer 2: Calculations (parallel)
            logger.info("Layer 2: Calculations")
            calculated_data = self._execute_layer2(canonical_data, config)
            
            # Layer 3: Presentation
            logger.info("Layer 3: Presentation")
            final_report = self._execute_layer3(calculated_data, config)
            
            logger.info(f"Agent engine execution completed for {ticker}")
            
            return {
                "status": "success",
                "ticker": ticker,
                "execution_log": self.execution_log,
                "results": final_report
            }
            
        except Exception as e:
            logger.error(f"Agent engine execution failed: {str(e)}")
            return {
                "status": "error",
                "ticker": ticker,
                "error": str(e),
                "execution_log": self.execution_log
            }
    
    def _execute_layer1(self, ticker: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Layer 1: Data Fetch Agent."""
        from src.data_agent.fetcher import DataFetcher
        
        self.execution_log.append({
            "layer": 1,
            "agent": "data_agent",
            "status": "started"
        })
        
        fetcher = DataFetcher()
        data = fetcher.fetch_and_save(ticker, period=config.get('period', '1y'))
        
        self.execution_log.append({
            "layer": 1,
            "agent": "data_agent",
            "status": "completed"
        })
        
        return data
    
    def _execute_layer2(self, canonical_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Layer 2: Calculation Agents (parallel)."""
        from src.agents.calculation_agent import CalculationAgent
        
        # Find the JSON file
        ticker = canonical_data["meta"]["ticker"]
        timestamp = canonical_data["meta"]["fetch_time"].replace(":", "-")
        json_path = f"runs/{ticker}_{timestamp}.json"
        
        self.execution_log.append({
            "layer": 2,
            "agents": ["calculation_agent", "ratio_agent", "valuation_agent", "risk_agent"],
            "status": "started"
        })
        
        # Execute calculation agent (which runs all calculations)
        agent = CalculationAgent()
        results = agent.execute(json_path)
        
        # Execute DCF with custom parameters if provided
        if config.get('run_dcf', True):
            dcf_results = agent.execute_dcf(
                json_path,
                wacc=config.get('wacc', 0.10),
                terminal_growth=config.get('terminal_growth', 0.025),
                forecast_years=config.get('forecast_years', 5)
            )
            results['dcf'] = dcf_results
        
        self.execution_log.append({
            "layer": 2,
            "agents": ["calculation_agent", "ratio_agent", "valuation_agent", "risk_agent"],
            "status": "completed",
            "successful": results['results']['successful'],
            "total": results['results']['total_modules']
        })
        
        return results
    
    def _execute_layer3(self, calculated_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Layer 3: Summarization and Presentation Agents."""
        self.execution_log.append({
            "layer": 3,
            "agents": ["summarization_agent", "presentation_agent", "voice_agent"],
            "status": "started"
        })
        
        # Layer 3 agents would be implemented here
        # For now, return the calculated data
        
        self.execution_log.append({
            "layer": 3,
            "agents": ["summarization_agent", "presentation_agent", "voice_agent"],
            "status": "completed"
        })
        
        return calculated_data


def main(event: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
    """
    Cloud Function entry point.
    
    Args:
        event: Cloud Function event with ticker and config
        context: Cloud Function context
        
    Returns:
        Execution results
    """
    ticker = event.get('ticker', 'AAPL')
    config = event.get('config', {})
    
    orchestrator = AgentEngineOrchestrator()
    results = orchestrator.execute(ticker, config)
    
    return results


if __name__ == "__main__":
    # Local testing
    test_event = {
        "ticker": "AAPL",
        "config": {
            "period": "1y",
            "wacc": 0.10,
            "terminal_growth": 0.025,
            "forecast_years": 5
        }
    }
    
    results = main(test_event)
    print(json.dumps(results, indent=2))
