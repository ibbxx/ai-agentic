"""
Logging Configuration - Structured JSON logging with request ID tracing.
"""
import logging
import json
import uuid
from datetime import datetime
from contextvars import ContextVar
from typing import Optional

# Context variable for request ID
request_id_var: ContextVar[str] = ContextVar('request_id', default='')

def get_request_id() -> str:
    """Get current request ID from context."""
    return request_id_var.get() or str(uuid.uuid4())[:8]

def set_request_id(request_id: str = None) -> str:
    """Set request ID in context. Generates new one if not provided."""
    rid = request_id or str(uuid.uuid4())[:8]
    request_id_var.set(rid)
    return rid

class JSONFormatter(logging.Formatter):
    """Structured JSON log formatter."""
    
    def format(self, record):
        log_record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": get_request_id(),
        }
        
        # Add extra fields
        if hasattr(record, 'user_id'):
            log_record["user_id"] = record.user_id
        if hasattr(record, 'intent'):
            log_record["intent"] = record.intent
        if hasattr(record, 'duration_ms'):
            log_record["duration_ms"] = record.duration_ms
        
        # Add exception info
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_record)

def setup_logging(json_format: bool = True, level: int = logging.INFO):
    """Setup logging with optional JSON format."""
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    
    if json_format:
        console_handler.setFormatter(JSONFormatter())
    else:
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s [%(request_id)s] %(levelname)s %(name)s: %(message)s',
            defaults={'request_id': get_request_id}
        ))
    
    root_logger.addHandler(console_handler)
    return root_logger

class LoggerAdapter(logging.LoggerAdapter):
    """Logger adapter that includes request ID."""
    
    def process(self, msg, kwargs):
        kwargs.setdefault('extra', {})
        kwargs['extra']['request_id'] = get_request_id()
        return msg, kwargs

def get_logger(name: str) -> LoggerAdapter:
    """Get a logger with request ID support."""
    return LoggerAdapter(logging.getLogger(name), {})
