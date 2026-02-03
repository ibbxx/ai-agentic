from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from core.models import Task, TaskStatus
from core.schemas import TaskRead
from core.db import crud
from core.agent import run_agent_loop
from typing import List
from pydantic import BaseModel
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Agent API")

class MessagePayload(BaseModel):
    telegram_user_id: str
    text: str
    message_id: int | None = None
    chat_id: int | None = None

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/v1/message")
async def handle_message(payload: MessagePayload, db: Session = Depends(get_db)):
    """
    Receive message from bot, run agent loop, return response.
    """
    telegram_user_id = payload.telegram_user_id
    text = payload.text
    
    logger.info(f"Received message from {telegram_user_id}: {text}")
    
    # Ensure user exists
    user = crud.get_or_create_user(db, telegram_user_id)
    
    # Log the incoming message
    crud.log_message(db, user.id, text, "telegram")
    
    # Run agent loop
    result = run_agent_loop(text, user.id, db)
    
    response_text = result.get("response", "")
    run_id = result.get("run_id")
    
    # Log agent response
    crud.log_message(db, user.id, response_text, "agent")
    
    return {"response": response_text, "run_id": run_id}

@app.get("/tasks", response_model=List[TaskRead])
def get_tasks(status: TaskStatus = None, db: Session = Depends(get_db)):
    query = db.query(Task)
    if status:
        query = query.filter(Task.status == status)
    return query.all()
