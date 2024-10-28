from typing import Dict, Optional
import time
from fastapi import HTTPException

class RateLimiter:
    def __init__(self):
        self.requests: Dict[str, list] = {}
        self.window_size = 60  # 60 seconds
        
    def check_rate_limit(self, key: str, max_requests: int) -> bool:
        current_time = time.time()
        
        if key not in self.requests:
            self.requests[key] = []
            
        # Remove old requests
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if current_time - req_time < self.window_size
        ]
        
        # Check if rate limit is exceeded
        if len(self.requests[key]) >= max_requests:
            return False
            
        # Add new request
        self.requests[key].append(current_time)
        return True