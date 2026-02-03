"""
Unit tests for intent parser.
"""
import pytest
from core.parser import parse_message, Intent

class TestParseMessage:
    
    def test_add_task_basic(self):
        result = parse_message("add task Buy groceries")
        assert result.intent == Intent.ADD_TASK
        assert result.params["title"] == "Buy groceries"
    
    def test_add_task_case_insensitive(self):
        result = parse_message("ADD TASK Meeting with team")
        assert result.intent == Intent.ADD_TASK
        assert result.params["title"] == "Meeting with team"
    
    def test_add_task_extra_whitespace(self):
        result = parse_message("  add   task   Clean the house  ")
        assert result.intent == Intent.ADD_TASK
        assert result.params["title"] == "Clean the house"
    
    def test_list_tasks_basic(self):
        result = parse_message("list tasks")
        assert result.intent == Intent.LIST_TASKS
    
    def test_list_tasks_variations(self):
        for cmd in ["List Tasks", "TASKS", "show tasks", "list task"]:
            result = parse_message(cmd)
            assert result.intent == Intent.LIST_TASKS, f"Failed for: {cmd}"
    
    def test_done_task_basic(self):
        result = parse_message("done 5")
        assert result.intent == Intent.DONE_TASK
        assert result.params["task_id"] == 5
    
    def test_done_task_variations(self):
        for cmd, expected_id in [("close 10", 10), ("complete 3", 3), ("DONE 99", 99)]:
            result = parse_message(cmd)
            assert result.intent == Intent.DONE_TASK, f"Failed for: {cmd}"
            assert result.params["task_id"] == expected_id
    
    def test_daily_brief_basic(self):
        result = parse_message("daily brief")
        assert result.intent == Intent.DAILY_BRIEF
    
    def test_daily_brief_variations(self):
        for cmd in ["Daily Brief", "brief", "daily", "morning brief"]:
            result = parse_message(cmd)
            assert result.intent == Intent.DAILY_BRIEF, f"Failed for: {cmd}"
    
    def test_approve_basic(self):
        result = parse_message("approve 42")
        assert result.intent == Intent.APPROVE
        assert result.params["approval_id"] == 42
    
    def test_approve_case_insensitive(self):
        result = parse_message("APPROVE 1")
        assert result.intent == Intent.APPROVE
        assert result.params["approval_id"] == 1
    
    def test_unknown_intent(self):
        result = parse_message("hello world")
        assert result.intent == Intent.UNKNOWN
        assert result.params["text"] == "hello world"
    
    def test_empty_string(self):
        result = parse_message("")
        assert result.intent == Intent.UNKNOWN
    
    def test_whitespace_only(self):
        result = parse_message("   ")
        assert result.intent == Intent.UNKNOWN
