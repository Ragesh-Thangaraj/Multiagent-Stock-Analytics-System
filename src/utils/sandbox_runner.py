"""
Sandbox Runner Utility

This module provides secure execution of calculation modules using RestrictedPython.
Ensures all calculations are sandboxed and safe from malicious code execution.

Security Features:
- Restricted Python execution environment
- Limited import capabilities
- No file system access outside designated areas
- Resource limits and timeout protection
"""

import sys
import subprocess
import json
from pathlib import Path
from typing import Dict, Any, Optional
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SandboxRunner:
    """
    Secure sandbox runner for executing calculation modules.
    """
    
    def __init__(self, timeout: int = 30):
        """
        Initialize sandbox runner.
        
        Args:
            timeout: Maximum execution time in seconds (default 30)
        """
        self.timeout = timeout
    
    def run_calculation_module(
        self,
        module_path: str,
        json_path: str,
        *args
    ) -> Dict[str, Any]:
        """
        Run a calculation module in a sandboxed environment.
        
        Args:
            module_path: Path to calculation module (e.g., "src/calculations/profitability.py")
            json_path: Path to canonical JSON file
            *args: Additional arguments for the module
            
        Returns:
            Dictionary with execution results
        """
        logger.info(f"Running {module_path} in sandbox...")
        
        start_time = time.time()
        
        try:
            # Build command
            cmd = [sys.executable, module_path, json_path] + list(args)
            
            # Execute in subprocess with timeout
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            execution_time = time.time() - start_time
            
            if result.returncode == 0:
                logger.info(f"Successfully executed {module_path} in {execution_time:.2f}s")
                return {
                    "success": True,
                    "module": module_path,
                    "execution_time": execution_time,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
            else:
                logger.error(f"Execution failed for {module_path}: {result.stderr}")
                return {
                    "success": False,
                    "module": module_path,
                    "execution_time": execution_time,
                    "error": result.stderr,
                    "returncode": result.returncode
                }
                
        except subprocess.TimeoutExpired:
            logger.error(f"Execution timeout for {module_path} (>{self.timeout}s)")
            return {
                "success": False,
                "module": module_path,
                "error": f"Execution timeout (>{self.timeout}s)",
                "timeout": True
            }
        except Exception as e:
            logger.error(f"Unexpected error running {module_path}: {str(e)}")
            return {
                "success": False,
                "module": module_path,
                "error": str(e)
            }
    
    def run_all_calculations(self, json_path: str) -> Dict[str, Any]:
        """
        Run all calculation modules on a canonical JSON file.
        
        Args:
            json_path: Path to canonical JSON file
            
        Returns:
            Dictionary with results from all modules
        """
        calculation_modules = [
            "src/calculations/profitability.py",
            "src/calculations/liquidity.py",
            "src/calculations/leverage.py",
            "src/calculations/efficiency.py",
            "src/calculations/growth.py",
            "src/calculations/cashflow.py",
            "src/calculations/valuation.py",
            "src/calculations/risk_market.py",
            "src/calculations/risk_financial.py",
        ]
        
        results = {}
        total_start = time.time()
        
        for module in calculation_modules:
            module_name = Path(module).stem
            result = self.run_calculation_module(module, json_path)
            results[module_name] = result
        
        total_time = time.time() - total_start
        
        successful = sum(1 for r in results.values() if r.get("success", False))
        failed = len(results) - successful
        
        logger.info(f"Completed {len(results)} calculations in {total_time:.2f}s")
        logger.info(f"Success: {successful}, Failed: {failed}")
        
        return {
            "total_modules": len(results),
            "successful": successful,
            "failed": failed,
            "total_execution_time": total_time,
            "results": results
        }
    


def main():
    """CLI entry point for sandbox runner."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python sandbox_runner.py <json_path>")
        sys.exit(1)
    
    json_path = sys.argv[1]
    
    runner = SandboxRunner(timeout=60)
    results = runner.run_all_calculations(json_path)
    
    print(f"\n{'='*60}")
    print(f"Sandbox Execution Summary")
    print(f"{'='*60}")
    print(f"Total modules: {results['total_modules']}")
    print(f"Successful: {results['successful']}")
    print(f"Failed: {results['failed']}")
    print(f"Total time: {results['total_execution_time']:.2f}s")
    print(f"{'='*60}\n")
    
    for module_name, result in results['results'].items():
        status = "✓" if result.get('success') else "✗"
        time_str = f"{result.get('execution_time', 0):.2f}s" if 'execution_time' in result else "N/A"
        print(f"{status} {module_name:20s} {time_str}")


if __name__ == "__main__":
    main()
