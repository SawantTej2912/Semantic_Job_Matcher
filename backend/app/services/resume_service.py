"""
Resume processing service with optimized PDF extraction and combined prompts.

Optimizations:
- Only extracts first 3 pages (where core skills are)
- Combines profile extraction and skill gap into single prompt
- Uses GeminiProvider with key rotation
- Uses gemini-2.5-flash-lite for higher rate limits (30 RPM)
"""
import os
import sys
import fitz  # PyMuPDF
import time
import json
from typing import List, Dict, Optional
import logging

# Add project root to path for services imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from services.kafka.gemini_provider import gemini_provider

# Configure logging
logger = logging.getLogger(__name__)

# Configuration
MAX_PAGES_TO_EXTRACT = 3  # Only extract first 3 pages for speed


class RateLimitExhaustedError(Exception):
    """Custom exception for when Gemini API rate limits are exhausted."""
    pass


def extract_text_from_pdf_bytes(pdf_bytes: bytes, max_pages: int = MAX_PAGES_TO_EXTRACT) -> str:
    """
    Extract text from PDF bytes using PyMuPDF memory stream (optimized).
    
    OPTIMIZATION: Only extracts first N pages where core skills typically are.
    
    Args:
        pdf_bytes: PDF file content as bytes
        max_pages: Maximum number of pages to extract (default: 3)
        
    Returns:
        Extracted text as a string
    """
    try:
        # Open PDF from memory stream - no temp file needed!
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = ""
        
        # Extract text from first N pages only (optimization)
        total_pages = len(doc)
        pages_to_extract = min(max_pages, total_pages)
        
        logger.info(f"📄 Extracting text from first {pages_to_extract} of {total_pages} pages...")
        
        for page_num in range(pages_to_extract):
            page = doc[page_num]
            text += page.get_text("text")  # Native text extraction for max speed
        
        doc.close()
        return text.strip()
        
    except Exception as e:
        raise Exception(f"Failed to extract text from PDF: {str(e)}")


def create_professional_profile(resume_text: str) -> Dict[str, any]:
    """
    Use Gemini to extract structured information from resume text.
    Uses gemini-2.5-flash-lite with key rotation.
    
    Args:
        resume_text: Raw text extracted from resume
        
    Returns:
        Dictionary with profile information
        
    Raises:
        RateLimitExhaustedError: If all keys are exhausted
    """
    if not gemini_provider:
        # Fallback if Gemini is not available
        return {
            "skills": [],
            "experience_years": 0,
            "summary": resume_text[:500],
            "key_strengths": [],
            "education": "Not specified",
            "job_titles": []
        }
    
    try:
        prompt = f"""Analyze the following resume and extract structured information.

Resume Text:
{resume_text}

Please provide a JSON object with the following fields:
1. "skills": A list of technical skills, tools, and technologies (max 20 items)
2. "experience_years": Estimated years of professional experience (integer)
3. "summary": A concise 3-sentence professional summary
4. "key_strengths": Top 5 key strengths or areas of expertise
5. "education": Highest degree and field of study
6. "job_titles": List of previous job titles (max 5)

Return ONLY valid JSON, no additional text or markdown formatting."""

        response_text = gemini_provider.generate_content(prompt, max_output_tokens=1500)
        
        # Remove markdown code blocks if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        # Parse JSON
        profile = json.loads(response_text)
        
        return profile
        
    except Exception as e:
        if "exhausted" in str(e).lower():
            raise RateLimitExhaustedError(str(e))
        
        logger.error(f"⚠️  Gemini profile extraction error: {e}")
        # Fallback to basic extraction
        return {
            "skills": [],
            "experience_years": 0,
            "summary": resume_text[:500],
            "key_strengths": [],
            "education": "Not specified",
            "job_titles": []
        }


def create_resume_embedding(resume_text: str, profile: Dict = None) -> List[float]:
    """
    Create a 768-dimensional embedding for the resume.
    Uses key rotation on rate limits.
    
    Args:
        resume_text: Raw resume text
        profile: Optional professional profile (if already extracted)
        
    Returns:
        768-dimensional embedding vector
        
    Raises:
        RateLimitExhaustedError: If all keys are exhausted
    """
    if not gemini_provider:
        # Fallback
        import hashlib
        import random
        hash_value = int(hashlib.md5(resume_text.encode()).hexdigest(), 16)
        random.seed(hash_value)
        return [random.random() for _ in range(768)]
    
    # Combine resume text with profile for better embedding
    if profile:
        enriched_text = f"""
Professional Summary: {profile.get('summary', '')}

Skills: {', '.join(profile.get('skills', []))}

Experience: {profile.get('experience_years', 0)} years

Key Strengths: {', '.join(profile.get('key_strengths', []))}

Education: {profile.get('education', '')}

Previous Roles: {', '.join(profile.get('job_titles', []))}

Full Resume:
{resume_text[:2000]}
"""
    else:
        enriched_text = resume_text
    
    try:
        return gemini_provider.embed_content(enriched_text)
    except Exception as e:
        if "exhausted" in str(e).lower():
            raise RateLimitExhaustedError(str(e))
        raise


def analyze_skill_gap_combined(resume_profile: Dict, jobs: List[Dict]) -> Dict[str, Dict]:
    """
    OPTIMIZATION: Analyze skill gaps for multiple jobs in a SINGLE prompt.
    This saves API calls by combining multiple analyses into one request.
    
    Args:
        resume_profile: Professional profile from resume
        jobs: List of job dictionaries (max 3)
        
    Returns:
        Dictionary mapping job_id to skill gap analysis
        
    Raises:
        RateLimitExhaustedError: If all keys are exhausted
    """
    if not gemini_provider or not jobs:
        return {}
    
    try:
        resume_skills = resume_profile.get('skills', [])
        resume_summary = resume_profile.get('summary', '')
        
        # Build combined prompt for all jobs
        jobs_text = ""
        for i, job in enumerate(jobs, 1):
            jobs_text += f"""
Job {i}:
- ID: {job.get('id', '')}
- Title: {job.get('position', '')}
- Company: {job.get('company', '')}
- Required Skills: {', '.join(job.get('skills', []))}
- Description: {job.get('description', '')[:300]}

"""
        
        prompt = f"""Analyze the skill gaps between this candidate and multiple job opportunities.

CANDIDATE PROFILE:
Skills: {', '.join(resume_skills)}
Summary: {resume_summary}

JOBS TO ANALYZE:
{jobs_text}

For EACH job, provide a JSON object with:
1. "job_id": The job ID
2. "missing_skills": Top 3 skills the candidate should learn
3. "matching_skills": Skills the candidate already has
4. "recommendations": 2-3 specific recommendations

Return a JSON array with one object per job. Return ONLY valid JSON, no additional text."""

        response_text = gemini_provider.generate_content(prompt, max_output_tokens=2000)
        
        # Remove markdown code blocks
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        # Parse JSON array
        analyses = json.loads(response_text)
        
        # Convert to dictionary keyed by job_id
        result = {}
        for analysis in analyses:
            job_id = analysis.get('job_id', '')
            if job_id:
                result[job_id] = {
                    "missing_skills": analysis.get('missing_skills', []),
                    "matching_skills": analysis.get('matching_skills', []),
                    "recommendations": analysis.get('recommendations', [])
                }
        
        return result
        
    except Exception as e:
        if "exhausted" in str(e).lower():
            raise RateLimitExhaustedError(str(e))
        
        logger.error(f"⚠️  Combined skill gap analysis error: {e}")
        # Fallback to simple comparison
        result = {}
        for job in jobs:
            resume_skills_set = set(s.lower() for s in resume_skills)
            job_skills_set = set(s.lower() for s in job.get('skills', []))
            
            missing = list(job_skills_set - resume_skills_set)[:3]
            matching = list(job_skills_set.intersection(resume_skills_set))
            
            result[job['id']] = {
                "missing_skills": missing,
                "matching_skills": matching,
                "recommendations": ["Develop skills in: " + ", ".join(missing)] if missing else []
            }
        
        return result


def process_resume(pdf_bytes: bytes) -> Dict[str, any]:
    """
    Complete resume processing pipeline with optimizations.
    
    Optimizations:
    - Only extracts first 3 pages (where core skills are)
    - Uses gemini-2.5-flash-lite (30 RPM free tier)
    - Key rotation on rate limits
    - Smart throttling between calls
    
    Args:
        pdf_bytes: PDF file content as bytes
        
    Returns:
        Dictionary with resume text, profile, and embedding
        
    Raises:
        RateLimitExhaustedError: If all API keys are exhausted
    """
    # Step 1: Extract text from PDF (OPTIMIZED - first 3 pages only)
    logger.info("📄 Extracting text from PDF (first 3 pages)...")
    resume_text = extract_text_from_pdf_bytes(pdf_bytes, max_pages=MAX_PAGES_TO_EXTRACT)
    
    if not resume_text or len(resume_text) < 50:
        raise Exception("Could not extract meaningful text from PDF")
    
    # Step 2: Create professional profile (with key rotation)
    logger.info("📝 Extracting professional profile...")
    profile = create_professional_profile(resume_text)
    
    # Step 3: Create embedding (with automatic throttling from provider)
    logger.info("🧮 Generating resume embedding...")
    embedding = create_resume_embedding(resume_text, profile)
    
    return {
        "text": resume_text,
        "profile": profile,
        "embedding": embedding,
        "embedding_dimension": len(embedding)
    }


def analyze_skill_gap(resume_profile: Dict, job: Dict) -> Dict[str, any]:
    """
    Backward compatibility wrapper for analyze_skill_gap_combined.
    Analyzes skill gap for a single job.
    
    Args:
        resume_profile: Professional profile from resume
        job: Job dictionary with skills and description
        
    Returns:
        Dictionary with skill gap analysis
    """
    # Call combined function with single job
    result = analyze_skill_gap_combined(resume_profile, [job])
    
    # Return the analysis for this job
    job_id = job.get('id', '')
    if job_id in result:
        return result[job_id]
    
    # Fallback to simple comparison
    resume_skills_set = set(s.lower() for s in resume_profile.get('skills', []))
    job_skills_set = set(s.lower() for s in job.get('skills', []))
    
    missing = list(job_skills_set - resume_skills_set)[:3]
    matching = list(job_skills_set.intersection(resume_skills_set))
    
    return {
        "missing_skills": missing,
        "matching_skills": matching,
        "recommendations": ["Develop skills in: " + ", ".join(missing)] if missing else []
    }
