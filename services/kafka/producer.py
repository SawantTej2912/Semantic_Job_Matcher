"""
Kafka producer that fetches jobs and sends them to the jobs_raw topic.
"""
import json
import os
import time
from confluent_kafka import Producer
from services.kafka.job_scraper import fetch_jobs


KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")
TOPIC = "jobs_raw"


def get_producer():
    """
    Creates and returns a Kafka Producer instance.
    
    Returns:
        Producer: Configured Kafka producer.
    """
    conf = {
        'bootstrap.servers': KAFKA_BROKER,
        'client.id': 'job-producer'
    }
    return Producer(conf)


def delivery_report(err, msg):
    """
    Callback function for message delivery reports.
    
    Args:
        err: Error if delivery failed.
        msg: Message that was delivered.
    """
    if err is not None:
        print(f"Message delivery failed: {err}")
    else:
        print(f"Message delivered to {msg.topic()} [{msg.partition()}]")


def send_jobs_to_kafka(producer, jobs):
    """
    Sends job postings to Kafka topic.
    
    Args:
        producer: Kafka Producer instance.
        jobs: List of job dictionaries to send.
    """
    for job in jobs:
        try:
            # Serialize job to JSON
            job_json = json.dumps(job)
            
            # Send to Kafka
            producer.produce(
                TOPIC,
                key=str(job.get('id', '')).encode('utf-8'),
                value=job_json.encode('utf-8'),
                callback=delivery_report
            )
            
            # Poll to handle delivery reports
            producer.poll(0)
            
        except Exception as e:
            print(f"Error sending job {job.get('id', 'unknown')}: {e}")
    
    # Wait for all messages to be delivered
    print("\nFlushing producer...")
    producer.flush()
    print("All messages sent successfully!")


if __name__ == "__main__":
    print("Starting job producer...")
    
    # Wait a bit for Kafka to be ready
    print("Waiting for Kafka to be ready...")
    time.sleep(10)
    
    # Create producer
    producer = get_producer()
    
    # Fetch jobs from RemoteOK
    jobs = fetch_jobs()
    
    if jobs:
        print(f"\nSending {len(jobs)} jobs to Kafka topic '{TOPIC}'...")
        send_jobs_to_kafka(producer, jobs)
    else:
        print("No jobs to send.")
    
    print("\nProducer finished.")
