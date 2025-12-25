#!/bin/bash
# Complete Kafka Pipeline Startup Script
# This script starts the entire job enrichment pipeline in the correct order

set -e  # Exit on error

echo "=========================================="
echo "Job Enrichment Pipeline Startup"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Step 1: Cleaning up existing containers...${NC}"
docker-compose down -v
echo -e "${GREEN}✅ Cleanup complete${NC}"
echo ""

echo -e "${YELLOW}Step 2: Building services...${NC}"
docker-compose build kafka_producer kafka_consumer
echo -e "${GREEN}✅ Services built${NC}"
echo ""

echo -e "${YELLOW}Step 3: Starting infrastructure (Zookeeper, Kafka, PostgreSQL, Redis)...${NC}"
docker-compose up -d zookeeper kafka postgres redis
echo -e "${GREEN}✅ Infrastructure started${NC}"
echo ""

echo -e "${YELLOW}Step 4: Waiting for Kafka to be fully ready (45 seconds)...${NC}"
echo "This ensures Kafka is completely initialized before we proceed."
for i in {45..1}; do
    echo -ne "  Waiting... $i seconds remaining\r"
    sleep 1
done
echo -e "\n${GREEN}✅ Kafka should be ready${NC}"
echo ""

echo -e "${YELLOW}Step 5: Verifying Kafka connectivity...${NC}"
max_retries=10
retry=0
while [ $retry -lt $max_retries ]; do
    if docker exec kafka kafka-broker-api-versions --bootstrap-server localhost:9092 > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Kafka is accessible and ready${NC}"
        break
    else
        retry=$((retry + 1))
        echo "  Attempt $retry/$max_retries failed, retrying..."
        sleep 3
    fi
done

if [ $retry -eq $max_retries ]; then
    echo -e "${YELLOW}⚠️  Could not verify Kafka, but continuing anyway${NC}"
fi
echo ""

echo -e "${YELLOW}Step 6: Running producer to create topic and send jobs...${NC}"
echo "The producer will fetch jobs and send them to Kafka."
echo "This will also create the 'jobs_raw' topic automatically."
echo ""
docker-compose up kafka_producer
echo ""
echo -e "${GREEN}✅ Producer finished${NC}"
echo ""

echo -e "${YELLOW}Step 7: Verifying topic creation...${NC}"
TOPICS=$(docker exec kafka kafka-topics --list --bootstrap-server localhost:9092 2>/dev/null)
echo "Available topics:"
echo "$TOPICS"
echo ""

if echo "$TOPICS" | grep -q "jobs_raw"; then
    echo -e "${GREEN}✅ Topic 'jobs_raw' exists!${NC}"
    echo ""
    echo "Topic details:"
    docker exec kafka kafka-topics --describe --topic jobs_raw --bootstrap-server localhost:9092
else
    echo -e "${YELLOW}⚠️  Topic 'jobs_raw' not found. Producer may not have sent any messages.${NC}"
fi
echo ""

echo -e "${YELLOW}Step 8: Starting consumer to process jobs...${NC}"
echo "The consumer will:"
echo "  - Connect to Kafka at kafka:9092"
echo "  - Subscribe to 'jobs_raw' topic"
echo "  - Enrich each job with skills, seniority, summary, and embeddings"
echo "  - Store enriched jobs in PostgreSQL"
echo "  - Cache jobs in Redis"
echo ""
echo "Press Ctrl+C to stop the consumer when done."
echo ""
echo "=========================================="
echo ""

docker-compose up kafka_consumer
