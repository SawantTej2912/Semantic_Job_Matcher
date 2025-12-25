"""
Vector search service for semantic job search using embeddings.
"""
import numpy as np
from typing import List, Dict, Tuple
import json
import psycopg2
import os

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


def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    Calculate cosine similarity between two vectors.
    
    Args:
        vec1: First vector
        vec2: Second vector
        
    Returns:
        Similarity score between 0 and 1
    """
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return float(dot_product / (norm1 * norm2))


def get_all_job_embeddings() -> List[Dict]:
    """
    Retrieve all jobs with valid 768-dimensional embeddings.
    
    Returns:
        List of job dictionaries with embeddings
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT id, company, position, location, url, skills, 
                   seniority, summary, description, embedding
            FROM jobs_enriched
            WHERE embedding IS NOT NULL
            ORDER BY created_at DESC
        """)
        
        rows = cursor.fetchall()
        
        jobs = []
        for row in rows:
            # Parse embedding
            embedding_str = row[9]
            try:
                embedding = json.loads(embedding_str) if embedding_str else []
            except:
                embedding = []
            
            # Only include jobs with valid 768-dim embeddings
            if len(embedding) == 768:
                job = {
                    'id': row[0],
                    'company': row[1],
                    'position': row[2],
                    'location': row[3],
                    'url': row[4],
                    'skills': row[5] if row[5] else [],
                    'seniority': row[6],
                    'summary': row[7],
                    'description': row[8],
                    'embedding': np.array(embedding, dtype=np.float32)
                }
                jobs.append(job)
        
        return jobs
        
    finally:
        cursor.close()
        conn.close()


def search_similar_jobs(
    query_embedding: List[float],
    limit: int = 10,
    min_similarity: float = 0.0,
    filters: Dict = None
) -> List[Dict]:
    """
    Search for jobs similar to the query embedding.
    
    Args:
        query_embedding: Query vector (768 dimensions)
        limit: Maximum number of results to return
        min_similarity: Minimum similarity threshold (0-1)
        filters: Optional filters (seniority, skills, etc.)
        
    Returns:
        List of matching jobs with similarity scores
    """
    # Get all jobs with embeddings
    all_jobs = get_all_job_embeddings()
    
    if not all_jobs:
        return []
    
    # Convert query to numpy array
    query_vec = np.array(query_embedding, dtype=np.float32)
    
    # Calculate similarities
    results = []
    for job in all_jobs:
        # Apply filters if provided
        if filters:
            if 'seniority' in filters and job['seniority'] != filters['seniority']:
                continue
            if 'skills' in filters:
                required_skills = set(s.lower() for s in filters['skills'])
                job_skills = set(s.lower() for s in job['skills'])
                if not required_skills.intersection(job_skills):
                    continue
        
        # Calculate similarity
        similarity = cosine_similarity(query_vec, job['embedding'])
        
        # Apply threshold
        if similarity >= min_similarity:
            # Remove embedding from result (too large to return)
            result_job = {k: v for k, v in job.items() if k != 'embedding'}
            result_job['similarity'] = round(similarity, 4)
            results.append(result_job)
    
    # Sort by similarity (highest first)
    results.sort(key=lambda x: x['similarity'], reverse=True)
    
    # Return top N results
    return results[:limit]


def get_job_by_id(job_id: str) -> Dict:
    """
    Retrieve a specific job by ID.
    
    Args:
        job_id: Job ID to retrieve
        
    Returns:
        Job dictionary or None if not found
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT id, company, position, location, url, skills, 
                   seniority, summary, description, embedding
            FROM jobs_enriched
            WHERE id = %s
        """, (job_id,))
        
        row = cursor.fetchone()
        
        if not row:
            return None
        
        # Parse embedding
        embedding_str = row[9]
        try:
            embedding = json.loads(embedding_str) if embedding_str else []
        except:
            embedding = []
        
        job = {
            'id': row[0],
            'company': row[1],
            'position': row[2],
            'location': row[3],
            'url': row[4],
            'skills': row[5] if row[5] else [],
            'seniority': row[6],
            'summary': row[7],
            'description': row[8],
            'embedding': embedding
        }
        
        return job
        
    finally:
        cursor.close()
        conn.close()


def find_similar_to_job(job_id: str, limit: int = 5) -> List[Dict]:
    """
    Find jobs similar to a specific job.
    
    Args:
        job_id: ID of the reference job
        limit: Maximum number of results
        
    Returns:
        List of similar jobs with similarity scores
    """
    # Get the reference job
    reference_job = get_job_by_id(job_id)
    
    if not reference_job or not reference_job.get('embedding'):
        return []
    
    # Search using the job's embedding
    results = search_similar_jobs(
        query_embedding=reference_job['embedding'],
        limit=limit + 1,  # +1 because the job itself will be in results
        min_similarity=0.0
    )
    
    # Remove the reference job from results
    results = [r for r in results if r['id'] != job_id]
    
    return results[:limit]
