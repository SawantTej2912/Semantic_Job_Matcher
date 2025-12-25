"""
PostgreSQL database helper module for storing enriched jobs.
"""
import os
import json
import psycopg2
from psycopg2.extras import execute_values
from typing import Dict, List


# Database connection parameters from environment
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'postgres')
POSTGRES_DB = os.getenv('POSTGRES_DB', 'jobs')
POSTGRES_USER = os.getenv('POSTGRES_USER', 'user')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'pass')
POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')


def get_connection():
    """
    Create and return a PostgreSQL database connection.
    
    Returns:
        psycopg2 connection object.
    """
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
        print(f"Error connecting to PostgreSQL: {e}")
        raise


def create_tables():
    """
    Create the jobs_enriched table if it doesn't exist.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Create jobs_enriched table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs_enriched (
                id TEXT PRIMARY KEY,
                company TEXT,
                position TEXT,
                location TEXT,
                url TEXT,
                tags TEXT[],
                skills TEXT[],
                seniority TEXT,
                summary TEXT,
                description TEXT,
                embedding TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Create index on company and position for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_company ON jobs_enriched(company)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_position ON jobs_enriched(position)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_seniority ON jobs_enriched(seniority)
        """)
        
        conn.commit()
        print("Tables created successfully")
        
    except Exception as e:
        print(f"Error creating tables: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def insert_enriched_job(job: Dict):
    """
    Insert an enriched job into the database.
    
    Args:
        job: Enriched job dictionary.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Convert embedding list to JSON string for storage
        embedding_json = json.dumps(job.get('embedding', []))
        
        # Convert tags and skills lists to PostgreSQL arrays
        tags = job.get('tags', [])
        skills = job.get('skills', [])
        
        cursor.execute("""
            INSERT INTO jobs_enriched 
            (id, company, position, location, url, tags, skills, seniority, summary, description, embedding)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                company = EXCLUDED.company,
                position = EXCLUDED.position,
                location = EXCLUDED.location,
                url = EXCLUDED.url,
                tags = EXCLUDED.tags,
                skills = EXCLUDED.skills,
                seniority = EXCLUDED.seniority,
                summary = EXCLUDED.summary,
                description = EXCLUDED.description,
                embedding = EXCLUDED.embedding,
                created_at = NOW()
        """, (
            job.get('id'),
            job.get('company'),
            job.get('position'),
            job.get('location'),
            job.get('url'),
            tags,
            skills,
            job.get('seniority'),
            job.get('summary'),
            job.get('description'),
            embedding_json
        ))
        
        conn.commit()
        print(f"Inserted/Updated job: {job.get('id')} - {job.get('position')} at {job.get('company')}")
        
    except Exception as e:
        print(f"Error inserting job: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def get_all_jobs(limit: int = 100) -> List[Dict]:
    """
    Retrieve all enriched jobs from the database.
    
    Args:
        limit: Maximum number of jobs to retrieve.
        
    Returns:
        List of job dictionaries.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT id, company, position, location, url, tags, skills, 
                   seniority, summary, description, created_at
            FROM jobs_enriched
            ORDER BY created_at DESC
            LIMIT %s
        """, (limit,))
        
        rows = cursor.fetchall()
        
        jobs = []
        for row in rows:
            job = {
                'id': row[0],
                'company': row[1],
                'position': row[2],
                'location': row[3],
                'url': row[4],
                'tags': row[5],
                'skills': row[6],
                'seniority': row[7],
                'summary': row[8],
                'description': row[9],
                'created_at': row[10].isoformat() if row[10] else None
            }
            jobs.append(job)
        
        return jobs
        
    except Exception as e:
        print(f"Error retrieving jobs: {e}")
        raise
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    # Test database connection and table creation
    print("Testing PostgreSQL connection...")
    create_tables()
    print("Database setup complete!")
