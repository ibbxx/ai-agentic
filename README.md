# AI Agentic - Telegram Task Bot

A self-improving AI-powered Telegram bot for task management with approval gates, memory, and proposal system.

## Features

- 🤖 **Intent Parsing** - Rule-based + LLM fallback
- 📋 **Task Management** - Add, list, complete, delete tasks
- ⚠️ **Approval Gate** - High-risk actions require confirmation
- 🧠 **Memory Layer** - User preferences + reflection logging
- 📈 **Self-Improvement** - Proposal system for learning new patterns
- ☀️ **Daily Brief** - Scheduled morning summaries
- 🔒 **Safety** - Rate limiting, input validation, step limits

## Quick Start

```bash
# Clone and setup
git clone https://github.com/ibbxx/ai-agentic.git
cd ai-agentic
cp .env.example .env

# Edit .env with your tokens
# TELEGRAM_BOT_TOKEN=...
# DATABASE_URL=...
# OPENAI_API_KEY=... (optional)

# Run with Docker
make dev
make migrate
```

## Demo Script

Here's a walkthrough of the bot's capabilities:

### 1. Add Tasks

```
You: add task beli matcha
Bot: ✅ Task added: #1 - beli matcha

You: add task review proposal kerja
Bot: ✅ Task added: #2 - review proposal kerja
```

<!-- Screenshot: add_tasks.png -->

### 2. List Tasks

```
You: list tasks
Bot: 📋 Open Tasks:
       1. beli matcha
       2. review proposal kerja
```

<!-- Screenshot: list_tasks.png -->

### 3. Complete a Task

```
You: done 1
Bot: ✅ Task #1 marked as done.
```

<!-- Screenshot: done_task.png -->

### 4. Daily Brief

```
You: daily brief
Bot: ☀️ Daily Brief:

     Open Tasks (1):
       - review proposal kerja
```

<!-- Screenshot: daily_brief.png -->

### 5. High-Risk Action → Approval Flow

```
You: delete task 2
Bot: ⚠️ **Action requires approval**

     • Permanently delete a task
       To approve, type: `APPROVE 1`

You: APPROVE 1
Bot: ✅ Request #1 approved and executed.
```

<!-- Screenshot: approval_flow.png -->

### 6. Preferences

```
You: my prefs
Bot: ⚙️ **Your Preferences**
     • Brief Time: 07:30
     • Brief Format: detailed
     • Timezone: Asia/Makassar

You: set brief time 08:00
Bot: ✅ Preference updated: brief_time = 08:00
```

<!-- Screenshot: preferences.png -->

### 7. Proposals (Self-Improvement)

```
You: ayo kerja
Bot: 🤖 I didn't understand: "ayo kerja"...

You: proposals
Bot: 📋 **Improvement Proposals**
     ⏳ **#1** - Create alias for: 'ayo kerja'
        → `approve proposal 1` or `reject proposal 1`

You: approve proposal 1
Bot: ✅ Proposal #1 approved. Rule #1 created.
```

<!-- Screenshot: proposals.png -->

## Architecture

```
apps/
├── api/          # FastAPI backend
└── bot/          # Telegram bot

packages/
└── core/         # Shared logic
    └── agent/
        ├── loop.py       # Main orchestration
        ├── intent.py     # Intent classification
        ├── planner.py    # Execution planning
        ├── executor.py   # Tool execution
        ├── formatter.py  # Response formatting
        └── tools/        # Tool implementations
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/metrics` | GET | Basic metrics |
| `/v1/message` | POST | Process bot message |
| `/tasks` | GET | List all tasks |

## Safety

See [docs/Safety.md](docs/Safety.md) for full guardrails documentation.

Key limits:
- Max 6 steps per agent run
- 30s timeout per tool
- 20 requests per minute rate limit
- Blocked patterns: `sudo`, `rm -rf`, `DROP TABLE`, etc.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | Yes | Telegram bot token |
| `DATABASE_URL` | Yes | PostgreSQL connection |
| `TELEGRAM_CHAT_ID` | No | Default chat ID |
| `OPENAI_API_KEY` | No | For LLM fallback |
| `OPENAI_MODEL` | No | Default: gpt-4o-mini |
| `TIMEZONE` | No | Default: Asia/Makassar |

## License

MIT
