#!/usr/bin/env python3
"""
Export embeddings from PostgreSQL to various formats.
"""
import os
import json
import csv
import argparse
import psycopg2
import numpy as np
from typing import List, Dict

# Database connection parameters
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
POSTGRES_DB = os.getenv('POSTGRES_DB', 'jobs')
POSTGRES_USER = os.getenv('POSTGRES_USER', 'user')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'pass')
POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')


def get_connection():
    """Create and return a PostgreSQL database connection."""
    conn = psycopg2.connect(
        host=POSTGRES_HOST,
        database=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        port=POSTGRES_PORT
    )
    return conn


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


def export_json(jobs: List[Dict], filename: str = "embeddings.json"):
    """Export embeddings to JSON file."""
    with open(filename, 'w') as f:
        json.dump(jobs, f, indent=2)
    print(f"✅ Exported {len(jobs)} jobs to {filename}")
    print(f"   File size: {os.path.getsize(filename) / 1024:.2f} KB")


def export_numpy(jobs: List[Dict], filename: str = "embeddings.npz"):
    """Export embeddings to NumPy compressed format."""
    # Filter jobs with valid embeddings
    valid_jobs = [j for j in jobs if j['embedding'] and len(j['embedding']) == 768]
    
    if not valid_jobs:
        print("⚠️  No valid 768-dimensional embeddings to export")
        return
    
    # Create arrays
    embeddings = np.array([j['embedding'] for j in valid_jobs])
    ids = np.array([j['id'] for j in valid_jobs])
    positions = np.array([j['position'] for j in valid_jobs])
    companies = np.array([j['company'] for j in valid_jobs])
    
    # Save to compressed NumPy format
    np.savez_compressed(
        filename,
        embeddings=embeddings,
        ids=ids,
        positions=positions,
        companies=companies
    )
    
    print(f"✅ Exported {len(valid_jobs)} embeddings to {filename}")
    print(f"   Shape: {embeddings.shape}")
    print(f"   File size: {os.path.getsize(filename) / 1024:.2f} KB")
    print(f"\nTo load:")
    print(f"   data = np.load('{filename}')")
    print(f"   embeddings = data['embeddings']")
    print(f"   ids = data['ids']")


def export_csv(jobs: List[Dict], filename: str = "embeddings.csv"):
    """Export embeddings metadata to CSV (embeddings as separate file)."""
    # Export metadata
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'company', 'position', 'seniority', 'skills', 'embedding_dim', 'created_at'])
        
        for job in jobs:
            writer.writerow([
                job['id'],
                job['company'],
                job['position'],
                job['seniority'],
                ','.join(job['skills']),
                len(job['embedding']) if job['embedding'] else 0,
                job['created_at']
            ])
    
    print(f"✅ Exported {len(jobs)} jobs metadata to {filename}")
    
    # Export embeddings as separate CSV
    embeddings_file = filename.replace('.csv', '_vectors.csv')
    valid_jobs = [j for j in jobs if j['embedding'] and len(j['embedding']) == 768]
    
    if valid_jobs:
        with open(embeddings_file, 'w', newline='') as f:
            writer = csv.writer(f)
            # Header: id + embedding dimensions
            writer.writerow(['id'] + [f'dim_{i}' for i in range(768)])
            
            for job in valid_jobs:
                writer.writerow([job['id']] + job['embedding'])
        
        print(f"✅ Exported {len(valid_jobs)} embedding vectors to {embeddings_file}")
        print(f"   File size: {os.path.getsize(embeddings_file) / 1024:.2f} KB")


def main():
    parser = argparse.ArgumentParser(description='Export embeddings from PostgreSQL')
    parser.add_argument(
        '--format',
        choices=['json', 'numpy', 'csv', 'all'],
        default='json',
        help='Export format (default: json)'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Output filename (optional)'
    )
    
    args = parser.parse_args()
    
    print("🔍 Fetching embeddings from PostgreSQL...")
    jobs = get_all_embeddings()
    
    if not jobs:
        print("⚠️  No jobs found in database")
        return
    
    print(f"✅ Found {len(jobs)} jobs\n")
    
    # Export based on format
    if args.format == 'json' or args.format == 'all':
        filename = args.output or 'embeddings.json'
        export_json(jobs, filename)
        print()
    
    if args.format == 'numpy' or args.format == 'all':
        filename = args.output or 'embeddings.npz'
        export_numpy(jobs, filename)
        print()
    
    if args.format == 'csv' or args.format == 'all':
        filename = args.output or 'embeddings.csv'
        export_csv(jobs, filename)
        print()
    
    print("✅ Export complete!")


if __name__ == "__main__":
    main()
