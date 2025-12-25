#!/usr/bin/env python3
"""
Debug script to test Gemini enrichment on a single Kafka message.
This script connects to the jobs_raw topic, consumes one message,
runs it through Gemini enrichment and embedding functions, and prints the results.
"""
import json
import os
import sys
import time
from confluent_kafka import Consumer, KafkaError

# Add services to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.kafka.enrichment import (
    enrich_job_with_gemini,
    get_gemini_embedding,
    enrich_job
)

# Configuration
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:29092")  # Use host port for local testing
TOPIC = "jobs_raw"
GROUP_ID = "debug_consumer_group"


def print_separator(char="=", length=80):
    """Print a separator line."""
    print(char * length)


def print_section(title):
    """Print a section header."""
    print_separator()
    print(f"  {title}")
    print_separator()


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
        'enable.auto.commit': False  # Don't commit offset for debugging
    }
    return Consumer(conf)


def wait_for_kafka(max_retries=10):
    """
    Wait for Kafka to be ready.
    
    Args:
        max_retries: Maximum number of connection attempts.
    """
    from confluent_kafka.admin import AdminClient
    
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            admin_client = AdminClient({'bootstrap.servers': KAFKA_BROKER})
            metadata = admin_client.list_topics(timeout=5)
            print(f"✅ Connected to Kafka at {KAFKA_BROKER}")
            return True
        except Exception as e:
            retry_count += 1
            print(f"⏳ Waiting for Kafka... ({retry_count}/{max_retries}): {e}")
            time.sleep(2)
    
    print(f"❌ Could not connect to Kafka after {max_retries} attempts")
    return False


def debug_single_message():
    """
    Consume a single message from Kafka and run it through Gemini enrichment.
    """
    print_section("🔍 GEMINI ENRICHMENT DEBUG SCRIPT")
    print(f"\nKafka Broker: {KAFKA_BROKER}")
    print(f"Topic: {TOPIC}")
    print(f"Group ID: {GROUP_ID}\n")
    
    # Check if Gemini API key is set
    gemini_api_key = os.getenv("GEMINI_API_KEY", "")
    if gemini_api_key:
        print(f"✅ GEMINI_API_KEY is set (length: {len(gemini_api_key)})")
    else:
        print("⚠️  GEMINI_API_KEY is NOT set - will use placeholder functions")
    
    print()
    
    # Wait for Kafka
    if not wait_for_kafka():
        print("\n❌ Cannot proceed without Kafka connection")
        return
    
    # Create consumer
    print("\n📡 Creating Kafka consumer...")
    consumer = get_kafka_consumer()
    
    try:
        # Subscribe to topic
        consumer.subscribe([TOPIC])
        print(f"✅ Subscribed to topic: {TOPIC}")
        print("\n⏳ Waiting for a message (timeout: 30 seconds)...\n")
        
        # Poll for a single message
        timeout = 30  # seconds
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            msg = consumer.poll(timeout=1.0)
            
            if msg is None:
                continue
            
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                elif msg.error().code() == KafkaError.UNKNOWN_TOPIC_OR_PART:
                    print(f"⚠️  Topic '{TOPIC}' not found. Make sure the producer has run first.")
                    print("   Run: docker-compose up kafka_producer")
                    return
                else:
                    print(f"❌ Consumer error: {msg.error()}")
                    continue
            
            # Message received!
            print_section("📥 RAW MESSAGE RECEIVED")
            
            try:
                # Decode the message
                job_data = json.loads(msg.value().decode('utf-8'))
                
                # Print raw job data
                print(f"\nJob ID: {job_data.get('id', 'N/A')}")
                print(f"Company: {job_data.get('company', 'N/A')}")
                print(f"Position: {job_data.get('position', 'N/A')}")
                print(f"Location: {job_data.get('location', 'N/A')}")
                print(f"URL: {job_data.get('url', 'N/A')}")
                print(f"Tags: {job_data.get('tags', [])}")
                print(f"\nDescription (first 300 chars):")
                description = job_data.get('description', '')
                print(f"{description[:300]}...")
                
                # Run Gemini enrichment
                print_section("🤖 RUNNING GEMINI ENRICHMENT")
                print("\nCalling enrich_job_with_gemini()...\n")
                
                start_enrich = time.time()
                gemini_result = enrich_job_with_gemini(
                    description=job_data.get('description', ''),
                    position=job_data.get('position', '')
                )
                enrich_time = time.time() - start_enrich
                
                print(f"⏱️  Enrichment took {enrich_time:.2f} seconds\n")
                print("📊 EXTRACTED INFORMATION:")
                print(f"\n  Skills ({len(gemini_result['skills'])} found):")
                for i, skill in enumerate(gemini_result['skills'], 1):
                    print(f"    {i}. {skill}")
                
                print(f"\n  Seniority Level: {gemini_result['seniority']}")
                
                print(f"\n  Summary:")
                print(f"    {gemini_result['summary']}")
                
                # Generate embedding
                print_section("🧮 GENERATING EMBEDDING VECTOR")
                
                full_text = f"{job_data.get('position', '')}. {description}"
                print(f"\nInput text length: {len(full_text)} characters")
                print("Calling get_gemini_embedding()...\n")
                
                start_embed = time.time()
                embedding = get_gemini_embedding(full_text)
                embed_time = time.time() - start_embed
                
                print(f"⏱️  Embedding generation took {embed_time:.2f} seconds\n")
                print(f"📐 EMBEDDING VECTOR:")
                print(f"  Dimension: {len(embedding)}")
                print(f"  First 10 values: {embedding[:10]}")
                print(f"  Last 10 values: {embedding[-10:]}")
                print(f"  Min value: {min(embedding):.6f}")
                print(f"  Max value: {max(embedding):.6f}")
                print(f"  Mean value: {sum(embedding)/len(embedding):.6f}")
                
                # Run full enrichment pipeline
                print_section("🔄 FULL ENRICHMENT PIPELINE")
                print("\nCalling enrich_job() (combines both functions)...\n")
                
                start_full = time.time()
                enriched_job = enrich_job(job_data)
                full_time = time.time() - start_full
                
                print(f"⏱️  Full enrichment took {full_time:.2f} seconds\n")
                print("✅ ENRICHED JOB DATA:")
                print(json.dumps({
                    'id': enriched_job.get('id'),
                    'company': enriched_job.get('company'),
                    'position': enriched_job.get('position'),
                    'location': enriched_job.get('location'),
                    'skills': enriched_job.get('skills'),
                    'seniority': enriched_job.get('seniority'),
                    'summary': enriched_job.get('summary'),
                    'embedding_dimension': len(enriched_job.get('embedding', []))
                }, indent=2))
                
                # Summary
                print_section("📈 SUMMARY")
                print(f"\n✅ Successfully processed job: {job_data.get('id')}")
                print(f"✅ Extracted {len(gemini_result['skills'])} skills")
                print(f"✅ Determined seniority: {gemini_result['seniority']}")
                print(f"✅ Generated {len(embedding)}-dimensional embedding vector")
                print(f"\n⏱️  Total processing time: {full_time:.2f} seconds")
                print(f"   - Enrichment: {enrich_time:.2f}s")
                print(f"   - Embedding: {embed_time:.2f}s")
                
                print_section("✅ DEBUG COMPLETE")
                
                # We got our message, exit
                return
                
            except json.JSONDecodeError as e:
                print(f"❌ Error decoding message: {e}")
                return
            except Exception as e:
                print(f"❌ Error processing job: {e}")
                import traceback
                traceback.print_exc()
                return
        
        # Timeout reached
        print(f"\n⏱️  Timeout reached ({timeout}s) - no messages received")
        print("\n💡 Tips:")
        print("   1. Make sure the producer has run: docker-compose up kafka_producer")
        print("   2. Check if Kafka is running: docker-compose ps")
        print("   3. Check Kafka logs: docker-compose logs kafka")
        
    except KeyboardInterrupt:
        print("\n\n🛑 Interrupted by user")
    
    finally:
        # Close consumer
        consumer.close()
        print("\n👋 Consumer closed")


if __name__ == "__main__":
    debug_single_message()
