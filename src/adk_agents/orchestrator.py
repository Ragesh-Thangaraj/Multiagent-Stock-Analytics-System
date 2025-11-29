"""
Stock Analytics Orchestrator - Deterministic ADK Orchestration

Three-layer agent architecture using ADK BaseAgent subclasses for deterministic
execution within SequentialAgent/ParallelAgent graphs driven by Runner.run_async.

Architecture:
    SequentialAgent (StockAnalyticsPipeline)
    ├── DeterministicDataAgent (BaseAgent) - Layer 1
    ├── ParallelAgent (Layer2ParallelAgent) - Layer 2
    │   ├── DeterministicRatioAgent (BaseAgent)
    │   ├── DeterministicValuationAgent (BaseAgent)
    │   └── DeterministicRiskAgent (BaseAgent)
    └── DeterministicPresentationAgent (BaseAgent) - Layer 3

Each agent is a BaseAgent subclass that executes deterministic calculations
and returns structured data via EventActions.state_delta.
"""

import logging
import time
import asyncio
from typing import Dict, Any, Optional, AsyncGenerator

from pydantic import PrivateAttr

from google.adk.agents import SequentialAgent, ParallelAgent, BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from .data_agent import DataAgent, create_data_agent
from .ratio_agent import RatioAgent, create_ratio_agent
from .valuation_agent import ValuationAgent, create_valuation_agent
from .risk_agent import RiskAnalysisAgent, create_risk_agent
from .presentation_agent import PresentationAgent, create_presentation_agent
from .logging_monitor import setup_agent_logging
from .mcp.server import create_mcp_server
from .mcp.guardrails import SecurityPolicy

logger = logging.getLogger(__name__)


class PipelineExecutionError(Exception):
    """Raised when pipeline execution fails."""
    pass


class DeterministicDataAgent(BaseAgent):
    """
    Deterministic data fetching agent.
    
    BaseAgent subclass that executes fetch_stock_data deterministically
    and stores structured output in session state via EventActions.state_delta.
    """
    
    _data_agent: DataAgent = PrivateAttr()
    
    def __init__(self, data_agent: DataAgent):
        super().__init__(name="DeterministicDataAgent")
        self._data_agent = data_agent
    
    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        """Execute data fetching and store in session state via state_delta."""
        ticker = ctx.session.state.get('ticker', '')
        period_days = ctx.session.state.get('period_days', 252)
        
        logger.info(f"DeterministicDataAgent: Fetching data for {ticker}")
        
        result = self._data_agent.fetch_stock_data(ticker, period_days)
        
        yield Event(
            author=self.name,
            invocation_id=ctx.invocation_id,
            content=types.Content(
                role="model",
                parts=[types.Part(text=f"Fetched data for {ticker}: {result.get('status')}")]
            ),
            actions=EventActions(state_delta={"canonical_data": result})
        )


class DeterministicRatioAgent(BaseAgent):
    """
    Deterministic ratio calculation agent.
    
    BaseAgent subclass that executes calculate_all_ratios deterministically
    and stores structured output in session state via EventActions.state_delta.
    """
    
    _ratio_agent: RatioAgent = PrivateAttr()
    
    def __init__(self, ratio_agent: RatioAgent):
        super().__init__(name="DeterministicRatioAgent")
        self._ratio_agent = ratio_agent
    
    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        """Execute ratio calculations and store in session state via state_delta."""
        canonical_data = ctx.session.state.get('canonical_data', {})
        
        logger.info(f"DeterministicRatioAgent: Calculating ratios")
        
        result = self._ratio_agent.calculate_all_ratios(canonical_data)
        
        yield Event(
            author=self.name,
            invocation_id=ctx.invocation_id,
            content=types.Content(
                role="model",
                parts=[types.Part(text=f"Calculated ratio metrics")]
            ),
            actions=EventActions(state_delta={"ratio_metrics": result})
        )


class DeterministicValuationAgent(BaseAgent):
    """
    Deterministic valuation calculation agent.
    
    BaseAgent subclass that executes calculate_all_valuations deterministically
    and stores structured output in session state via EventActions.state_delta.
    """
    
    _valuation_agent: ValuationAgent = PrivateAttr()
    
    def __init__(self, valuation_agent: ValuationAgent):
        super().__init__(name="DeterministicValuationAgent")
        self._valuation_agent = valuation_agent
    
    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        """Execute valuation calculations and store in session state via state_delta."""
        canonical_data = ctx.session.state.get('canonical_data', {})
        
        logger.info(f"DeterministicValuationAgent: Calculating valuations")
        
        result = self._valuation_agent.calculate_all_valuations(canonical_data)
        
        yield Event(
            author=self.name,
            invocation_id=ctx.invocation_id,
            content=types.Content(
                role="model",
                parts=[types.Part(text=f"Calculated valuation metrics")]
            ),
            actions=EventActions(state_delta={"valuation_metrics": result})
        )


class DeterministicRiskAgent(BaseAgent):
    """
    Deterministic risk calculation agent.
    
    BaseAgent subclass that executes calculate_all_risks deterministically
    and stores structured output in session state via EventActions.state_delta.
    """
    
    _risk_agent: RiskAnalysisAgent = PrivateAttr()
    
    def __init__(self, risk_agent: RiskAnalysisAgent):
        super().__init__(name="DeterministicRiskAgent")
        self._risk_agent = risk_agent
    
    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        """Execute risk calculations and store in session state via state_delta."""
        canonical_data = ctx.session.state.get('canonical_data', {})
        
        logger.info(f"DeterministicRiskAgent: Calculating risks")
        
        result = self._risk_agent.calculate_all_risks(canonical_data)
        
        yield Event(
            author=self.name,
            invocation_id=ctx.invocation_id,
            content=types.Content(
                role="model",
                parts=[types.Part(text=f"Calculated risk metrics")]
            ),
            actions=EventActions(state_delta={"risk_metrics": result})
        )


class DeterministicPresentationAgent(BaseAgent):
    """
    Deterministic presentation agent.
    
    BaseAgent subclass that generates reports deterministically
    and stores structured output in session state via EventActions.state_delta.
    """
    
    _presentation_agent: PresentationAgent = PrivateAttr()
    
    def __init__(self, presentation_agent: PresentationAgent):
        super().__init__(name="DeterministicPresentationAgent")
        self._presentation_agent = presentation_agent
    
    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        """Generate report and store in session state via state_delta."""
        canonical_data = ctx.session.state.get('canonical_data', {})
        ratio_metrics = ctx.session.state.get('ratio_metrics', {})
        valuation_metrics = ctx.session.state.get('valuation_metrics', {})
        risk_metrics = ctx.session.state.get('risk_metrics', {})
        
        logger.info(f"DeterministicPresentationAgent: Generating report")
        
        result = self._presentation_agent.generate_report(
            canonical_data,
            ratio_metrics,
            valuation_metrics,
            risk_metrics,
        )
        
        yield Event(
            author=self.name,
            invocation_id=ctx.invocation_id,
            content=types.Content(
                role="model",
                parts=[types.Part(text=f"Generated report")]
            ),
            actions=EventActions(state_delta={"presentation_output": result})
        )


class StockAnalyticsOrchestrator:
    """
    Deterministic ADK Orchestrator for stock analytics.
    
    Uses ADK SequentialAgent/ParallelAgent for orchestration with
    BaseAgent subclasses for deterministic execution.
    
    Pipeline Structure:
        SequentialAgent (StockAnalyticsPipeline)
        ├── DeterministicDataAgent (Layer 1)
        ├── ParallelAgent (Layer2ParallelAgent)
        │   ├── DeterministicRatioAgent
        │   ├── DeterministicValuationAgent
        │   └── DeterministicRiskAgent
        └── DeterministicPresentationAgent (Layer 3)
    
    Execution via Runner.run_async ensures ADK drives the workflow.
    State is passed between agents via EventActions.state_delta.
    """
    
    def __init__(self, model: str = "gemini-2.0-flash"):
        """Initialize the Deterministic ADK Orchestrator."""
        self.model = model
        
        self.data_agent = create_data_agent(model)
        self.ratio_agent = create_ratio_agent(model)
        self.valuation_agent = create_valuation_agent(model)
        self.risk_agent = create_risk_agent(model)
        self.presentation_agent = create_presentation_agent(model)
        
        self.det_data_agent = DeterministicDataAgent(self.data_agent)
        self.det_ratio_agent = DeterministicRatioAgent(self.ratio_agent)
        self.det_valuation_agent = DeterministicValuationAgent(self.valuation_agent)
        self.det_risk_agent = DeterministicRiskAgent(self.risk_agent)
        self.det_presentation_agent = DeterministicPresentationAgent(self.presentation_agent)
        
        self.layer2_parallel = self._create_parallel_agent()
        self.pipeline = self._create_sequential_pipeline()
        
        self.session_service = InMemorySessionService()
        self.runner = Runner(
            agent=self.pipeline,
            app_name="stock_analytics",
            session_service=self.session_service
        )
        
        self.monitor = setup_agent_logging()
        
        self.mcp_server = create_mcp_server(
            policy=SecurityPolicy(
                max_api_calls_per_minute=100,
                max_calculation_timeout_seconds=60.0,
                require_valid_fundamentals=True,
            )
        )
        
        self.context: Dict[str, Any] = {}
        self._current_session_id: Optional[str] = None
        self._current_user_id: str = "stock_analytics_user"
        
        logger.info("StockAnalyticsOrchestrator initialized with Deterministic ADK Pattern")
        logger.info(f"  Pipeline: {self.pipeline.name} (SequentialAgent)")
        logger.info(f"  Layer2: {self.layer2_parallel.name} (ParallelAgent)")
    
    def _create_parallel_agent(self) -> ParallelAgent:
        """
        Create Layer 2 ParallelAgent with deterministic calculation agents.
        """
        return ParallelAgent(
            name="Layer2ParallelAgent",
            sub_agents=[
                self.det_ratio_agent,
                self.det_valuation_agent,
                self.det_risk_agent,
            ],
            description="Concurrent execution of DeterministicRatioAgent, DeterministicValuationAgent, DeterministicRiskAgent.",
        )
    
    def _create_sequential_pipeline(self) -> SequentialAgent:
        """
        Create the main SequentialAgent pipeline with deterministic agents.
        """
        return SequentialAgent(
            name="StockAnalyticsPipeline",
            sub_agents=[
                self.det_data_agent,
                self.layer2_parallel,
                self.det_presentation_agent,
            ],
            description="Sequential pipeline: DataAgent -> ParallelAgent -> PresentationAgent",
        )
    
    def _validate_with_guardrails(self, ticker: str, operation: str) -> tuple[bool, Optional[str]]:
        """Validate operation against MCP guardrails."""
        guardrails = self.mcp_server.guardrails
        
        is_valid, error_msg = guardrails.validate_input({'ticker': ticker})
        if not is_valid:
            return False, error_msg
        
        if not guardrails.check_rate_limit(operation):
            return False, "Rate limit exceeded"
            
        return True, None
    
    def _filter_output_with_guardrails(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """Filter output data through guardrails."""
        return self.mcp_server.guardrails.filter_output(output)
    
    def analyze_stock(self, ticker: str, period_days: int = 252) -> Dict[str, Any]:
        """
        Execute stock analysis using ADK Runner.run_async.
        
        Runs the SequentialAgent pipeline via Runner.run_async:
        1. DeterministicDataAgent (Layer 1) - fetches data
        2. ParallelAgent with DeterministicRatio/Valuation/RiskAgents (Layer 2)
        3. DeterministicPresentationAgent (Layer 3) - generates report
        
        All agents are BaseAgent subclasses that execute deterministically
        and store results in session state via EventActions.state_delta.
        
        Args:
            ticker: Stock ticker symbol
            period_days: Number of trading days for price history
            
        Returns:
            dict: Complete analysis results from session state
        """
        ticker = ticker.upper().strip()
        
        is_valid, error_msg = self._validate_with_guardrails(ticker, "analyze_stock")
        if not is_valid:
            return {
                "status": "error",
                "error_message": f"Guardrails validation failed: {error_msg}",
                "ticker": ticker,
            }
        
        period_days = self.mcp_server.guardrails.policy.validate_period(period_days)
        pipeline_id = self.monitor.start_pipeline(ticker)
        
        try:
            result = asyncio.run(
                self._execute_adk_runner(ticker, period_days, pipeline_id)
            )
            return self._filter_output_with_guardrails(result)
            
        except RuntimeError as e:
            if "cannot be called from a running event loop" in str(e):
                loop = asyncio.new_event_loop()
                try:
                    result = loop.run_until_complete(
                        self._execute_adk_runner(ticker, period_days, pipeline_id)
                    )
                    return self._filter_output_with_guardrails(result)
                finally:
                    loop.close()
            raise
            
        except PipelineExecutionError as e:
            logger.error(f"ADK Pipeline failed for {ticker}: {e}")
            self.monitor.end_pipeline("error")
            return {
                "status": "error",
                "error_message": str(e),
                "ticker": ticker,
                "pipeline_id": pipeline_id,
            }
            
        except Exception as e:
            logger.error(f"Unexpected error in pipeline for {ticker}: {e}")
            self.monitor.end_pipeline("error")
            return {
                "status": "error",
                "error_message": str(e),
                "ticker": ticker,
                "pipeline_id": pipeline_id,
            }
    
    async def _execute_adk_runner(self, ticker: str, period_days: int, pipeline_id: str) -> Dict[str, Any]:
        """
        Execute the ADK pipeline via Runner.run_async.
        
        The Runner executes the SequentialAgent pipeline:
        1. DeterministicDataAgent stores canonical_data via state_delta
        2. ParallelAgent runs DeterministicRatio/Valuation/RiskAgents concurrently
        3. DeterministicPresentationAgent generates report
        
        Results are retrieved from session state after execution.
        """
        import inspect
        
        session_id = f"adk_{ticker}_{int(time.time())}"
        self._current_session_id = session_id
        
        create_result = self.session_service.create_session(
            app_name="stock_analytics",
            user_id=self._current_user_id,
            session_id=session_id,
            state={"ticker": ticker, "period_days": period_days}
        )
        if inspect.isawaitable(create_result):
            await create_result
        
        message = types.Content(
            role="user",
            parts=[types.Part(text=f"Analyze stock {ticker}")]
        )
        
        logger.info(f"=== Executing ADK Runner for {ticker} ===")
        logger.info(f"Pipeline: {self.pipeline.name}")
        logger.info(f"Session: {session_id}")
        
        start_time = time.time()
        
        async for event in self.runner.run_async(
            user_id=self._current_user_id,
            session_id=session_id,
            new_message=message
        ):
            if event.author:
                logger.debug(f"Event from {event.author}")
        
        adk_duration = (time.time() - start_time) * 1000
        
        get_result = self.session_service.get_session(
            app_name="stock_analytics",
            user_id=self._current_user_id,
            session_id=session_id
        )
        if inspect.isawaitable(get_result):
            session = await get_result
        else:
            session = get_result
        
        session_state = dict(session.state) if session else {}
        
        logger.info(f"ADK Runner complete in {adk_duration:.0f}ms")
        logger.info(f"Session state keys: {list(session_state.keys())}")
        
        canonical_data = session_state.get('canonical_data', {})
        ratio_metrics = session_state.get('ratio_metrics', {})
        valuation_metrics = session_state.get('valuation_metrics', {})
        risk_metrics = session_state.get('risk_metrics', {})
        report = session_state.get('presentation_output', {})
        
        if canonical_data.get('status') == 'error':
            raise PipelineExecutionError(f"DataAgent failed: {canonical_data.get('error_message')}")
        
        self.context['canonical_data'] = canonical_data
        self.context['ratio_metrics'] = ratio_metrics
        self.context['valuation_metrics'] = valuation_metrics
        self.context['risk_metrics'] = risk_metrics
        self.context['presentation_output'] = report
        
        self.monitor.end_pipeline("success")
        self.monitor.save_metrics_to_disk(ticker, pipeline_id)
        
        return {
            "status": "success",
            "pipeline_id": pipeline_id,
            "ticker": ticker,
            "meta": canonical_data.get('meta', {}),
            "price_history": canonical_data.get('price_history', []),
            "info": canonical_data.get('info', {}),
            "news": canonical_data.get('news', []),
            "calculated": {
                "profitability": ratio_metrics.get('profitability', {}),
                "liquidity": ratio_metrics.get('liquidity', {}),
                "leverage": ratio_metrics.get('leverage', {}),
                "efficiency": ratio_metrics.get('efficiency', {}),
                "growth": ratio_metrics.get('growth', {}),
                "cashflow": ratio_metrics.get('cashflow', {}),
                "valuation": valuation_metrics.get('metrics', {}),
                "risk_market": risk_metrics.get('market_risk', {}),
                "risk_financial": risk_metrics.get('financial_risk', {}),
            },
            "overall_risk": risk_metrics.get('overall_risk', {}),
            "report": report,
            "timing": {
                "adk_runner_ms": adk_duration,
            },
        }
    
    def get_pipeline(self) -> SequentialAgent:
        """Get the ADK SequentialAgent pipeline."""
        return self.pipeline
    
    def get_parallel_agent(self) -> ParallelAgent:
        """Get the Layer 2 ParallelAgent."""
        return self.layer2_parallel
    
    def get_runner(self) -> Runner:
        """Get the ADK Runner."""
        return self.runner
    
    def get_context(self) -> Dict[str, Any]:
        """Get the current execution context."""
        return self.context.copy()
    
    def clear_context(self):
        """Clear the execution context."""
        self.context.clear()
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        return {
            "pipeline_stats": self.monitor.get_pipeline_summary(),
            "agent_stats": {
                "DataAgent": self.monitor.get_agent_performance("DataAgent"),
                "RatioAgent": self.monitor.get_agent_performance("RatioAgent"),
                "ValuationAgent": self.monitor.get_agent_performance("ValuationAgent"),
                "RiskAnalysisAgent": self.monitor.get_agent_performance("RiskAnalysisAgent"),
                "PresentationAgent": self.monitor.get_agent_performance("PresentationAgent"),
            },
            "mcp_stats": self.mcp_server.get_execution_stats(),
        }


_global_orchestrator: Optional[StockAnalyticsOrchestrator] = None


def run_stock_analysis(ticker: str, period_days: int = 252) -> Dict[str, Any]:
    """Run stock analysis using ADK Runner with deterministic agents."""
    global _global_orchestrator
    
    if _global_orchestrator is None:
        _global_orchestrator = StockAnalyticsOrchestrator()
    
    return _global_orchestrator.analyze_stock(ticker, period_days)


def get_orchestrator() -> StockAnalyticsOrchestrator:
    """Get the global orchestrator instance."""
    global _global_orchestrator
    
    if _global_orchestrator is None:
        _global_orchestrator = StockAnalyticsOrchestrator()
    
    return _global_orchestrator
