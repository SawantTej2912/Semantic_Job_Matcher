#!/usr/bin/env python3
"""
Backfill script to re-enrich jobs with placeholder embeddings using Gemini API.

This script:
1. Identifies jobs with placeholder embeddings (384 dim or sequential values)
2. Re-enriches them using Gemini API
3. Updates the database with real embeddings and enrichment data
"""
import os
import sys
import json
import time
import psycopg2
from typing import List, Dict, Tuple

# Add services to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.kafka.enrichment import enrich_job_with_gemini, get_gemini_embedding

# Database connection parameters
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
POSTGRES_DB = os.getenv('POSTGRES_DB', 'jobs')
POSTGRES_USER = os.getenv('POSTGRES_USER', 'user')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'pass')
POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')

# Gemini API key
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')


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


def is_placeholder_embedding(embedding: List[float]) -> bool:
    """
    Determine if an embedding is a placeholder.
    
    Placeholder embeddings have:
    - 384 dimensions (not 768)
    - Sequential values (e.g., 0.414, 0.415, 0.416...)
    
    Args:
        embedding: List of embedding values
        
    Returns:
        True if placeholder, False if real Gemini embedding
    """
    if not embedding or len(embedding) == 0:
        return True
    
    # Check dimension
    if len(embedding) != 768:
        return True
    
    # Check if values are sequential (placeholder pattern)
    if len(embedding) >= 5:
        first_five = embedding[:5]
        diffs = [abs(first_five[i+1] - first_five[i]) for i in range(4)]
        avg_diff = sum(diffs) / len(diffs)
        
        # If differences are very small and consistent, it's likely a placeholder
        if avg_diff < 0.002:
            return True
    
    return False


def get_placeholder_jobs() -> List[Dict]:
    """
    Retrieve all jobs with placeholder embeddings from the database.
    
    Returns:
        List of job dictionaries with placeholder embeddings
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT id, company, position, location, url, tags, description, embedding, created_at
            FROM jobs_enriched
            ORDER BY created_at DESC
        """)
        
        rows = cursor.fetchall()
        
        placeholder_jobs = []
        for row in rows:
            # Parse embedding
            embedding_str = row[7]
            try:
                embedding = json.loads(embedding_str) if embedding_str else []
            except:
                embedding = []
            
            # Check if placeholder
            if is_placeholder_embedding(embedding):
                job = {
                    'id': row[0],
                    'company': row[1],
                    'position': row[2],
                    'location': row[3],
                    'url': row[4],
                    'tags': row[5] if row[5] else [],
                    'description': row[6],
                    'embedding': embedding,
                    'created_at': row[8].isoformat() if row[8] else None
                }
                placeholder_jobs.append(job)
        
        return placeholder_jobs
        
    finally:
        cursor.close()
        conn.close()


def update_job_enrichment(job_id: str, enriched_data: Dict) -> bool:
    """
    Update a job in the database with new enrichment data.
    
    Args:
        job_id: Job ID to update
        enriched_data: Dictionary with skills, seniority, summary, embedding
        
    Returns:
        True if successful, False otherwise
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Convert embedding to JSON string
        embedding_json = json.dumps(enriched_data.get('embedding', []))
        
        cursor.execute("""
            UPDATE jobs_enriched
            SET skills = %s,
                seniority = %s,
                summary = %s,
                embedding = %s,
                created_at = NOW()
            WHERE id = %s
        """, (
            enriched_data.get('skills', []),
            enriched_data.get('seniority', 'Mid'),
            enriched_data.get('summary', ''),
            embedding_json,
            job_id
        ))
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"❌ Error updating job {job_id}: {e}")
        conn.rollback()
        return False
        
    finally:
        cursor.close()
        conn.close()


def backfill_enrichments(batch_size: int = 10, delay_seconds: float = 2.0):
    """
    Main backfill function to re-enrich placeholder jobs.
    
    Args:
        batch_size: Number of jobs to process before showing progress
        delay_seconds: Delay between API calls to avoid rate limits
    """
    print_section("🔄 GEMINI ENRICHMENT BACKFILL")
    
    # Check API key
    if not GEMINI_API_KEY:
        print("\n❌ GEMINI_API_KEY is not set!")
        print("   Please set it: export GEMINI_API_KEY='your-key'")
        return
    
    print(f"\n✅ GEMINI_API_KEY is set (length: {len(GEMINI_API_KEY)})")
    print(f"📊 Batch size: {batch_size}")
    print(f"⏱️  Delay between jobs: {delay_seconds}s")
    print()
    
    # Get placeholder jobs
    print("🔍 Identifying jobs with placeholder embeddings...")
    placeholder_jobs = get_placeholder_jobs()
    
    if not placeholder_jobs:
        print("\n✅ No placeholder jobs found! All jobs have real embeddings.")
        return
    
    total_jobs = len(placeholder_jobs)
    print(f"\n📋 Found {total_jobs} jobs with placeholder embeddings")
    print()
    
    # Ask for confirmation
    print(f"⚠️  This will re-enrich {total_jobs} jobs using Gemini API.")
    print(f"   Estimated time: ~{(total_jobs * delay_seconds) / 60:.1f} minutes")
    print(f"   API calls: {total_jobs * 2} (enrichment + embedding)")
    print()
    
    response = input("Continue? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("\n❌ Backfill cancelled")
        return
    
    print()
    print_section("🚀 STARTING BACKFILL")
    
    # Process jobs
    successful = 0
    failed = 0
    skipped = 0
    
    start_time = time.time()
    
    for i, job in enumerate(placeholder_jobs, 1):
        job_id = job['id']
        position = job['position']
        company = job['company']
        description = job.get('description', '')
        
        print(f"\n[{i}/{total_jobs}] Processing: {position} at {company}")
        print(f"   Job ID: {job_id}")
        
        # Skip if no description
        if not description or len(description.strip()) < 10:
            print(f"   ⚠️  Skipping - no description")
            skipped += 1
            continue
        
        try:
            # Enrich with Gemini
            print(f"   🤖 Calling Gemini for enrichment...")
            gemini_result = enrich_job_with_gemini(description, position)
            
            # Generate embedding
            print(f"   🧮 Generating embedding...")
            full_text = f"{position}. {description}"
            embedding = get_gemini_embedding(full_text)
            
            # Check if we got real data
            if is_placeholder_embedding(embedding):
                print(f"   ⚠️  Warning: Still got placeholder embedding (Gemini may have failed)")
                # Continue anyway to update skills/summary
            
            # Prepare enriched data
            enriched_data = {
                'skills': gemini_result['skills'],
                'seniority': gemini_result['seniority'],
                'summary': gemini_result['summary'],
                'embedding': embedding
            }
            
            # Update database
            print(f"   💾 Updating database...")
            if update_job_enrichment(job_id, enriched_data):
                successful += 1
                print(f"   ✅ Success!")
                print(f"      Skills: {len(enriched_data['skills'])} found")
                print(f"      Seniority: {enriched_data['seniority']}")
                print(f"      Embedding: {len(embedding)} dimensions")
            else:
                failed += 1
                print(f"   ❌ Failed to update database")
            
            # Progress update
            if i % batch_size == 0:
                elapsed = time.time() - start_time
                rate = i / elapsed
                remaining = (total_jobs - i) / rate if rate > 0 else 0
                
                print()
                print(f"   📊 Progress: {i}/{total_jobs} ({i/total_jobs*100:.1f}%)")
                print(f"   ⏱️  Elapsed: {elapsed/60:.1f}m | Remaining: ~{remaining/60:.1f}m")
                print(f"   ✅ Successful: {successful} | ❌ Failed: {failed} | ⚠️  Skipped: {skipped}")
            
            # Delay to avoid rate limits
            if i < total_jobs:
                time.sleep(delay_seconds)
                
        except KeyboardInterrupt:
            print("\n\n⚠️  Backfill interrupted by user")
            print(f"   Processed: {i}/{total_jobs}")
            print(f"   Successful: {successful} | Failed: {failed} | Skipped: {skipped}")
            break
            
        except Exception as e:
            failed += 1
            print(f"   ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            # Continue with next job
            continue
    
    # Final summary
    elapsed_total = time.time() - start_time
    
    print()
    print_section("📊 BACKFILL COMPLETE")
    
    print(f"\n✅ Successfully enriched: {successful}/{total_jobs}")
    print(f"❌ Failed: {failed}/{total_jobs}")
    print(f"⚠️  Skipped (no description): {skipped}/{total_jobs}")
    print(f"⏱️  Total time: {elapsed_total/60:.1f} minutes")
    print(f"⚡ Average rate: {successful/elapsed_total*60:.1f} jobs/minute")
    
    if successful > 0:
        print(f"\n🎉 {successful} jobs now have real Gemini embeddings!")
        print(f"\nVerify results:")
        print(f"   python3 verify_thinking.py")
        print(f"   python3 view_embeddings.py")
    
    print_separator()


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Backfill placeholder embeddings with real Gemini enrichment'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=10,
        help='Number of jobs to process before showing progress (default: 10)'
    )
    parser.add_argument(
        '--delay',
        type=float,
        default=2.0,
        help='Delay in seconds between API calls (default: 2.0)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be processed without actually doing it'
    )
    
    args = parser.parse_args()
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - No changes will be made\n")
        placeholder_jobs = get_placeholder_jobs()
        print(f"Found {len(placeholder_jobs)} jobs with placeholder embeddings:")
        for i, job in enumerate(placeholder_jobs[:10], 1):
            print(f"  {i}. {job['position']} at {job['company']} (ID: {job['id']})")
        if len(placeholder_jobs) > 10:
            print(f"  ... and {len(placeholder_jobs) - 10} more")
        print(f"\nRun without --dry-run to process these jobs")
    else:
        backfill_enrichments(
            batch_size=args.batch_size,
            delay_seconds=args.delay
        )


if __name__ == "__main__":
    main()
