"""
Search API routes for semantic job search.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List
import time
import sys
import os

# Add project root to path for services imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.models.search import (
    SearchQuery,
    SearchResponse,
    JobResult,
    SimilarJobsQuery,
    SimilarJobsResponse
)
from app.services.vector_search import (
    search_similar_jobs,
    find_similar_to_job,
    get_job_by_id
)
from services.kafka.enrichment import get_gemini_embedding


router = APIRouter(prefix="/api/search", tags=["search"])


@router.post("/semantic", response_model=SearchResponse)
async def semantic_search(query: SearchQuery):
    """
    Semantic job search using natural language queries.
    
    Converts the query to an embedding and finds similar jobs.
    
    Example queries:
    - "Python machine learning engineer"
    - "Senior DevOps with Kubernetes experience"
    - "Remote frontend developer React"
    """
    start_time = time.time()
    
    try:
        # Convert query to embedding using Gemini
        query_embedding = get_gemini_embedding(query.query)
        
        # Check if embedding is valid
        if not query_embedding or len(query_embedding) != 768:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate query embedding"
            )
        
        # Prepare filters
        filters = {}
        if query.seniority:
            filters['seniority'] = query.seniority
        if query.skills:
            filters['skills'] = query.skills
        
        # Search for similar jobs
        results = search_similar_jobs(
            query_embedding=query_embedding,
            limit=query.limit,
            min_similarity=query.min_similarity,
            filters=filters if filters else None
        )
        
        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000  # Convert to ms
        
        return SearchResponse(
            query=query.query,
            results=[JobResult(**job) for job in results],
            count=len(results),
            processing_time_ms=round(processing_time, 2)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )


@router.post("/similar", response_model=SimilarJobsResponse)
async def find_similar_jobs(query: SimilarJobsQuery):
    """
    Find jobs similar to a specific job.
    
    Useful for "More jobs like this" functionality.
    """
    try:
        # Find similar jobs
        results = find_similar_to_job(
            job_id=query.job_id,
            limit=query.limit
        )
        
        if not results and not get_job_by_id(query.job_id):
            raise HTTPException(
                status_code=404,
                detail=f"Job with ID '{query.job_id}' not found"
            )
        
        return SimilarJobsResponse(
            reference_job_id=query.job_id,
            results=[JobResult(**job) for job in results],
            count=len(results)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to find similar jobs: {str(e)}"
        )


@router.get("/job/{job_id}")
async def get_job(job_id: str):
    """
    Get a specific job by ID.
    
    Returns full job details including description.
    """
    try:
        job = get_job_by_id(job_id)
        
        if not job:
            raise HTTPException(
                status_code=404,
                detail=f"Job with ID '{job_id}' not found"
            )
        
        # Remove embedding from response (too large)
        if 'embedding' in job:
            del job['embedding']
        
        return job
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve job: {str(e)}"
        )


@router.get("/stats")
async def get_search_stats():
    """
    Get statistics about the search index.
    
    Returns information about available jobs and embeddings.
    """
    try:
        from app.services.vector_search import get_all_job_embeddings
        
        jobs = get_all_job_embeddings()
        
        # Calculate statistics
        seniority_counts = {}
        total_skills = set()
        
        for job in jobs:
            # Count seniority levels
            seniority = job.get('seniority', 'Unknown')
            seniority_counts[seniority] = seniority_counts.get(seniority, 0) + 1
            
            # Collect unique skills
            for skill in job.get('skills', []):
                total_skills.add(skill.lower())
        
        return {
            "total_jobs": len(jobs),
            "jobs_with_embeddings": len(jobs),
            "embedding_dimension": 768,
            "seniority_distribution": seniority_counts,
            "unique_skills": len(total_skills),
            "top_skills": sorted(list(total_skills))[:20]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get stats: {str(e)}"
        )
