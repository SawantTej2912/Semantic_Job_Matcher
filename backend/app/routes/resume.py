"""
Resume matching API routes with hardened error handling.

Script Type: PERMANENT SERVICE (API endpoints)
Purpose: HTTP interface for resume upload and job matching
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import time

from app.services.resume_service import (
    process_resume,
    analyze_skill_gap,
    analyze_skill_gap_combined,
    RateLimitExhaustedError
)
from app.services.vector_search import search_similar_jobs, get_job_by_id


router = APIRouter(prefix="/api/resume", tags=["resume"])


class ResumeProfile(BaseModel):
    """Professional profile extracted from resume."""
    skills: List[str]
    experience_years: int
    summary: str
    key_strengths: List[str]
    education: Optional[str] = None
    job_titles: Optional[List[str]] = None


class SkillGapAnalysis(BaseModel):
    """Skill gap analysis between resume and job."""
    missing_skills: List[str]
    matching_skills: List[str]
    recommendations: List[str]


class JobMatch(BaseModel):
    """Job match result with similarity and skill gap."""
    id: str
    company: str
    position: str
    location: str
    url: str
    skills: List[str]
    seniority: str
    summary: str
    similarity: float
    skill_gap: Optional[SkillGapAnalysis] = None


class ResumeMatchResponse(BaseModel):
    """Response for resume matching."""
    profile: ResumeProfile
    matches: List[JobMatch]
    total_matches: int
    processing_time_ms: float


@router.post("/match", response_model=ResumeMatchResponse)
async def match_resume_to_jobs(
    file: UploadFile = File(..., description="Resume PDF file"),
    limit: int = 5,
    min_similarity: float = 0.3,
    include_skill_gap: bool = True
):
    """
    Upload a resume PDF and get matched jobs with skill gap analysis.
    
    This endpoint includes hardened rate limit protection:
    - Exponential backoff retry (60s, 120s, 240s)
    - 2-second throttling between operations
    - Clear error messages (HTTP 429) when rate limits exhausted
    
    This endpoint:
    1. Extracts text from the PDF
    2. Uses Gemini to create a professional profile (with retry + backoff)
    3. Generates a 768-dim embedding (with retry + backoff)
    4. Finds similar jobs using cosine similarity
    5. Analyzes skill gaps for top matches (with throttling)
    
    Args:
        file: Resume PDF file
        limit: Maximum number of job matches to return (default: 5)
        min_similarity: Minimum similarity threshold 0-1 (default: 0.3)
        include_skill_gap: Whether to include skill gap analysis (default: True)
    
    Returns:
        Professional profile, matched jobs, and skill gap analysis
        
    Raises:
        400: Invalid file or empty file
        429: AI Analysis is busy (rate limits exhausted) - wait 60 seconds
        500: Other processing errors
    """
    start_time = time.time()
    
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are supported"
            )
        
        # Read PDF content
        pdf_bytes = await file.read()
        
        if len(pdf_bytes) == 0:
            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty"
            )
        
        # Process resume (with exponential backoff retry)
        try:
            resume_data = process_resume(pdf_bytes)
        except RateLimitExhaustedError as e:
            # Return clear 429 error
            raise HTTPException(
                status_code=429,
                detail=str(e)
            )
        
        # Get profile and embedding
        profile = resume_data['profile']
        embedding = resume_data['embedding']
        
        # Validate embedding
        if not embedding or len(embedding) != 768:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate resume embedding"
            )
        
        # Search for matching jobs
        job_matches = search_similar_jobs(
            query_embedding=embedding,
            limit=limit,
            min_similarity=min_similarity
        )
        
        # Add skill gap analysis for top matches (with throttling)
        matches_with_gap = []
        for i, job in enumerate(job_matches):
            job_match = JobMatch(**job)
            
            # Add skill gap analysis for top 3 matches
            if include_skill_gap and i < 3:
                try:
                    # Get full job details for skill gap analysis
                    full_job = get_job_by_id(job['id'])
                    if full_job:
                        gap_analysis = analyze_skill_gap(profile, full_job)
                        job_match.skill_gap = SkillGapAnalysis(**gap_analysis)
                except RateLimitExhaustedError as e:
                    # Return clear 429 error
                    raise HTTPException(
                        status_code=429,
                        detail=str(e)
                    )
                except Exception as e:
                    # Skip skill gap for this job if other error
                    print(f"⚠️  Skipping skill gap for job {job['id']}: {e}")
            
            matches_with_gap.append(job_match)
        
        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000
        
        return ResumeMatchResponse(
            profile=ResumeProfile(**profile),
            matches=matches_with_gap,
            total_matches=len(matches_with_gap),
            processing_time_ms=round(processing_time, 2)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Resume processing failed: {str(e)}"
        )


@router.post("/analyze")
async def analyze_resume(
    file: UploadFile = File(..., description="Resume PDF file")
):
    """
    Analyze a resume and extract professional profile without job matching.
    
    Useful for profile extraction only.
    """
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are supported"
            )
        
        # Read PDF content
        pdf_bytes = await file.read()
        
        # Process resume
        try:
            resume_data = process_resume(pdf_bytes)
        except RateLimitExhaustedError as e:
            raise HTTPException(
                status_code=429,
                detail=str(e)
            )
        
        return {
            "profile": resume_data['profile'],
            "text_length": len(resume_data['text']),
            "embedding_dimension": resume_data['embedding_dimension']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Resume analysis failed: {str(e)}"
        )


@router.post("/skill-gap/{job_id}")
async def get_skill_gap(
    job_id: str,
    file: UploadFile = File(..., description="Resume PDF file")
):
    """
    Analyze skill gap between a resume and a specific job.
    
    Args:
        job_id: ID of the job to compare against
        file: Resume PDF file
    """
    try:
        # Validate file
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are supported"
            )
        
        # Process resume
        pdf_bytes = await file.read()
        try:
            resume_data = process_resume(pdf_bytes)
        except RateLimitExhaustedError as e:
            raise HTTPException(
                status_code=429,
                detail=str(e)
            )
        
        profile = resume_data['profile']
        
        # Get job
        job = get_job_by_id(job_id)
        if not job:
            raise HTTPException(
                status_code=404,
                detail=f"Job with ID '{job_id}' not found"
            )
        
        # Analyze skill gap
        try:
            gap_analysis = analyze_skill_gap(profile, job)
        except RateLimitExhaustedError as e:
            raise HTTPException(
                status_code=429,
                detail=str(e)
            )
        
        return {
            "job": {
                "id": job['id'],
                "position": job['position'],
                "company": job['company'],
                "required_skills": job['skills']
            },
            "candidate": {
                "skills": profile['skills'],
                "experience_years": profile['experience_years']
            },
            "skill_gap": gap_analysis
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Skill gap analysis failed: {str(e)}"
        )
