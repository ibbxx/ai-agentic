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

# Copy API app
COPY apps/api /app/apps/api

CMD ["uvicorn", "apps.api.src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
