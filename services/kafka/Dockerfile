
FROM python:3.11-slim

WORKDIR /app

# Copy all requirements files from services subdirectories
COPY services/kafka/requirements.txt ./kafka_requirements.txt
COPY services/db/requirements.txt ./db_requirements.txt
COPY services/redis/requirements.txt ./redis_requirements.txt

# Install all dependencies
RUN pip install --no-cache-dir -r kafka_requirements.txt && \
    pip install --no-cache-dir -r db_requirements.txt && \
    pip install --no-cache-dir -r redis_requirements.txt

# Copy the entire services directory structure to preserve package hierarchy
COPY services/ ./services/

CMD ["python", "-m", "services.kafka.producer"]
