from sqlalchemy import Column, Integer, String, DateTime, Enum, Boolean, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from core.database import Base
import enum

class TaskStatus(str, enum.Enum):
    OPEN = "OPEN"
    DONE = "DONE"

class ApprovalStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class AgentRunStatus(str, enum.Enum):
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_user_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    timezone = Column(String, default="Asia/Makassar")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tasks = relationship("Task", back_populates="user")
    messages = relationship("Message", back_populates="user")
    agent_runs = relationship("AgentRun", back_populates="user")
    approvals = relationship("ApprovalRequest", back_populates="user")
    memories = relationship("Memory", back_populates="user")

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    status = Column(Enum(TaskStatus), default=TaskStatus.OPEN)
    priority = Column(Integer, default=0) # 0=Normal, 1=High
    due_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    done_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="tasks")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    channel = Column(String, default="telegram")
    text = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="messages")

class AgentRun(Base):
    __tablename__ = "agent_runs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    input_text = Column(String, nullable=True)
    intent = Column(String, nullable=True)
    plan_json = Column(JSON, nullable=True)
    result_json = Column(JSON, nullable=True)
    status = Column(Enum(AgentRunStatus), default=AgentRunStatus.RUNNING)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="agent_runs")

class ApprovalRequest(Base):
    __tablename__ = "approval_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action_type = Column(String, nullable=False)
    action_payload_json = Column(JSON, nullable=False)
    status = Column(Enum(ApprovalStatus), default=ApprovalStatus.PENDING)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    decided_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="approvals")

class Memory(Base):
    __tablename__ = "memories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    key = Column(String, index=True, nullable=False)
    value_json = Column(JSON, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="memories")

# Deprecated/Legacy compatibility if needed (can remove if we migrate cleanly)
class ActivityLog(Base):
    __tablename__ = "activity_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False) 
    command = Column(String, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
