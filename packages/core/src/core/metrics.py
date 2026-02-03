"""
Metrics - Basic metrics collection for /metrics endpoint.
"""
from datetime import datetime
from typing import Dict, Any
import threading

class Metrics:
    """Simple metrics collector."""
    
    def __init__(self):
        self._lock = threading.Lock()
        self._counters: Dict[str, int] = {}
        self._gauges: Dict[str, float] = {}
        self._start_time = datetime.utcnow()
    
    def increment(self, name: str, value: int = 1):
        """Increment a counter."""
        with self._lock:
            self._counters[name] = self._counters.get(name, 0) + value
    
    def set_gauge(self, name: str, value: float):
        """Set a gauge value."""
        with self._lock:
            self._gauges[name] = value
    
    def get_all(self) -> Dict[str, Any]:
        """Get all metrics."""
        with self._lock:
            uptime = (datetime.utcnow() - self._start_time).total_seconds()
            return {
                "uptime_seconds": uptime,
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
            }

# Global metrics instance
metrics = Metrics()

# Pre-defined metric names
METRIC_REQUESTS_TOTAL = "requests_total"
METRIC_REQUESTS_SUCCESS = "requests_success"
METRIC_REQUESTS_FAILED = "requests_failed"
METRIC_RATE_LIMITED = "rate_limited_total"
METRIC_AGENT_RUNS = "agent_runs_total"
METRIC_LLM_CALLS = "llm_calls_total"
METRIC_DB_QUERIES = "db_queries_total"
