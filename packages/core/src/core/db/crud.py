from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from core.models import User, Task, TaskStatus, Message, AgentRun, AgentRunStatus, ApprovalRequest, ApprovalStatus, Memory
import json

# User
def get_or_create_user(db: Session, telegram_id: str, name: str = None) -> User:
    user = db.query(User).filter(User.telegram_user_id == str(telegram_id)).first()
    if not user:
        user = User(telegram_user_id=str(telegram_id), name=name)
        db.add(user)
        db.commit()
        db.refresh(user)
    elif name and user.name != name:
        user.name = name
        db.commit()
        db.refresh(user)
    return user

# Task
def create_task(db: Session, user_id: int, title: str, priority: int = 0) -> Task:
    task = Task(user_id=user_id, title=title, priority=priority)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

def close_task(db: Session, task_id: int) -> Task | None:
    task = db.query(Task).filter(Task.id == task_id).first()
    if task:
        task.status = TaskStatus.DONE
        task.done_at = func.now()
        db.commit()
        db.refresh(task)
    return task

def list_open_tasks(db: Session, user_id: int):
    return db.query(Task).filter(Task.user_id == user_id, Task.status == TaskStatus.OPEN).all()

# Message
def log_message(db: Session, user_id: int, text: str, channel: str = "telegram") -> Message:
    msg = Message(user_id=user_id, text=text, channel=channel)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg

# Agent Run
def create_agent_run(db: Session, user_id: int, input_text: str, intent: str = None) -> AgentRun:
    run = AgentRun(user_id=user_id, input_text=input_text, intent=intent, status=AgentRunStatus.RUNNING)
    db.add(run)
    db.commit()
    db.refresh(run)
    return run

def update_agent_run(db: Session, run_id: int, status: AgentRunStatus, result: dict = None, plan: dict = None):
    run = db.query(AgentRun).filter(AgentRun.id == run_id).first()
    if run:
        run.status = status
        if result:
            run.result_json = result
        if plan:
            run.plan_json = plan
        db.commit()
        db.refresh(run)
    return run

# Approval
def create_approval_request(db: Session, user_id: int, action_type: str, payload: dict) -> ApprovalRequest:
    req = ApprovalRequest(
        user_id=user_id, 
        action_type=action_type, 
        action_payload_json=payload,
        status=ApprovalStatus.PENDING
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req

def update_approval_status(db: Session, req_id: int, status: ApprovalStatus) -> ApprovalRequest | None:
    req = db.query(ApprovalRequest).filter(ApprovalRequest.id == req_id).first()
    if req:
        req.status = status
        req.decided_at = func.now()
        db.commit()
        db.refresh(req)
    return req

# Memory
def set_memory(db: Session, user_id: int, key: str, value: dict) -> Memory:
    mem = db.query(Memory).filter(Memory.user_id == user_id, Memory.key == key).first()
    if not mem:
        mem = Memory(user_id=user_id, key=key, value_json=value)
        db.add(mem)
    else:
        mem.value_json = value
    
    db.commit()
    db.refresh(mem)
    return mem

def get_memory(db: Session, user_id: int, key: str) -> dict | None:
    mem = db.query(Memory).filter(Memory.user_id == user_id, Memory.key == key).first()
    return mem.value_json if mem else None
