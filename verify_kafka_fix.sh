#!/bin/bash
# Kafka Fix Verification Script
# This script verifies that the Kafka broker mismatch is resolved

echo "=========================================="
echo "Kafka Fix Verification Script"
echo "=========================================="
echo ""

echo "Step 1: Stopping all containers..."
docker-compose down
echo "✅ Containers stopped"
echo ""

echo "Step 2: Rebuilding kafka_producer and kafka_consumer..."
docker-compose build kafka_producer kafka_consumer
echo "✅ Services rebuilt"
echo ""

echo "Step 3: Starting infrastructure services..."
docker-compose up -d zookeeper kafka postgres redis
echo "✅ Infrastructure started"
echo ""

echo "Step 4: Waiting for Kafka to be ready (30 seconds)..."
sleep 30
echo "✅ Kafka should be ready"
echo ""

echo "Step 5: Checking Kafka connectivity..."
docker exec kafka kafka-broker-api-versions --bootstrap-server localhost:9092 > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Kafka is accessible"
else
    echo "❌ Kafka is not accessible"
    exit 1
fi
echo ""

echo "Step 6: Starting producer (will run once and exit)..."
docker-compose up kafka_producer
echo "✅ Producer finished"
echo ""

echo "Step 7: Listing Kafka topics..."
docker exec kafka kafka-topics --list --bootstrap-server localhost:9092
echo ""

echo "Step 8: Checking if 'jobs_raw' topic exists..."
TOPIC_EXISTS=$(docker exec kafka kafka-topics --list --bootstrap-server localhost:9092 | grep -c "jobs_raw")
if [ $TOPIC_EXISTS -eq 1 ]; then
    echo "✅ Topic 'jobs_raw' exists!"
else
    echo "❌ Topic 'jobs_raw' does NOT exist"
    exit 1
fi
echo ""

echo "Step 9: Describing 'jobs_raw' topic..."
docker exec kafka kafka-topics --describe --topic jobs_raw --bootstrap-server localhost:9092
echo ""

echo "Step 10: Starting consumer..."
echo "The consumer will now start and should successfully consume messages."
echo "Press Ctrl+C to stop the consumer."
echo ""
docker-compose up kafka_consumer
