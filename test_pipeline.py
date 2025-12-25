#!/usr/bin/env python3
"""
Pipeline Diagnostic Script
Tests Kafka, PostgreSQL, and Redis connectivity and data flow
"""

import sys
import json
from typing import Dict, List, Optional
from datetime import datetime

# Kafka imports
try:
    from confluent_kafka.admin import AdminClient
    from confluent_kafka import KafkaException
except ImportError:
    print("⚠️  confluent-kafka not installed. Run: pip install confluent-kafka")
    sys.exit(1)

# PostgreSQL imports
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    print("⚠️  psycopg2 not installed. Run: pip install psycopg2-binary")
    sys.exit(1)

# Redis imports
try:
    import redis
except ImportError:
    print("⚠️  redis not installed. Run: pip install redis")
    sys.exit(1)


class PipelineDiagnostics:
    """Comprehensive pipeline diagnostic checker"""
    
    def __init__(self):
        # Configuration from environment or defaults
        self.kafka_broker = "localhost:29092"  # Use host port for local testing
        self.postgres_config = {
            "host": "localhost",
            "port": 5432,
            "database": "jobs",
            "user": "user",
            "password": "pass"
        }
        self.redis_config = {
            "host": "localhost",
            "port": 6379,
            "decode_responses": True
        }
        
        self.results = {
            "kafka": {"status": "❌", "details": {}},
            "postgres": {"status": "❌", "details": {}},
            "redis": {"status": "❌", "details": {}},
            "data_flow": {"status": "❌", "details": {}}
        }
    
    def print_header(self, title: str):
        """Print formatted section header"""
        print(f"\n{'='*70}")
        print(f"  {title}")
        print(f"{'='*70}\n")
    
    def print_result(self, check_name: str, status: str, details: str = ""):
        """Print formatted check result"""
        print(f"{status} {check_name}")
        if details:
            print(f"   └─ {details}")
    
    def check_kafka(self) -> bool:
        """Check Kafka connectivity and topics"""
        self.print_header("🔍 KAFKA CHECK")
        
        try:
            # Create admin client
            admin_client = AdminClient({"bootstrap.servers": self.kafka_broker})
            
            # Get cluster metadata
            metadata = admin_client.list_topics(timeout=10)
            
            # Check if jobs_raw topic exists
            topics = metadata.topics
            topic_list = list(topics.keys())
            
            self.print_result(
                "Kafka Connection",
                "✅",
                f"Connected to {self.kafka_broker}"
            )
            
            self.print_result(
                "Available Topics",
                "✅",
                f"Found {len(topic_list)} topics"
            )
            
            for topic in topic_list:
                print(f"      • {topic}")
            
            # Check for jobs_raw topic
            if "jobs_raw" in topic_list:
                self.print_result(
                    "jobs_raw Topic",
                    "✅",
                    "Topic exists and is ready"
                )
                jobs_raw_exists = True
            else:
                self.print_result(
                    "jobs_raw Topic",
                    "⚠️",
                    "Topic does not exist (will be auto-created on first message)"
                )
                jobs_raw_exists = False
            
            self.results["kafka"]["status"] = "✅"
            self.results["kafka"]["details"] = {
                "broker": self.kafka_broker,
                "topics": topic_list,
                "jobs_raw_exists": jobs_raw_exists
            }
            
            return True
            
        except KafkaException as e:
            self.print_result(
                "Kafka Connection",
                "❌",
                f"Failed: {str(e)}"
            )
            self.results["kafka"]["details"]["error"] = str(e)
            return False
        except Exception as e:
            self.print_result(
                "Kafka Connection",
                "❌",
                f"Unexpected error: {str(e)}"
            )
            self.results["kafka"]["details"]["error"] = str(e)
            return False
    
    def check_postgres(self) -> bool:
        """Check PostgreSQL connectivity and data"""
        self.print_header("🔍 POSTGRESQL CHECK")
        
        try:
            # Connect to PostgreSQL
            conn = psycopg2.connect(**self.postgres_config)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            self.print_result(
                "PostgreSQL Connection",
                "✅",
                f"Connected to {self.postgres_config['host']}:{self.postgres_config['port']}"
            )
            
            # Check if jobs_enriched table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'jobs_enriched'
                );
            """)
            table_exists = cursor.fetchone()['exists']
            
            if table_exists:
                self.print_result(
                    "jobs_enriched Table",
                    "✅",
                    "Table exists"
                )
                
                # Get record count
                cursor.execute("SELECT COUNT(*) as count FROM jobs_enriched;")
                count = cursor.fetchone()['count']
                
                self.print_result(
                    "Total Records",
                    "✅",
                    f"{count} records in jobs_enriched table"
                )
                
                self.results["postgres"]["status"] = "✅"
                self.results["postgres"]["details"] = {
                    "host": self.postgres_config['host'],
                    "database": self.postgres_config['database'],
                    "table_exists": True,
                    "record_count": count
                }
                
            else:
                self.print_result(
                    "jobs_enriched Table",
                    "⚠️",
                    "Table does not exist (run consumer to create it)"
                )
                self.results["postgres"]["status"] = "⚠️"
                self.results["postgres"]["details"] = {
                    "host": self.postgres_config['host'],
                    "database": self.postgres_config['database'],
                    "table_exists": False,
                    "record_count": 0
                }
            
            cursor.close()
            conn.close()
            return True
            
        except psycopg2.OperationalError as e:
            self.print_result(
                "PostgreSQL Connection",
                "❌",
                f"Connection failed: {str(e)}"
            )
            self.results["postgres"]["details"]["error"] = str(e)
            return False
        except Exception as e:
            self.print_result(
                "PostgreSQL Check",
                "❌",
                f"Unexpected error: {str(e)}"
            )
            self.results["postgres"]["details"]["error"] = str(e)
            return False
    
    def check_redis(self) -> bool:
        """Check Redis connectivity and cached data"""
        self.print_header("🔍 REDIS CHECK")
        
        try:
            # Connect to Redis
            r = redis.Redis(**self.redis_config)
            
            # Test connection
            r.ping()
            
            self.print_result(
                "Redis Connection",
                "✅",
                f"Connected to {self.redis_config['host']}:{self.redis_config['port']}"
            )
            
            # Check recent_jobs list
            recent_jobs_length = r.llen("recent_jobs")
            
            if recent_jobs_length > 0:
                self.print_result(
                    "recent_jobs List",
                    "✅",
                    f"{recent_jobs_length} job IDs cached"
                )
                
                # Get a sample of job IDs
                sample_jobs = r.lrange("recent_jobs", 0, 4)
                print(f"   └─ Sample IDs:")
                for job_id in sample_jobs[:3]:
                    print(f"      • {job_id}")
                
            else:
                self.print_result(
                    "recent_jobs List",
                    "⚠️",
                    "No jobs cached yet (run consumer to populate)"
                )
            
            self.results["redis"]["status"] = "✅"
            self.results["redis"]["details"] = {
                "host": self.redis_config['host'],
                "recent_jobs_count": recent_jobs_length
            }
            
            return True
            
        except redis.ConnectionError as e:
            self.print_result(
                "Redis Connection",
                "❌",
                f"Connection failed: {str(e)}"
            )
            self.results["redis"]["details"]["error"] = str(e)
            return False
        except Exception as e:
            self.print_result(
                "Redis Check",
                "❌",
                f"Unexpected error: {str(e)}"
            )
            self.results["redis"]["details"]["error"] = str(e)
            return False
    
    def check_data_flow(self) -> bool:
        """Verify end-to-end data flow by checking recent records"""
        self.print_header("🔍 END-TO-END DATA FLOW CHECK")
        
        try:
            # Connect to PostgreSQL
            conn = psycopg2.connect(**self.postgres_config)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Check if table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'jobs_enriched'
                );
            """)
            
            if not cursor.fetchone()['exists']:
                self.print_result(
                    "Data Flow",
                    "⚠️",
                    "jobs_enriched table doesn't exist yet"
                )
                cursor.close()
                conn.close()
                return False
            
            # Get 3 most recent records
            cursor.execute("""
                SELECT id, position, company, seniority, created_at
                FROM jobs_enriched
                ORDER BY created_at DESC
                LIMIT 3;
            """)
            
            recent_jobs = cursor.fetchall()
            
            if recent_jobs:
                self.print_result(
                    "Recent Jobs in Database",
                    "✅",
                    f"Found {len(recent_jobs)} recent jobs"
                )
                
                print(f"\n   📋 Most Recent Jobs:")
                print(f"   {'-'*66}")
                
                for idx, job in enumerate(recent_jobs, 1):
                    print(f"\n   {idx}. Position: {job['position']}")
                    print(f"      Company:  {job['company']}")
                    print(f"      Seniority: {job['seniority'] or 'Not specified'}")
                    print(f"      Created:  {job['created_at']}")
                
                self.results["data_flow"]["status"] = "✅"
                self.results["data_flow"]["details"] = {
                    "recent_jobs": [
                        {
                            "position": job["position"],
                            "company": job["company"],
                            "seniority": job["seniority"],
                            "created_at": str(job["created_at"])
                        }
                        for job in recent_jobs
                    ]
                }
                
            else:
                self.print_result(
                    "Recent Jobs",
                    "⚠️",
                    "No jobs found in database yet"
                )
                self.results["data_flow"]["status"] = "⚠️"
                self.results["data_flow"]["details"]["message"] = "No data yet"
            
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            self.print_result(
                "Data Flow Check",
                "❌",
                f"Error: {str(e)}"
            )
            self.results["data_flow"]["details"]["error"] = str(e)
            return False
    
    def print_summary(self):
        """Print overall diagnostic summary"""
        self.print_header("📊 DIAGNOSTIC SUMMARY")
        
        print(f"Kafka:        {self.results['kafka']['status']}")
        print(f"PostgreSQL:   {self.results['postgres']['status']}")
        print(f"Redis:        {self.results['redis']['status']}")
        print(f"Data Flow:    {self.results['data_flow']['status']}")
        
        # Overall status
        all_green = all(
            result["status"] == "✅" 
            for result in self.results.values()
        )
        
        print(f"\n{'='*70}")
        if all_green:
            print("✅ ALL CHECKS PASSED - Pipeline is healthy!")
        else:
            print("⚠️  SOME CHECKS FAILED - Review details above")
        print(f"{'='*70}\n")
        
        # Recommendations
        if not all_green:
            print("💡 Recommendations:")
            
            if self.results["kafka"]["status"] != "✅":
                print("   • Start Kafka: docker-compose up -d kafka zookeeper")
            
            if self.results["postgres"]["status"] != "✅":
                print("   • Start PostgreSQL: docker-compose up -d postgres")
            
            if self.results["redis"]["status"] != "✅":
                print("   • Start Redis: docker-compose up -d redis")
            
            if self.results["data_flow"]["status"] != "✅":
                print("   • Run producer: docker-compose up kafka_producer")
                print("   • Run consumer: docker-compose up kafka_consumer")
            
            print()
    
    def run_all_checks(self):
        """Run all diagnostic checks"""
        print("\n" + "="*70)
        print("  🔧 PIPELINE DIAGNOSTIC TOOL")
        print("  Testing: Kafka → PostgreSQL → Redis Data Flow")
        print("="*70)
        
        # Run checks
        self.check_kafka()
        self.check_postgres()
        self.check_redis()
        self.check_data_flow()
        
        # Print summary
        self.print_summary()
        
        # Return exit code
        all_passed = all(
            result["status"] == "✅" 
            for result in self.results.values()
        )
        return 0 if all_passed else 1


def main():
    """Main entry point"""
    diagnostics = PipelineDiagnostics()
    exit_code = diagnostics.run_all_checks()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
