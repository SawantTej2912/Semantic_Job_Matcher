# Debug Consumer Usage Guide

## Overview
The `debug_consumer.py` script connects to Kafka, consumes a single message from the `jobs_raw` topic, and runs it through the Gemini enrichment pipeline to verify that skills extraction and embedding generation are working correctly.

## Prerequisites

1. **Kafka must be running** with messages in the `jobs_raw` topic
2. **GEMINI_API_KEY** must be set in your environment

## How to Run

### Option 1: Run Locally (Recommended for Debugging)

```bash
# 1. Make sure Kafka is running
docker-compose up -d kafka zookeeper

# 2. Make sure there are messages in the topic (run producer)
docker-compose up kafka_producer

# 3. Set your Gemini API key
export GEMINI_API_KEY="your-api-key-here"

# 4. Run the debug script
python3 debug_consumer.py
```

### Option 2: Run Inside Docker

```bash
# Run as a one-off container
docker-compose run --rm \
  -e GEMINI_API_KEY="${GEMINI_API_KEY}" \
  kafka_consumer python debug_consumer.py
```

## What the Script Does

1. **Connects to Kafka** at `localhost:29092` (or `KAFKA_BROKER` env var)
2. **Subscribes** to the `jobs_raw` topic
3. **Consumes ONE message** (waits up to 30 seconds)
4. **Runs Gemini enrichment** to extract:
   - Skills (list of technical skills)
   - Seniority level (Junior/Mid/Senior/Lead)
   - Summary (2-sentence job description)
5. **Generates embedding vector** using Gemini's text-embedding-004 model
6. **Prints detailed results** including:
   - Raw job data
   - Extracted skills
   - Seniority level
   - Summary
   - Embedding vector statistics (dimension, sample values, min/max/mean)
   - Processing times

## Expected Output

```
================================================================================
  🔍 GEMINI ENRICHMENT DEBUG SCRIPT
================================================================================

Kafka Broker: localhost:29092
Topic: jobs_raw
Group ID: debug_consumer_group

✅ GEMINI_API_KEY is set (length: 39)

✅ Connected to Kafka at localhost:29092

📡 Creating Kafka consumer...
✅ Subscribed to topic: jobs_raw

⏳ Waiting for a message (timeout: 30 seconds)...

================================================================================
  📥 RAW MESSAGE RECEIVED
================================================================================

Job ID: job-123
Company: Tech Corp
Position: Senior Python Developer
Location: Remote
...

================================================================================
  🤖 RUNNING GEMINI ENRICHMENT
================================================================================

Calling enrich_job_with_gemini()...

⏱️  Enrichment took 1.23 seconds

📊 EXTRACTED INFORMATION:

  Skills (8 found):
    1. Python
    2. AWS
    3. Docker
    4. Kubernetes
    5. SQL
    6. PostgreSQL
    7. Microservices
    8. REST API

  Seniority Level: Senior

  Summary:
    We are seeking a Senior Python Developer with 5+ years of experience...

================================================================================
  🧮 GENERATING EMBEDDING VECTOR
================================================================================

Input text length: 542 characters
Calling get_gemini_embedding()...

⏱️  Embedding generation took 0.87 seconds

📐 EMBEDDING VECTOR:
  Dimension: 768
  First 10 values: [0.023, -0.041, 0.015, ...]
  ...

================================================================================
  ✅ DEBUG COMPLETE
================================================================================
```

## Troubleshooting

### "Topic 'jobs_raw' not found"
- Run the producer first: `docker-compose up kafka_producer`

### "Could not connect to Kafka"
- Make sure Kafka is running: `docker-compose ps`
- Check Kafka logs: `docker-compose logs kafka`

### "GEMINI_API_KEY is NOT set"
- The script will still run but use placeholder functions
- Set the key: `export GEMINI_API_KEY="your-key"`

### "Timeout reached - no messages received"
- No messages in the topic
- Run producer: `docker-compose up kafka_producer`

## Configuration

You can customize the script behavior with environment variables:

- `KAFKA_BROKER`: Kafka broker address (default: `localhost:29092`)
- `GEMINI_API_KEY`: Your Gemini API key (required for real enrichment)

## Notes

- The script does **not commit offsets**, so you can run it multiple times on the same message
- It processes **only ONE message** and then exits
- Processing times are displayed to help you understand performance
- The script works with or without Gemini API key (falls back to placeholder functions)
