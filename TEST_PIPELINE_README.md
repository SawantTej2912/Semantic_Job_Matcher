# Pipeline Diagnostic Tool - Usage Guide

## 📋 Overview

`test_pipeline.py` is a comprehensive diagnostic script that verifies your job pipeline's health by checking:

1. **Kafka Check**: Connects to `kafka:9092` broker and lists all topics to ensure `jobs_raw` exists
2. **PostgreSQL Check**: Connects to the `jobs_enriched` table and returns the count of total records
3. **Redis Check**: Connects to Redis and returns the length of the `recent_jobs` list
4. **End-to-End Data Check**: Prints the 'position' and 'company' of the 3 most recent records in PostgreSQL

## 🚀 Quick Start

### Prerequisites

Install required Python packages:
```bash
pip3 install confluent-kafka psycopg2-binary redis
```

### Run the Diagnostic

```bash
python3 test_pipeline.py
```

## 📊 What It Checks

### 1. Kafka Check
- ✅ Connects to Kafka broker at `localhost:29092`
- ✅ Lists all available topics
- ✅ Verifies `jobs_raw` topic exists (or notes it will be auto-created)

### 2. PostgreSQL Check
- ✅ Connects to PostgreSQL at `localhost:5432`
- ✅ Verifies `jobs_enriched` table exists
- ✅ Returns total record count

### 3. Redis Check
- ✅ Connects to Redis at `localhost:6379`
- ✅ Checks `recent_jobs` list length
- ✅ Shows sample job IDs if available

### 4. End-to-End Data Flow
- ✅ Retrieves 3 most recent jobs from PostgreSQL
- ✅ Displays position, company, seniority, and creation time
- ✅ Verifies data successfully moved from Kafka → Consumer → Database

## 🎯 Sample Output

```
======================================================================
  🔧 PIPELINE DIAGNOSTIC TOOL
  Testing: Kafka → PostgreSQL → Redis Data Flow
======================================================================

======================================================================
  🔍 KAFKA CHECK
======================================================================

✅ Kafka Connection
   └─ Connected to localhost:29092
✅ Available Topics
   └─ Found 2 topics
      • __consumer_offsets
      • jobs_raw
✅ jobs_raw Topic
   └─ Topic exists and is ready

======================================================================
  🔍 POSTGRESQL CHECK
======================================================================

✅ PostgreSQL Connection
   └─ Connected to localhost:5432
✅ jobs_enriched Table
   └─ Table exists
✅ Total Records
   └─ 42 records in jobs_enriched table

======================================================================
  🔍 REDIS CHECK
======================================================================

✅ Redis Connection
   └─ Connected to localhost:6379
✅ recent_jobs List
   └─ 42 job IDs cached
   └─ Sample IDs:
      • job_12345
      • job_12346
      • job_12347

======================================================================
  🔍 END-TO-END DATA FLOW CHECK
======================================================================

✅ Recent Jobs in Database
   └─ Found 3 recent jobs

   📋 Most Recent Jobs:
   ------------------------------------------------------------------

   1. Position: Senior Python Developer
      Company:  TechCorp Inc
      Seniority: Senior
      Created:  2024-12-23 14:30:15

   2. Position: Full Stack Engineer
      Company:  StartupXYZ
      Seniority: Mid
      Created:  2024-12-23 14:29:45

   3. Position: DevOps Engineer
      Company:  CloudSolutions
      Seniority: Senior
      Created:  2024-12-23 14:29:20

======================================================================
  📊 DIAGNOSTIC SUMMARY
======================================================================

Kafka:        ✅
PostgreSQL:   ✅
Redis:        ✅
Data Flow:    ✅

======================================================================
✅ ALL CHECKS PASSED - Pipeline is healthy!
======================================================================
```

## 🔧 Configuration

The script uses the following default connection settings:

```python
# Kafka
kafka_broker = "localhost:29092"  # Host port for local testing

# PostgreSQL
postgres_config = {
    "host": "localhost",
    "port": 5432,
    "database": "jobs",
    "user": "user",
    "password": "pass"
}

# Redis
redis_config = {
    "host": "localhost",
    "port": 6379
}
```

### Modify for Docker Network Testing

If you want to test from inside the Docker network, change:
```python
self.kafka_broker = "kafka:9092"
self.postgres_config["host"] = "postgres"
self.redis_config["host"] = "redis"
```

## 🐛 Troubleshooting

### No Data Found

If you see warnings about no data:

```bash
# 1. Start infrastructure
docker-compose up -d zookeeper kafka postgres redis

# 2. Wait for services to be ready
sleep 30

# 3. Run producer to fetch jobs
docker-compose up kafka_producer

# 4. Run consumer to enrich and store jobs
docker-compose up kafka_consumer

# 5. Run diagnostic again
python3 test_pipeline.py
```

### Connection Errors

If services aren't running:

```bash
# Check service status
docker-compose ps

# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f
```

### Kafka Topic Not Found

The `jobs_raw` topic is auto-created when the producer first sends a message. This is normal and expected.

## 💡 Integration with Pipeline

You can run this diagnostic:

- **Before starting the pipeline**: To verify infrastructure is ready
- **After running producer/consumer**: To verify data flow
- **During debugging**: To identify which component is failing
- **In CI/CD**: As a health check before deployment

## 📝 Exit Codes

- `0`: All checks passed ✅
- `1`: One or more checks failed ⚠️

This makes it suitable for automated testing:

```bash
if python3 test_pipeline.py; then
    echo "Pipeline is healthy!"
else
    echo "Pipeline has issues, check output above"
fi
```

## 🔗 Related Files

- `docker-compose.yml`: Service orchestration
- `start_pipeline.sh`: Automated pipeline startup
- `KAFKA_GUIDE.md`: Kafka troubleshooting
- `PROJECT_STATEMENT.md`: Full project documentation
