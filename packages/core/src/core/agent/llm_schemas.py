"""
LLM Schemas - Pydantic models for structured LLM output.
"""
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from enum import Enum

# Allowlist of tools the LLM can reference
ALLOWED_TOOLS = [
    "task_tool", "scheduler_tool", "approval_tool", 
    "preference_tool", "proposal_tool",
    "shell_tool", "file_tool", "app_tool"
]

# Blocked patterns (dangerous operations)
BLOCKED_PATTERNS = [
    "rm -rf /", "rm -rf ~", "sudo rm", "mkfs", "dd if=",
    ":(){ :|:", "> /dev/sda", "chmod -R 777 /",
    "DROP TABLE", "DELETE FROM", "<script>", "javascript:",
]

class LLMIntent(str, Enum):
    ADD_TASK = "add_task"
    LIST_TASKS = "list_tasks"
    DONE_TASK = "done_task"
    DELETE_TASK = "delete_task"
    DAILY_BRIEF = "daily_brief"
    APPROVE = "approve"
    # Computer use intents
    RUN_COMMAND = "run_command"
    READ_FILE = "read_file"
    WRITE_FILE = "write_file"
    LIST_FILES = "list_files"
    OPEN_APP = "open_app"
    CLOSE_APP = "close_app"
    SCREENSHOT = "screenshot"
    UNKNOWN = "unknown"

class PlanStep(BaseModel):
    tool: str = Field(..., description="Tool to use")
    action: str = Field(..., description="Action to perform")
    params: Dict[str, Any] = Field(default_factory=dict, description="Parameters for the action")
    
    @field_validator('tool')
    @classmethod
    def validate_tool(cls, v):
        if v not in ALLOWED_TOOLS:
            raise ValueError(f"Tool '{v}' not allowed. Must be one of: {ALLOWED_TOOLS}")
        return v
    
    @field_validator('params')
    @classmethod
    def validate_params(cls, v):
        def check_value(val):
            if isinstance(val, str):
                for pattern in BLOCKED_PATTERNS:
                    if pattern in val:
                        raise ValueError(f"Blocked pattern in params: {pattern}")
            elif isinstance(val, dict):
                for inner_v in val.values():
                    check_value(inner_v)
            elif isinstance(val, list):
                for item in val:
                    check_value(item)
        check_value(v)
        return v

class LLMResponse(BaseModel):
    intent: LLMIntent = Field(..., description="Detected intent from user message")
    entities: Dict[str, Any] = Field(default_factory=dict, description="Extracted entities")
    plan_steps: List[PlanStep] = Field(default_factory=list, description="Steps to execute")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="Confidence score 0-1")
    
    @field_validator('plan_steps')
    @classmethod
    def validate_steps(cls, v):
        if len(v) > 5:
            raise ValueError("Too many plan steps. Maximum 5 allowed.")
        return v
