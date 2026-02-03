FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared packages
COPY packages/core /app/packages/core
RUN pip install -e /app/packages/core

# Copy Bot app
COPY apps/bot /app/apps/bot

CMD ["python", "apps/bot/src/main.py"]
