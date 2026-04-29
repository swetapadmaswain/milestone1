import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from threading import Lock
from typing import Dict, List, Any

from app.models.schemas import MetricsResponse


class MetricsService:
    """Service for collecting and managing application metrics."""
    
    def __init__(self):
        self.counters = defaultdict(int)
        self.gauges = defaultdict(float)
        self.timers = defaultdict(lambda: deque(maxlen=1000))  # Keep last 1000 measurements
        self.lock = Lock()
        self.start_time = time.time()
    
    def increment_counter(self, key: str, value: int = 1) -> None:
        """Increment a counter metric."""
        with self.lock:
            self.counters[key] += value
    
    def set_gauge(self, key: str, value: float) -> None:
        """Set a gauge metric value."""
        with self.lock:
            self.gauges[key] = value
    
    def observe_latency(self, key: str, latency_ms: float) -> None:
        """Record a latency measurement."""
        with self.lock:
            self.timers[key].append(latency_ms)
    
    def get_timer_stats(self, key: str) -> Dict[str, float]:
        """Get statistics for a timer."""
        with self.lock:
            values = list(self.timers[key])
            if not values:
                return {"count": 0, "min": 0.0, "max": 0.0, "mean": 0.0, "p50": 0.0, "p95": 0.0, "p99": 0.0}
            
            sorted_values = sorted(values)
            count = len(sorted_values)
            
            return {
                "count": count,
                "min": sorted_values[0],
                "max": sorted_values[-1],
                "mean": sum(sorted_values) / count,
                "p50": sorted_values[int(count * 0.5)],
                "p95": sorted_values[int(count * 0.95)],
                "p99": sorted_values[int(count * 0.99)],
            }
    
    def get_metrics(self) -> MetricsResponse:
        """Get all current metrics."""
        with self.lock:
            # Process timers to get statistics
            timer_stats = {}
            for key in self.timers:
                timer_stats[key] = self.get_timer_stats(key)
            
            return MetricsResponse(
                counters=dict(self.counters),
                gauges=dict(self.gauges),
                timers=timer_stats,
                timestamp=datetime.now(timezone.utc),
            )
    
    def reset_metrics(self) -> None:
        """Reset all metrics (useful for testing)."""
        with self.lock:
            self.counters.clear()
            self.gauges.clear()
            self.timers.clear()
    
    def get_uptime_seconds(self) -> float:
        """Get application uptime in seconds."""
        return time.time() - self.start_time
    
    def get_health_metrics(self) -> Dict[str, Any]:
        """Get health-related metrics."""
        metrics = self.get_metrics()
        uptime = self.get_uptime_seconds()
        
        return {
            "uptime_seconds": uptime,
            "total_requests": sum(metrics.counters.get(key, 0) for key in metrics.counters if key.startswith("http.")),
            "error_rate": self._calculate_error_rate(metrics.counters),
            "avg_response_time": self._calculate_avg_response_time(metrics.timers),
            "cache_hit_rate": self._calculate_cache_hit_rate(metrics.counters),
        }
    
    def _calculate_error_rate(self, counters: Dict[str, int]) -> float:
        """Calculate error rate from counters."""
        total_requests = sum(counters.get(key, 0) for key in counters if key.startswith("http."))
        total_errors = sum(counters.get(key, 0) for key in counters if key.startswith("errors."))
        
        if total_requests == 0:
            return 0.0
        
        return (total_errors / total_requests) * 100
    
    def _calculate_avg_response_time(self, timers: Dict[str, List[float]]) -> float:
        """Calculate average response time from timers."""
        http_timers = {key: values for key, values in timers.items() if key.startswith("http.")}
        
        if not http_timers:
            return 0.0
        
        all_times = []
        for values in http_timers.values():
            all_times.extend(values)
        
        if not all_times:
            return 0.0
        
        return sum(all_times) / len(all_times)
    
    def _calculate_cache_hit_rate(self, counters: Dict[str, int]) -> float:
        """Calculate cache hit rate from counters."""
        hits = counters.get("cache.hit", 0)
        misses = counters.get("cache.miss", 0)
        
        total = hits + misses
        if total == 0:
            return 0.0
        
        return (hits / total) * 100


class PrometheusMetricsExporter:
    """Export metrics in Prometheus format."""
    
    def __init__(self, metrics_service: MetricsService):
        self.metrics_service = metrics_service
    
    def export_metrics(self) -> str:
        """Export metrics in Prometheus format."""
        metrics = self.metrics_service.get_metrics()
        lines = []
        
        # Export counters
        for key, value in metrics.counters.items():
            safe_key = self._sanitize_metric_name(key)
            lines.append(f"# TYPE {safe_key} counter")
            lines.append(f"{safe_key} {value}")
        
        # Export gauges
        for key, value in metrics.gauges.items():
            safe_key = self._sanitize_metric_name(key)
            lines.append(f"# TYPE {safe_key} gauge")
            lines.append(f"{safe_key} {value}")
        
        # Export timer stats
        for key, stats in metrics.timers.items():
            safe_key = self._sanitize_metric_name(key)
            lines.append(f"# TYPE {safe_key}_seconds histogram")
            lines.append(f"{safe_key}_seconds_count {stats['count']}")
            lines.append(f"{safe_key}_seconds_sum {stats['mean'] * stats['count']}")
        
        return "\n".join(lines)
    
    def _sanitize_metric_name(self, name: str) -> str:
        """Sanitize metric name for Prometheus."""
        # Replace dots and special characters with underscores
        import re
        return re.sub(r'[^a-zA-Z0-9_]', '_', name)


class HealthChecker:
    """Service for checking application health."""
    
    def __init__(self, metrics_service: MetricsService):
        self.metrics_service = metrics_service
    
    async def check_database_health(self) -> bool:
        """Check database connectivity."""
        try:
            # This would implement actual database health check
            # For now, return True as placeholder
            return True
        except Exception:
            return False
    
    async def check_llm_health(self) -> bool:
        """Check LLM service connectivity."""
        try:
            # This would implement actual LLM service health check
            # For now, return True if API key is configured
            from app.core.config import settings
            return bool(settings.GROQ_API_KEY)
        except Exception:
            return False
    
    async def check_cache_health(self) -> bool:
        """Check cache service health."""
        try:
            # This would implement actual cache health check
            # For now, return True as placeholder
            return True
        except Exception:
            return False
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status."""
        health_metrics = self.metrics_service.get_health_metrics()
        
        checks = {
            "database": await self.check_database_health(),
            "llm_service": await self.check_llm_health(),
            "cache": await self.check_cache_health(),
        }
        
        overall_status = "healthy" if all(checks.values()) else "unhealthy"
        
        return {
            "status": overall_status,
            "uptime_seconds": health_metrics["uptime_seconds"],
            "checks": checks,
            "metrics": health_metrics,
        }
