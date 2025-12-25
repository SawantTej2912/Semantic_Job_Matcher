#!/usr/bin/env python3
"""
Interactive embedding viewer - explore embeddings stored in PostgreSQL.
"""
import os
import json
import psycopg2
import numpy as np
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


def get_all_embeddings() -> List[Dict]:
    """Retrieve all jobs with embeddings from the database."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT id, company, position, seniority, skills, embedding, created_at
            FROM jobs_enriched
            ORDER BY created_at DESC
        """)
        
        rows = cursor.fetchall()
        
        jobs = []
        for row in rows:
            # Parse embedding JSON string back to list
            embedding_str = row[5]
            try:
                embedding = json.loads(embedding_str) if embedding_str else []
            except:
                embedding = []
            
            job = {
                'id': row[0],
                'company': row[1],
                'position': row[2],
                'seniority': row[3],
                'skills': row[4] if row[4] else [],
                'embedding': embedding,
                'created_at': row[6].isoformat() if row[6] else None
            }
            jobs.append(job)
        
        return jobs
        
    finally:
        cursor.close()
        conn.close()


def calculate_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0
    
    vec1_np = np.array(vec1)
    vec2_np = np.array(vec2)
    
    # Cosine similarity
    dot_product = np.dot(vec1_np, vec2_np)
    norm1 = np.linalg.norm(vec1_np)
    norm2 = np.linalg.norm(vec2_np)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return dot_product / (norm1 * norm2)


def view_embeddings():
    """Main function to view and explore embeddings."""
    print_section("🔍 EMBEDDING VIEWER")
    
    print(f"\nConnecting to PostgreSQL at {POSTGRES_HOST}:{POSTGRES_PORT}...")
    print(f"Database: {POSTGRES_DB}\n")
    
    # Get all jobs with embeddings
    jobs = get_all_embeddings()
    
    if not jobs:
        print("⚠️  No jobs found in the database.")
        return
    
    # Filter jobs with valid embeddings
    jobs_with_embeddings = [j for j in jobs if j['embedding'] and len(j['embedding']) > 0]
    real_embeddings = [j for j in jobs_with_embeddings if len(j['embedding']) == 768]
    
    print(f"📊 Database Statistics:")
    print(f"   Total jobs: {len(jobs)}")
    print(f"   Jobs with embeddings: {len(jobs_with_embeddings)}")
    print(f"   Jobs with 768-dim embeddings: {len(real_embeddings)}")
    print()
    
    # Display all embeddings
    print_section("📋 ALL EMBEDDINGS")
    
    for i, job in enumerate(jobs_with_embeddings, 1):
        embedding = job['embedding']
        is_real = len(embedding) == 768
        
        print(f"\n{i}. {job['position']} at {job['company']}")
        print(f"   Job ID: {job['id']}")
        print(f"   Seniority: {job['seniority']}")
        print(f"   Skills: {', '.join(job['skills'][:5])}{'...' if len(job['skills']) > 5 else ''}")
        print(f"   Embedding dimension: {len(embedding)}")
        print(f"   Type: {'✅ Real Gemini' if is_real else '⚠️  Placeholder'}")
        print(f"   First 10 values: {embedding[:10]}")
        
        if is_real:
            # Calculate statistics for real embeddings
            embedding_np = np.array(embedding)
            print(f"   Statistics:")
            print(f"      Mean: {np.mean(embedding_np):.6f}")
            print(f"      Std Dev: {np.std(embedding_np):.6f}")
            print(f"      Min: {np.min(embedding_np):.6f}")
            print(f"      Max: {np.max(embedding_np):.6f}")
        
        print(f"   Created: {job['created_at']}")
    
    # Calculate similarity between real embeddings
    if len(real_embeddings) >= 2:
        print_section("🔗 EMBEDDING SIMILARITIES")
        print("\nCosine similarity between jobs (1.0 = identical, 0.0 = unrelated):\n")
        
        for i in range(min(3, len(real_embeddings))):
            for j in range(i + 1, min(3, len(real_embeddings))):
                job1 = real_embeddings[i]
                job2 = real_embeddings[j]
                
                similarity = calculate_similarity(job1['embedding'], job2['embedding'])
                
                print(f"📊 {job1['position'][:40]}")
                print(f"   vs")
                print(f"   {job2['position'][:40]}")
                print(f"   Similarity: {similarity:.4f} {'🔥' if similarity > 0.8 else '✅' if similarity > 0.5 else '📉'}")
                print()
    
    # Export option
    print_section("💾 EXPORT OPTIONS")
    print("\nYou can export embeddings to:")
    print("  1. JSON file: python3 export_embeddings.py")
    print("  2. NumPy array: python3 export_embeddings.py --format numpy")
    print("  3. CSV file: python3 export_embeddings.py --format csv")
    print()
    print("Or query directly from PostgreSQL:")
    print(f"  psql -h {POSTGRES_HOST} -U {POSTGRES_USER} -d {POSTGRES_DB}")
    print(f"  SELECT id, position, embedding FROM jobs_enriched;")
    print()
    
    print_separator()


if __name__ == "__main__":
    try:
        view_embeddings()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
