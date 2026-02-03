"""
Rate Limiter - Simple in-memory rate limiting for message spam protection.
"""
from datetime import datetime, timedelta
from typing import Dict, Tuple
import threading

class RateLimiter:
    """Simple token bucket rate limiter."""
    
    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._buckets: Dict[str, list] = {}
        self._lock = threading.Lock()
    
    def is_allowed(self, user_id: str) -> Tuple[bool, int]:
        """
        Check if request is allowed for user.
        Returns (allowed, remaining_requests).
        """
        with self._lock:
            now = datetime.utcnow()
            cutoff = now - timedelta(seconds=self.window_seconds)
            
            if user_id not in self._buckets:
                self._buckets[user_id] = []
            
            # Remove old requests
            self._buckets[user_id] = [t for t in self._buckets[user_id] if t > cutoff]
            
            current_count = len(self._buckets[user_id])
            remaining = max(0, self.max_requests - current_count)
            
            if current_count >= self.max_requests:
                return False, 0
            
            # Record this request
            self._buckets[user_id].append(now)
            return True, remaining - 1
    
    def get_retry_after(self, user_id: str) -> int:
        """Get seconds until next request is allowed."""
        with self._lock:
            if user_id not in self._buckets or not self._buckets[user_id]:
                return 0
            
            oldest = min(self._buckets[user_id])
            retry_after = (oldest + timedelta(seconds=self.window_seconds) - datetime.utcnow()).total_seconds()
            return max(0, int(retry_after))

# Global rate limiter instance
message_rate_limiter = RateLimiter(max_requests=20, window_seconds=60)
