"""
Kafka consumer that reads jobs from jobs_raw topic, enriches them, and stores in PostgreSQL.
"""
import json
import os
import sys
import time
from confluent_kafka import Consumer, KafkaError

# Add parent directories to path for imports
sys.path.append('/app')
sys.path.append('/app/services')

from services.kafka.enrichment import enrich_job
from services.db.postgres import insert_enriched_job, create_tables, get_connection
from services.redis.redis_cache import cache_job


KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")
TOPIC = "jobs_raw"
GROUP_ID = "job_enrichment_group"


def get_kafka_consumer():
    """
    Create and return a Kafka Consumer instance.
    
    Returns:
        Consumer: Configured Kafka consumer.
    """
    conf = {
        'bootstrap.servers': KAFKA_BROKER,
        'group.id': GROUP_ID,
        'auto.offset.reset': 'earliest',
        'enable.auto.commit': True
    }
    return Consumer(conf)


def wait_for_postgres():
    """
    Wait for PostgreSQL to be ready.
    """
    max_retries = 30
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            conn = get_connection()
            conn.close()
            print("PostgreSQL is ready!")
            return
        except Exception as e:
            retry_count += 1
            print(f"Waiting for PostgreSQL... ({retry_count}/{max_retries})")
            time.sleep(2)
    
    raise Exception("PostgreSQL did not become ready in time")


def wait_for_kafka():
    """
    Wait for Kafka to be ready.
    """
    from confluent_kafka.admin import AdminClient
    
    max_retries = 30
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            admin_client = AdminClient({'bootstrap.servers': KAFKA_BROKER})
            # Try to get cluster metadata
            metadata = admin_client.list_topics(timeout=5)
            print("Kafka is ready!")
            return
        except Exception as e:
            retry_count += 1
            print(f"Waiting for Kafka... ({retry_count}/{max_retries}): {e}")
            time.sleep(2)
    
    raise Exception("Kafka did not become ready in time")


def consume_and_enrich_jobs():
    """
    Main consumer loop that reads jobs, enriches them, and stores in PostgreSQL.
    """
    # Wait for Kafka to be ready
    print("Waiting for Kafka to be ready...")
    wait_for_kafka()
    
    # Wait for PostgreSQL to be ready
    print("Waiting for PostgreSQL to be ready...")
    wait_for_postgres()
    
    # Create tables if they don't exist
    print("Creating database tables...")
    create_tables()
    
    # Create Kafka consumer
    print(f"Connecting to Kafka at {KAFKA_BROKER}...")
    consumer = get_kafka_consumer()
    
    # Subscribe with retry logic (topic might not exist yet)
    max_subscribe_retries = 10
    subscribe_retry = 0
    
    while subscribe_retry < max_subscribe_retries:
        try:
            consumer.subscribe([TOPIC])
            print(f"Subscribed to topic: {TOPIC}")
            break
        except Exception as e:
            subscribe_retry += 1
            print(f"Waiting for topic '{TOPIC}' to be available... ({subscribe_retry}/{max_subscribe_retries})")
            time.sleep(3)
            if subscribe_retry >= max_subscribe_retries:
                print(f"Warning: Could not verify topic exists, but will continue anyway.")
                consumer.subscribe([TOPIC])
    
    print("\n=== Starting job enrichment consumer ===\n")
    
    try:
        while True:
            # Poll for messages
            msg = consumer.poll(timeout=1.0)
            
            if msg is None:
                continue
            
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    # End of partition, not an error
                    continue
                elif msg.error().code() == KafkaError.UNKNOWN_TOPIC_OR_PART:
                    # Topic doesn't exist yet - producer hasn't run
                    print(f"⚠️  Topic '{TOPIC}' not found. Waiting for producer to create it...")
                    time.sleep(5)
                    continue
                else:
                    print(f"Consumer error: {msg.error()}")
                    continue
            
            # Process message
            try:
                # Decode message
                job_data = json.loads(msg.value().decode('utf-8'))
                job_id = job_data.get('id', 'unknown')
                
                print(f"\n📥 Consumed job ID: {job_id}")
                print(f"   Position: {job_data.get('position', 'N/A')}")
                print(f"   Company: {job_data.get('company', 'N/A')}")
                
                # Enrich the job
                print(f"🔄 Enriching job {job_id}...")
                enriched_job = enrich_job(job_data)
                
                # Store in PostgreSQL
                print(f"💾 Saving to PostgreSQL...")
                insert_enriched_job(enriched_job)
                
                # Cache in Redis
                try:
                    cache_job(enriched_job)
                    print(f"📦 Cached in Redis")
                except Exception as e:
                    print(f"⚠️  Redis caching failed: {e}")
                
                print(f"✅ Enriched job saved: {job_id}")
                print(f"   Skills: {enriched_job.get('skills', [])}")
                print(f"   Seniority: {enriched_job.get('seniority', 'N/A')}")
                
            except json.JSONDecodeError as e:
                print(f"❌ Error decoding message: {e}")
            except Exception as e:
                print(f"❌ Error processing job: {e}")
                import traceback
                traceback.print_exc()
    
    except KeyboardInterrupt:
        print("\n\n🛑 Consumer stopped by user")
    
    finally:
        # Close consumer
        consumer.close()
        print("Consumer closed")


if __name__ == "__main__":
    consume_and_enrich_jobs()
