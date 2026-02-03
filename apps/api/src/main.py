from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from core.database import get_db
from core.models import Task, TaskStatus
from core.schemas import TaskRead
from core.db import crud
from core.agent import run_agent_loop
from core.logging_config import setup_logging, set_request_id, get_logger
from core.rate_limiter import message_rate_limiter
from core.safety import validate_input, MAX_STEPS_PER_RUN
from core.metrics import metrics, METRIC_REQUESTS_TOTAL, METRIC_REQUESTS_SUCCESS, METRIC_REQUESTS_FAILED, METRIC_RATE_LIMITED
from typing import List
from pydantic import BaseModel
import time
import uuid

# Setup structured logging
setup_logging(json_format=True)
logger = get_logger(__name__)

app = FastAPI(title="Agent API")

class MessagePayload(BaseModel):
    telegram_user_id: str
    text: str
    message_id: int | None = None
    chat_id: int | None = None

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add request ID to all requests."""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
    set_request_id(request_id)
    
    start_time = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start_time) * 1000
    
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
    
    logger.info(f"{request.method} {request.url.path} - {response.status_code} ({duration_ms:.2f}ms)")
    return response

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "agent-api", "version": "0.1.0"}

@app.get("/metrics")
def get_metrics():
    """Basic metrics endpoint."""
    return metrics.get_all()

@app.post("/v1/message")
async def handle_message(payload: MessagePayload, db: Session = Depends(get_db)):
    """Receive message from bot, run agent loop, return response."""
    request_id = set_request_id()
    metrics.increment(METRIC_REQUESTS_TOTAL)
    
    telegram_user_id = payload.telegram_user_id
    text = payload.text
    
    logger.info(f"Received message from {telegram_user_id}: {text[:50]}...")
    
    # Rate limiting
    allowed, remaining = message_rate_limiter.is_allowed(telegram_user_id)
    if not allowed:
        metrics.increment(METRIC_RATE_LIMITED)
        retry_after = message_rate_limiter.get_retry_after(telegram_user_id)
        return JSONResponse(
            status_code=429,
            content={"error": "Rate limited", "retry_after": retry_after},
            headers={"Retry-After": str(retry_after)}
        )
    
    # Input validation
    valid, error_msg = validate_input(text)
    if not valid:
        metrics.increment(METRIC_REQUESTS_FAILED)
        return JSONResponse(status_code=400, content={"error": error_msg})
    
    # Ensure user exists
    user = crud.get_or_create_user(db, telegram_user_id)
    
    # Log the incoming message
    crud.log_message(db, user.id, text, "telegram")
    
    # Run agent loop
    try:
        result = run_agent_loop(text, user.id, db)
        metrics.increment(METRIC_REQUESTS_SUCCESS)
    except Exception as e:
        metrics.increment(METRIC_REQUESTS_FAILED)
        logger.error(f"Agent loop error: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"error": "Internal error", "request_id": request_id})
    
    response_text = result.get("response", "")
    run_id = result.get("run_id")
    
    # Log agent response
    crud.log_message(db, user.id, response_text, "agent")
    
    return {"response": response_text, "run_id": run_id, "request_id": request_id}

@app.get("/tasks", response_model=List[TaskRead])
def get_tasks(status: TaskStatus = None, db: Session = Depends(get_db)):
    query = db.query(Task)
    if status:
        query = query.filter(Task.status == status)
    return query.all()
