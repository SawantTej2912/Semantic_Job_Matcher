"""
Pydantic models for search API.
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class SearchQuery(BaseModel):
    """Request model for semantic search."""
    query: str = Field(..., description="Search query text", min_length=1, max_length=500)
    limit: int = Field(10, description="Maximum number of results", ge=1, le=100)
    min_similarity: float = Field(0.5, description="Minimum similarity threshold", ge=0.0, le=1.0)
    seniority: Optional[str] = Field(None, description="Filter by seniority level")
    skills: Optional[List[str]] = Field(None, description="Filter by required skills")


class JobResult(BaseModel):
    """Job search result with similarity score."""
    id: str
    company: str
    position: str
    location: str
    url: str
    skills: List[str]
    seniority: str
    summary: str
    similarity: float = Field(..., description="Similarity score (0-1)")


class SearchResponse(BaseModel):
    """Response model for semantic search."""
    query: str
    results: List[JobResult]
    count: int
    processing_time_ms: float


class SimilarJobsQuery(BaseModel):
    """Request model for finding similar jobs."""
    job_id: str = Field(..., description="Reference job ID")
    limit: int = Field(5, description="Maximum number of results", ge=1, le=50)


class SimilarJobsResponse(BaseModel):
    """Response model for similar jobs."""
    reference_job_id: str
    results: List[JobResult]
    count: int
