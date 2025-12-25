#!/usr/bin/env python3
"""
Verification script to check Gemini enrichment output in PostgreSQL.
Queries the jobs_enriched table and displays:
- Position
- Gemini-generated Summary
- First 5 values of the embedding vector
"""
import os
import json
import psycopg2
from typing import List, Dict

# Database connection parameters
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
POSTGRES_DB = os.getenv('POSTGRES_DB', 'jobs')
POSTGRES_USER = os.getenv('POSTGRES_USER', 'user')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'pass')
POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')


def print_separator(char="=", length=80):
    """Print a separator line."""
    print(char * length)


def print_section(title):
    """Print a section header."""
    print_separator()
    print(f"  {title}")
    print_separator()


def get_connection():
    """Create and return a PostgreSQL database connection."""
    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            database=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            port=POSTGRES_PORT
        )
        return conn
    except Exception as e:
        print(f"❌ Error connecting to PostgreSQL: {e}")
        raise


def get_latest_jobs(limit: int = 3) -> List[Dict]:
    """
    Retrieve the latest enriched jobs from the database.
    
    Args:
        limit: Number of jobs to retrieve.
        
    Returns:
        List of job dictionaries with enrichment data.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT id, company, position, location, skills, seniority, 
                   summary, embedding, created_at
            FROM jobs_enriched
            ORDER BY created_at DESC
            LIMIT %s
        """, (limit,))
        
        rows = cursor.fetchall()
        
        jobs = []
        for row in rows:
            # Parse embedding JSON string back to list
            embedding_str = row[7]
            try:
                embedding = json.loads(embedding_str) if embedding_str else []
            except:
                embedding = []
            
            job = {
                'id': row[0],
                'company': row[1],
                'position': row[2],
                'location': row[3],
                'skills': row[4] if row[4] else [],
                'seniority': row[5],
                'summary': row[6],
                'embedding': embedding,
                'created_at': row[8].isoformat() if row[8] else None
            }
            jobs.append(job)
        
        return jobs
        
    except Exception as e:
        print(f"❌ Error retrieving jobs: {e}")
        raise
    finally:
        cursor.close()
        conn.close()


def verify_gemini_output():
    """
    Main verification function that displays Gemini enrichment results.
    """
    print_section("🔍 GEMINI ENRICHMENT VERIFICATION")
    
    print(f"\nConnecting to PostgreSQL at {POSTGRES_HOST}:{POSTGRES_PORT}...")
    print(f"Database: {POSTGRES_DB}\n")
    
    try:
        # Get latest 3 jobs
        jobs = get_latest_jobs(limit=3)
        
        if not jobs:
            print("⚠️  No jobs found in the database.")
            print("\n💡 Tips:")
            print("   1. Make sure the consumer is running: docker-compose ps kafka_consumer")
            print("   2. Check consumer logs: docker-compose logs kafka_consumer")
            print("   3. Verify jobs were sent to Kafka: docker-compose logs kafka_producer")
            return
        
        print(f"✅ Found {len(jobs)} enriched job(s) in the database\n")
        
        # Display each job
        for i, job in enumerate(jobs, 1):
            print_separator("-")
            print(f"  JOB #{i}")
            print_separator("-")
            
            print(f"\n📋 Position: {job['position']}")
            print(f"🏢 Company: {job['company']}")
            print(f"📍 Location: {job['location'] or 'Not specified'}")
            print(f"🆔 Job ID: {job['id']}")
            
            print(f"\n🎯 Seniority Level: {job['seniority']}")
            
            print(f"\n💼 Skills ({len(job['skills'])} found):")
            if job['skills']:
                for skill in job['skills'][:10]:  # Show first 10 skills
                    print(f"   • {skill}")
                if len(job['skills']) > 10:
                    print(f"   ... and {len(job['skills']) - 10} more")
            else:
                print("   (No skills extracted)")
            
            print(f"\n📝 Gemini-Generated Summary:")
            summary = job['summary'] or "(No summary generated)"
            # Clean HTML tags if present
            import re
            summary_clean = re.sub(r'<[^>]+>', '', summary)
            # Wrap text at 80 characters
            words = summary_clean.split()
            lines = []
            current_line = "   "
            for word in words:
                if len(current_line) + len(word) + 1 <= 80:
                    current_line += word + " "
                else:
                    lines.append(current_line.rstrip())
                    current_line = "   " + word + " "
            if current_line.strip():
                lines.append(current_line.rstrip())
            
            for line in lines:
                print(line)
            
            print(f"\n🧮 Embedding Vector:")
            embedding = job['embedding']
            if embedding and len(embedding) > 0:
                print(f"   Dimension: {len(embedding)}")
                print(f"   First 5 values: {embedding[:5]}")
                print(f"   Type: {'✅ Real Gemini embedding' if len(embedding) == 768 else '⚠️  Unexpected dimension'}")
                
                # Check if it's a real embedding (not placeholder)
                if len(embedding) >= 5:
                    # Placeholder embeddings have sequential values like 0.414, 0.415, 0.416
                    # Real embeddings have varied values
                    first_five = embedding[:5]
                    diffs = [abs(first_five[i+1] - first_five[i]) for i in range(4)]
                    avg_diff = sum(diffs) / len(diffs)
                    
                    if avg_diff < 0.002:  # Very small differences = likely placeholder
                        print(f"   Status: ⚠️  Appears to be placeholder (sequential values)")
                    else:
                        print(f"   Status: ✅ Appears to be real Gemini embedding (varied values)")
            else:
                print("   ❌ No embedding vector found")
            
            print(f"\n⏰ Created: {job['created_at']}")
            print()
        
        # Summary statistics
        print_section("📊 VERIFICATION SUMMARY")
        
        total_jobs = len(jobs)
        jobs_with_skills = sum(1 for j in jobs if j['skills'])
        jobs_with_summary = sum(1 for j in jobs if j['summary'])
        jobs_with_embedding = sum(1 for j in jobs if j['embedding'] and len(j['embedding']) > 0)
        jobs_with_real_embedding = sum(1 for j in jobs if j['embedding'] and len(j['embedding']) == 768)
        
        print(f"\n✅ Total jobs verified: {total_jobs}")
        print(f"✅ Jobs with skills: {jobs_with_skills}/{total_jobs}")
        print(f"✅ Jobs with summary: {jobs_with_summary}/{total_jobs}")
        print(f"✅ Jobs with embedding: {jobs_with_embedding}/{total_jobs}")
        print(f"✅ Jobs with 768-dim embedding: {jobs_with_real_embedding}/{total_jobs}")
        
        if jobs_with_real_embedding == total_jobs and jobs_with_summary == total_jobs:
            print("\n🎉 SUCCESS! Gemini enrichment is working correctly!")
            print("   - LLM is generating summaries ✅")
            print("   - Embedding model is creating real vectors ✅")
        else:
            print("\n⚠️  Some jobs may not have complete enrichment data.")
            print("   Check the consumer logs for any errors.")
        
        print_separator()
        
    except Exception as e:
        print(f"\n❌ Error during verification: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    verify_gemini_output()
