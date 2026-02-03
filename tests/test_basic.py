import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.database import Base
from core.models import Task, TaskStatus, ApprovalRequest, ApprovalStatus, User, Message, AgentRun
from core.db import crud
from unittest.mock import MagicMock

# Setup in-memory DB for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

def test_get_or_create_user(db):
    user = crud.get_or_create_user(db, "123", "Test User")
    assert user.id is not None
    assert user.telegram_user_id == "123"
    assert user.name == "Test User"
    
    # Test idempotent
    user2 = crud.get_or_create_user(db, "123", "New Name")
    assert user2.id == user.id
    assert user2.name == "New Name"

def test_create_task_linked_to_user(db):
    user = crud.get_or_create_user(db, "123")
    task = crud.create_task(db, user.id, "Buying milk", priority=1)
    
    assert task.user_id == user.id
    assert task.title == "Buying milk"
    assert task.priority == 1
    assert task.status == TaskStatus.OPEN

def test_log_message_and_relationships(db):
    user = crud.get_or_create_user(db, "999")
    msg = crud.log_message(db, user.id, "Hello bot")
    
    assert msg.user_id == user.id
    assert msg.text == "Hello bot"
    
    # Check relationship
    assert len(user.messages) == 1
    assert user.messages[0].text == "Hello bot"

def test_agent_run_lifecycle(db):
    user = crud.get_or_create_user(db, "888")
    run = crud.create_agent_run(db, user.id, "Help me", "help")
    
    assert run.status == "RUNNING"
    
    run = crud.update_agent_run(db, run.id, "COMPLETED", result={"text": "Done"})
    assert run.status == "COMPLETED"
    assert run.result_json == {"text": "Done"}

def test_approval_flow(db):
    user = crud.get_or_create_user(db, "777")
    req = crud.create_approval_request(db, user.id, "nuke", {"target": "all"})
    
    assert req.status == ApprovalStatus.PENDING
    
    updated = crud.update_approval_status(db, req.id, ApprovalStatus.REJECTED)
    assert updated.status == ApprovalStatus.REJECTED
    assert updated.decided_at is not None

def test_memory(db):
    user = crud.get_or_create_user(db, "666")
    crud.set_memory(db, user.id, "hobby", {"value": "coding"})
    
    val = crud.get_memory(db, user.id, "hobby")
    assert val == {"value": "coding"}
    
    # Update
    crud.set_memory(db, user.id, "hobby", {"value": "sleeping"})
    val = crud.get_memory(db, user.id, "hobby")
    assert val == {"value": "sleeping"}
