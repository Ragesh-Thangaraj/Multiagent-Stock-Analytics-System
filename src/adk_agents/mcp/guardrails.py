"""
Guardrails for ADK Agent Security

This module provides security policies and guardrails for agent operations,
including input validation, output filtering, and execution constraints.
"""

import logging
import re
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk levels for operations."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SecurityPolicy:
    """
    Security policy configuration for agent operations.
    """
    max_api_calls_per_minute: int = 60
    max_calculation_timeout_seconds: float = 30.0
    allowed_tickers_pattern: str = r'^[A-Z]{1,5}$'
    blocked_tickers: List[str] = field(default_factory=list)
    max_price_history_days: int = 365
    require_valid_fundamentals: bool = True
    max_output_size_bytes: int = 10 * 1024 * 1024  # 10MB
    enable_rate_limiting: bool = True
    log_all_operations: bool = True
    
    def validate_ticker(self, ticker: str) -> bool:
        """Validate a stock ticker against the policy."""
        if not ticker:
            return False
        
        ticker = ticker.upper().strip()
        
        if ticker in self.blocked_tickers:
            logger.warning(f"Blocked ticker attempted: {ticker}")
            return False
        
        if not re.match(self.allowed_tickers_pattern, ticker):
            logger.warning(f"Invalid ticker format: {ticker}")
            return False
        
        return True
    
    def validate_period(self, days: int) -> int:
        """Validate and constrain the analysis period."""
        if days < 1:
            return 30
        if days > self.max_price_history_days:
            logger.warning(f"Period {days} exceeds max, capping to {self.max_price_history_days}")
            return self.max_price_history_days
        return days


class Guardrails:
    """
    Guardrails system for ADK agents.
    Provides security checks, input validation, and output filtering.
    """
    
    def __init__(self, policy: Optional[SecurityPolicy] = None):
        """
        Initialize the Guardrails system.
        
        Args:
            policy: Security policy configuration
        """
        self.policy = policy or SecurityPolicy()
        self.api_call_counts: Dict[str, int] = {}
        self.validators: List[Callable] = []
        self.filters: List[Callable] = []
        
        self._register_default_validators()
        self._register_default_filters()
    
    def _register_default_validators(self):
        """Register default input validators."""
        
        def validate_ticker_input(data: Dict[str, Any]) -> bool:
            ticker = data.get('ticker')
            if ticker:
                return self.policy.validate_ticker(ticker)
            return True
        
        def validate_numeric_bounds(data: Dict[str, Any]) -> bool:
            for key, value in data.items():
                if isinstance(value, (int, float)):
                    if abs(value) > 1e15:
                        logger.warning(f"Numeric value out of bounds: {key}={value}")
                        return False
            return True
        
        self.validators.append(validate_ticker_input)
        self.validators.append(validate_numeric_bounds)
    
    def _register_default_filters(self):
        """Register default output filters."""
        
        def filter_sensitive_data(output: Dict[str, Any]) -> Dict[str, Any]:
            sensitive_keys = ['api_key', 'secret', 'password', 'token', 'credential']
            
            def filter_dict(d: Dict) -> Dict:
                filtered = {}
                for key, value in d.items():
                    if any(s in key.lower() for s in sensitive_keys):
                        filtered[key] = "[REDACTED]"
                    elif isinstance(value, dict):
                        filtered[key] = filter_dict(value)
                    else:
                        filtered[key] = value
                return filtered
            
            return filter_dict(output)
        
        def limit_output_size(output: Dict[str, Any]) -> Dict[str, Any]:
            import json
            output_size = len(json.dumps(output))
            
            if output_size > self.policy.max_output_size_bytes:
                logger.warning(f"Output size {output_size} exceeds limit")
                return {
                    "error": "Output size exceeded",
                    "max_size": self.policy.max_output_size_bytes,
                }
            
            return output
        
        self.filters.append(filter_sensitive_data)
        self.filters.append(limit_output_size)
    
    def validate_input(self, data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate input data against all registered validators.
        
        Args:
            data: Input data to validate
            
        Returns:
            tuple: (is_valid, error_message)
        """
        for validator in self.validators:
            try:
                if not validator(data):
                    return False, f"Validation failed: {validator.__name__}"
            except Exception as e:
                logger.error(f"Validator error: {e}")
                return False, f"Validation error: {str(e)}"
        
        return True, None
    
    def filter_output(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply all output filters to the data.
        
        Args:
            output: Output data to filter
            
        Returns:
            dict: Filtered output data
        """
        filtered = output
        
        for filter_func in self.filters:
            try:
                filtered = filter_func(filtered)
            except Exception as e:
                logger.error(f"Filter error: {e}")
        
        return filtered
    
    def check_rate_limit(self, operation: str) -> bool:
        """
        Check if an operation is within rate limits.
        
        Args:
            operation: The operation identifier
            
        Returns:
            bool: True if within limits, False otherwise
        """
        if not self.policy.enable_rate_limiting:
            return True
        
        current_count = self.api_call_counts.get(operation, 0)
        
        if current_count >= self.policy.max_api_calls_per_minute:
            logger.warning(f"Rate limit exceeded for {operation}")
            return False
        
        self.api_call_counts[operation] = current_count + 1
        return True
    
    def reset_rate_limits(self):
        """Reset all rate limit counters."""
        self.api_call_counts.clear()
    
    def assess_risk(self, operation: str, data: Dict[str, Any]) -> RiskLevel:
        """
        Assess the risk level of an operation.
        
        Args:
            operation: The operation type
            data: Associated data
            
        Returns:
            RiskLevel: The assessed risk level
        """
        if operation in ['delete', 'modify', 'execute']:
            return RiskLevel.HIGH
        
        if 'external_api' in operation:
            return RiskLevel.MEDIUM
        
        if 'calculation' in operation:
            return RiskLevel.LOW
        
        return RiskLevel.LOW
    
    def add_validator(self, validator: Callable[[Dict[str, Any]], bool]):
        """Add a custom input validator."""
        self.validators.append(validator)
    
    def add_filter(self, filter_func: Callable[[Dict[str, Any]], Dict[str, Any]]):
        """Add a custom output filter."""
        self.filters.append(filter_func)
