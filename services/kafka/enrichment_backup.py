"""
Job enrichment module using Gemini API for extracting skills, seniority, and generating summaries.
"""
import os
import json
import re
import time
from typing import List, Dict, Optional
import hashlib

# Gemini API imports
try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️  google-genai not installed. Using placeholder enrichment.")


# Rate limiting configuration
RATE_LIMIT_DELAY = 4  # Seconds between consecutive Gemini API calls
MAX_RETRIES = 3  # Maximum number of retries for 429 errors
RETRY_DELAY = 60  # Seconds to wait after 429 error

# Track last API call time for rate limiting
_last_api_call_time = 0


def _wait_for_rate_limit():
    """Ensure minimum delay between API calls to avoid rate limits."""
    global _last_api_call_time
    current_time = time.time()
    time_since_last_call = current_time - _last_api_call_time
    
    if time_since_last_call < RATE_LIMIT_DELAY:
        sleep_time = RATE_LIMIT_DELAY - time_since_last_call
        print(f"⏱️  Rate limiting: waiting {sleep_time:.1f}s before next API call...")
        time.sleep(sleep_time)
    
    _last_api_call_time = time.time()


# Initialize Gemini client
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
gemini_client = None

if GEMINI_AVAILABLE and GEMINI_API_KEY:
    try:
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
        print("✅ Gemini API client initialized successfully")
    except Exception as e:
        print(f"⚠️  Failed to initialize Gemini client: {e}")
        gemini_client = None
else:
    if not GEMINI_API_KEY:
        print("⚠️  GEMINI_API_KEY not set. Using placeholder enrichment.")


def enrich_job_with_gemini(description: str, position: str = "") -> Dict:
    """
    Use Gemini API to extract skills, seniority, and summary from job description.
    
    Args:
        description: Job description text.
        position: Job position/title.
        
    Returns:
        Dictionary containing:
        - skills: List of extracted skills
        - seniority: Seniority level (Junior, Mid, Senior, Lead)
        - summary: 2-sentence summary of the job
    """
    if not gemini_client:
        # Fallback to placeholder implementation
        return {
            "skills": extract_skills_placeholder(description),
            "seniority": extract_seniority_placeholder(description),
            "summary": summarize_job_placeholder(description)
        }
    
    try:
        # Create the prompt for Gemini
        prompt = f"""Analyze the following job posting and extract structured information.

Job Title: {position}

Job Description:
{description}

Please provide a JSON object with the following fields:
1. "skills": A list of technical skills, tools, and technologies mentioned (max 15 items)
2. "seniority": The seniority level - must be one of: "Junior", "Mid", "Senior", or "Lead"
3. "summary": A concise 2-sentence summary of the role and key requirements

Return ONLY valid JSON, no additional text or markdown formatting."""

        # Call Gemini API
        response = gemini_client.models.generate_content(
            model='models/gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,  # Lower temperature for more consistent output
                max_output_tokens=1000,
            )
        )
        
        # Extract the response text
        response_text = response.text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        # Parse JSON response
        result = json.loads(response_text)
        
        # Validate and normalize the response
        skills = result.get("skills", [])
        if isinstance(skills, str):
            skills = [s.strip() for s in skills.split(",")]
        
        seniority = result.get("seniority", "Mid")
        # Ensure seniority is one of the valid values
        valid_seniorities = ["Junior", "Mid", "Senior", "Lead"]
        if seniority not in valid_seniorities:
            # Try to map common variations
            seniority_lower = seniority.lower()
            if "junior" in seniority_lower or "entry" in seniority_lower:
                seniority = "Junior"
            elif "senior" in seniority_lower or "sr" in seniority_lower:
                seniority = "Senior"
            elif "lead" in seniority_lower or "principal" in seniority_lower or "staff" in seniority_lower:
                seniority = "Lead"
            else:
                seniority = "Mid"
        
        summary = result.get("summary", "")
        
        return {
            "skills": skills[:15],  # Limit to 15 skills
            "seniority": seniority,
            "summary": summary
        }
        
    except json.JSONDecodeError as e:
        print(f"⚠️  Gemini returned invalid JSON: {e}")
        print(f"Response: {response_text[:200]}")
        # Fallback to placeholder
        return {
            "skills": extract_skills_placeholder(description),
            "seniority": extract_seniority_placeholder(description),
            "summary": summarize_job_placeholder(description)
        }
    except Exception as e:
        print(f"⚠️  Gemini API error: {e}")
        # Fallback to placeholder
        return {
            "skills": extract_skills_placeholder(description),
            "seniority": extract_seniority_placeholder(description),
            "summary": summarize_job_placeholder(description)
        }


def get_gemini_embedding(text: str) -> List[float]:
    """
    Generate embedding vector using Gemini's text-embedding-004 model.
    
    Args:
        text: Text to generate embedding for.
        
    Returns:
        Embedding vector (list of floats).
    """
    if not gemini_client:
        # Fallback to placeholder embedding
        return generate_embedding_placeholder(text)
    
    try:
        # Call Gemini embeddings API
        result = gemini_client.models.embed_content(
            model='text-embedding-004',
            contents=text
        )
        
        # Extract embedding vector
        embedding = result.embeddings[0].values
        
        return list(embedding)
        
    except Exception as e:
        print(f"⚠️  Gemini embedding error: {e}")
        # Fallback to placeholder
        return generate_embedding_placeholder(text)


# Placeholder functions (fallback when Gemini is not available)

def extract_skills_placeholder(description: str) -> List[str]:
    """
    Extract skills from job description using simple keyword matching.
    Fallback when Gemini API is not available.
    """
    common_skills = [
        'python', 'javascript', 'react', 'node.js', 'sql', 'aws', 
        'docker', 'kubernetes', 'java', 'typescript', 'go', 'rust',
        'machine learning', 'data science', 'devops', 'ci/cd',
        'postgresql', 'mongodb', 'redis', 'kafka', 'git', 'linux',
        'api', 'rest', 'graphql', 'microservices', 'agile', 'scrum'
    ]
    
    description_lower = description.lower()
    found_skills = [skill for skill in common_skills if skill in description_lower]
    
    return found_skills[:15]


def extract_seniority_placeholder(description: str) -> str:
    """
    Extract seniority level using simple keyword matching.
    Fallback when Gemini API is not available.
    """
    description_lower = description.lower()
    
    if any(word in description_lower for word in ['senior', 'sr.', 'sr ', 'lead', 'principal', 'staff']):
        return 'Senior'
    elif any(word in description_lower for word in ['junior', 'jr.', 'jr ', 'entry', 'graduate', 'intern']):
        return 'Junior'
    elif any(word in description_lower for word in ['mid-level', 'intermediate', 'mid level']):
        return 'Mid'
    else:
        return 'Mid'  # Default


def summarize_job_placeholder(description: str) -> str:
    """
    Generate a simple summary by taking the first sentences.
    Fallback when Gemini API is not available.
    """
    # Try to extract first 2 sentences
    sentences = re.split(r'[.!?]+', description)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if len(sentences) >= 2:
        summary = '. '.join(sentences[:2]) + '.'
    elif len(sentences) == 1:
        summary = sentences[0] + '.'
    else:
        summary = description[:200] + "..." if len(description) > 200 else description
    
    # Limit length
    if len(summary) > 300:
        summary = summary[:297] + "..."
    
    return summary


def generate_embedding_placeholder(text: str) -> List[float]:
    """
    Generate a pseudo-embedding using hash-based method.
    Fallback when Gemini API is not available.
    """
    hash_obj = hashlib.md5(text.encode())
    hash_int = int(hash_obj.hexdigest(), 16)
    
    # Generate 768 pseudo-random floats (matching text-embedding-004 dimension)
    embedding = []
    for i in range(768):
        val = ((hash_int + i) % 1000) / 1000.0
        embedding.append(val)
    
    return embedding


# Main enrichment function

def enrich_job(job_dict: Dict) -> Dict:
    """
    Enrich a job dictionary with Gemini-extracted information.
    
    Args:
        job_dict: Raw job dictionary from scraper.
        
    Returns:
        Enriched job dictionary with additional fields.
    """
    description = job_dict.get('description', '')
    position = job_dict.get('position', '')
    
    # Use Gemini to extract skills, seniority, and summary
    gemini_result = enrich_job_with_gemini(description, position)
    
    # Combine position and description for embedding
    full_text = f"{position}. {description}"
    
    # Generate embedding using Gemini
    embedding = get_gemini_embedding(full_text)
    
    # Create enriched job dict
    enriched_job = {
        'id': job_dict.get('id', ''),
        'company': job_dict.get('company', ''),
        'position': position,
        'location': job_dict.get('location', ''),
        'url': job_dict.get('url', ''),
        'tags': job_dict.get('tags', []),
        'description': description,
        'skills': gemini_result['skills'],
        'seniority': gemini_result['seniority'],
        'summary': gemini_result['summary'],
        'embedding': embedding
    }
    
    return enriched_job


# Legacy function names for backward compatibility
def extract_skills(description: str) -> List[str]:
    """Legacy function - use enrich_job_with_gemini instead."""
    return extract_skills_placeholder(description)


def extract_seniority(description: str) -> str:
    """Legacy function - use enrich_job_with_gemini instead."""
    return extract_seniority_placeholder(description)


def summarize_job(description: str) -> str:
    """Legacy function - use enrich_job_with_gemini instead."""
    return summarize_job_placeholder(description)


def generate_embedding(text: str) -> List[float]:
    """Legacy function - use get_gemini_embedding instead."""
    return get_gemini_embedding(text)


if __name__ == "__main__":
    # Test enrichment
    test_job = {
        'id': 'test-123',
        'company': 'Tech Corp',
        'position': 'Senior Python Developer',
        'description': 'We are looking for a senior Python developer with experience in AWS, Docker, and Kubernetes. Must have strong SQL skills and knowledge of microservices architecture. The ideal candidate will have 5+ years of experience building scalable backend systems.',
        'location': 'Remote',
        'url': 'https://example.com/job',
        'tags': ['python', 'backend']
    }
    
    print("Testing job enrichment...")
    enriched = enrich_job(test_job)
    print("\n✅ Enriched Job:")
    print(f"   Skills: {enriched['skills']}")
    print(f"   Seniority: {enriched['seniority']}")
    print(f"   Summary: {enriched['summary']}")
    print(f"   Embedding dimension: {len(enriched['embedding'])}")
