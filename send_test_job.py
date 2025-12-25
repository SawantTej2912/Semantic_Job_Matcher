#!/usr/bin/env python3
"""
Send a test job message to Kafka for debugging Gemini enrichment.
"""
import json
from confluent_kafka import Producer

KAFKA_BROKER = "localhost:29092"
TOPIC = "jobs_raw"

test_job = {
    "id": "test-12345",
    "company": "TechCorp AI",
    "position": "Senior Python Developer - Machine Learning",
    "tags": ["python", "machine learning", "aws", "docker"],
    "description": """We are seeking an experienced Senior Python Developer to join our ML team. 
    
The ideal candidate will have 5+ years of experience building scalable backend systems using Python, 
with strong expertise in machine learning frameworks like TensorFlow and PyTorch. You'll work on 
deploying ML models to production using Docker and Kubernetes on AWS.

Key Requirements:
- Expert-level Python programming
- Experience with TensorFlow, PyTorch, or similar ML frameworks
- Strong knowledge of AWS services (EC2, S3, Lambda, SageMaker)
- Proficiency with Docker and Kubernetes
- Experience with PostgreSQL and Redis
- Familiarity with CI/CD pipelines
- Strong understanding of RESTful APIs and microservices architecture

Nice to have:
- Experience with Kafka or other message queues
- Knowledge of React or other frontend frameworks
- Contributions to open-source ML projects

This is a remote position with competitive salary and benefits.""",
    "location": "Remote (US)",
    "url": "https://example.com/jobs/senior-python-ml"
}

def delivery_report(err, msg):
    if err is not None:
        print(f"❌ Message delivery failed: {err}")
    else:
        print(f"✅ Message delivered to {msg.topic()} [{msg.partition()}]")

# Create producer
conf = {
    'bootstrap.servers': KAFKA_BROKER,
    'client.id': 'test-producer'
}
producer = Producer(conf)

# Send test job
print("📤 Sending test job to Kafka...")
print(f"   Topic: {TOPIC}")
print(f"   Job: {test_job['position']} at {test_job['company']}")
print()

job_json = json.dumps(test_job)
producer.produce(
    TOPIC,
    key=str(test_job['id']).encode('utf-8'),
    value=job_json.encode('utf-8'),
    callback=delivery_report
)

producer.flush()
print("\n✅ Test job sent successfully!")
print("\nNow run: python3 debug_consumer.py")
