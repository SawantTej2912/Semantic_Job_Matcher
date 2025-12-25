# Kafka Pipeline - Quick Reference Guide

## 🚀 Quick Start

### Option 1: Automated Startup (Recommended)
```bash
cd /Users/sawanttej/Desktop/W
./start_pipeline.sh
```

This script will:
1. Clean up existing containers
2. Build services
3. Start infrastructure (Zookeeper, Kafka, PostgreSQL, Redis)
4. Wait for Kafka to be ready
5. Run producer to create topic and send jobs
6. Start consumer to process jobs

---

### Option 2: Manual Startup

```bash
# 1. Stop and clean
docker-compose down -v

# 2. Build services
docker-compose build kafka_producer kafka_consumer

# 3. Start infrastructure
docker-compose up -d zookeeper kafka postgres redis

# 4. Wait for Kafka (important!)
sleep 45

# 5. Run producer (creates topic and sends jobs)
docker-compose up kafka_producer

# 6. Start consumer (processes jobs)
docker-compose up kafka_consumer
```

---

## 🔍 Troubleshooting

### Issue: "UNKNOWN_TOPIC_OR_PART" error

**Cause:** Consumer started before producer created the topic.

**Solution:**
1. Stop the consumer (Ctrl+C)
2. Run the producer first: `docker-compose up kafka_producer`
3. Then start the consumer: `docker-compose up kafka_consumer`

---

### Issue: "Connection refused" to Kafka

**Cause:** Kafka not fully ready yet.

**Solution:**
Wait longer (45-60 seconds) after starting Kafka before running producer/consumer.

```bash
docker-compose up -d kafka
sleep 60
docker-compose up kafka_producer
```

---

### Issue: Consumer shows no messages

**Possible causes:**
1. Producer hasn't run yet → Run `docker-compose up kafka_producer`
2. Topic is empty → Check producer logs for errors
3. Consumer started before topic existed → Restart consumer

**Check topic:**
```bash
docker exec kafka kafka-topics --list --bootstrap-server localhost:9092
docker exec kafka kafka-topics --describe --topic jobs_raw --bootstrap-server localhost:9092
```

---

## 📊 Monitoring

### View logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f kafka_consumer
docker-compose logs -f kafka_producer
docker-compose logs -f kafka
```

### Check Kafka topics
```bash
# List all topics
docker exec kafka kafka-topics --list --bootstrap-server localhost:9092

# Describe jobs_raw topic
docker exec kafka kafka-topics --describe --topic jobs_raw --bootstrap-server localhost:9092

# Check messages in topic
docker exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic jobs_raw \
  --from-beginning \
  --max-messages 5
```

### Check PostgreSQL
```bash
# Connect to PostgreSQL
docker exec -it postgres psql -U user -d jobs

# Inside psql:
\dt                          # List tables
SELECT COUNT(*) FROM jobs_enriched;
SELECT id, company, position, seniority FROM jobs_enriched LIMIT 5;
\q                           # Exit
```

### Check Redis
```bash
# Connect to Redis
docker exec -it redis redis-cli

# Inside redis-cli:
KEYS *                       # List all keys
LRANGE recent_jobs 0 10     # Get recent job IDs
GET job:some-job-id         # Get specific job
QUIT                         # Exit
```

---

## 🏗️ Architecture

```
┌─────────────┐
│  Producer   │ ──┐
│ (job scraper)│  │
└─────────────┘  │
                 ▼
            ┌─────────┐
            │  Kafka  │
            │ (broker)│
            └─────────┘
                 │
                 ▼
         ┌──────────────┐
         │   Consumer   │
         │ (enrichment) │
         └──────────────┘
                 │
        ┌────────┴────────┐
        ▼                 ▼
   ┌──────────┐      ┌───────┐
   │PostgreSQL│      │ Redis │
   │  (jobs)  │      │(cache)│
   └──────────┘      └───────┘
```

---

## 📝 Key Configuration

### Kafka Broker Addresses
- **Inside Docker:** `kafka:9092` (used by producer & consumer)
- **From host:** `localhost:29092` (for debugging)

### Environment Variables

**Producer:**
- `KAFKA_BROKER=kafka:9092`

**Consumer:**
- `KAFKA_BROKER=kafka:9092`
- `POSTGRES_HOST=postgres`
- `POSTGRES_DB=jobs`
- `POSTGRES_USER=user`
- `POSTGRES_PASSWORD=pass`
- `REDIS_HOST=redis`

---

## ✅ Success Indicators

### Producer Success
```
Starting job producer...
Fetching jobs from RemoteOK API...
Sending 10 jobs to Kafka topic 'jobs_raw'...
Message delivered to jobs_raw [0]
...
All messages sent successfully!
Producer finished.
```

### Consumer Success
```
Waiting for Kafka to be ready...
Kafka is ready!
Waiting for PostgreSQL to be ready...
PostgreSQL is ready!
Creating database tables...
Tables created successfully
Connecting to Kafka at kafka:9092...
Subscribed to topic: jobs_raw

=== Starting job enrichment consumer ===

📥 Consumed job ID: 12345
   Position: Senior Python Developer
   Company: Tech Corp
🔄 Enriching job 12345...
💾 Saving to PostgreSQL...
📦 Cached in Redis
✅ Enriched job saved: 12345
   Skills: ['python', 'aws', 'docker']
   Seniority: Senior
```

---

## 🛑 Stopping Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v

# Stop specific service
docker-compose stop kafka_consumer
```

---

## 🔄 Restart Services

```bash
# Restart consumer only
docker-compose restart kafka_consumer

# Restart all
docker-compose restart
```
