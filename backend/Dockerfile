
FROM python:3.11-slim

WORKDIR /app/backend

# Copy requirements from backend directory
COPY backend/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy entire project (backend and services)
COPY . /app

# Set PYTHONPATH to include both /app (for services) and /app/backend
ENV PYTHONPATH=/app:/app/backend

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
