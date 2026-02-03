# Safety.md - Guardrails and Safety Measures

This document outlines all safety measures implemented in the Telegram Agent Bot.

## 1. Tool Allowlist

Only approved tools can be executed:
- `task_tool` - Task CRUD operations
- `scheduler_tool` - Daily brief
- `approval_tool` - Approval management
- `preference_tool` - User preferences
- `proposal_tool` - Improvement proposals

**No shell commands, file system access, or network requests are allowed.**

## 2. High-Risk Action Gate

Dangerous actions require explicit user approval:

| Tool | Risky Actions |
|------|---------------|
| task_tool | delete, delete_all, purge |
| file_tool | delete, move, overwrite |
| email_tool | send, send_bulk |
| external_tool | webhook, http_request |

**Flow:**
1. User requests risky action
2. System creates pending approval
3. User must type `APPROVE <id>` to execute
4. Only the same user can approve their own requests

## 3. Execution Limits

| Limit | Value | Purpose |
|-------|-------|---------|
| Max Steps | 6 | Prevent runaway loops |
| Tool Timeout | 30s | Prevent hanging |
| LLM Tokens | 500 | Cost control |
| Plan Depth | 3 | Prevent recursion |

## 4. Rate Limiting

| Limit | Value |
|-------|-------|
| Requests | 20 per user |
| Window | 60 seconds |

Returns `429 Too Many Requests` with `Retry-After` header.

## 5. Input Validation

Blocked patterns in user input:
- `sudo`, `rm -rf`, `DROP TABLE`, `DELETE FROM`
- `<script>`, `javascript:`, `eval(`, `exec(`

Message length limit: 4000 characters.

## 6. LLM Safety

When using LLM fallback:
- Output schema enforced via Pydantic
- Only allowed tools can be referenced
- Shell/system commands blocked
- URLs and file paths blocked in output
- Low temperature (0.1) for determinism

## 7. Proposal System Safety

- Proposals require explicit approval
- Rules are deterministic (pattern → action)
- Rollback available for approved proposals
- User can only approve/rollback their own proposals

## 8. Logging & Tracing

- All requests have unique Request ID
- Structured JSON logging
- Agent runs persisted to database
- Reflections logged for auditing

## 9. Configuration

All safety limits configurable via `core/safety.py`:

```python
MAX_STEPS_PER_RUN = 6
TOOL_TIMEOUT_SECONDS = 30
MAX_LLM_TOKENS = 500
MAX_PLAN_DEPTH = 3
RATE_LIMIT_REQUESTS = 20
RATE_LIMIT_WINDOW = 60
```

## 10. Endpoints

| Endpoint | Purpose |
|----------|---------|
| `/health` | Service health check |
| `/metrics` | Basic metrics (counters, uptime) |

---

**Last Updated:** 2026-02-03
