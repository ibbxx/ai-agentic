# Telegram Agent Bot

This is a local-first Telegram bot agent built with Python, FastAPI, and PostgreSQL. It features task management, daily briefs, and an approval system for sensitive actions.

## Technology Stack
- **Python 3.11**
- **FastAPI**
- **PostgreSQL**
- **Docker Compose**
- **SQLAlchemy & Alembic**
- **python-telegram-bot**

## Setup & Run Instructions

### Prerequisites
- Docker & Docker Compose
- A Telegram Bot Token (from @BotFather)

### Configuration
1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Edit `.env` and fill in your values:
   - `TELEGRAM_BOT_TOKEN`: Your bot token.
   - `TELEGRAM_CHAT_ID`: Your chat ID (or comma-separated IDs) for admin/approvals.
   - `DATABASE_URL`: Setup automatically for Docker, but can be customized.

### Running with Docker (Recommended)
1. Build and start the services:
   ```bash
   docker-compose up -d --build
   ```
2. The bot should now be running and polling for updates.
3. To view logs:
   ```bash
   docker-compose logs -f app
   ```

### Running Locally (Development)
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Start the database (you can use the docker postgres service):
   ```bash
   docker-compose up -d postgres
   ```
3. Run migrations:
   ```bash
   alembic upgrade head
   ```
4. Start the application:
   ```bash
   python src/main.py
   ```

## Definition of Done (v0.1)
- [ ] Telegram Bot receives messages.
- [ ] Agent can: add task, list task, close task.
- [ ] Daily brief automated at 07:30 (Asia/Makassar).
- [ ] All activity logged to Postgres.
- [ ] High-risk actions require "APPROVE <id>".
- [ ] Unit tests for parsing & basic CRUD.
