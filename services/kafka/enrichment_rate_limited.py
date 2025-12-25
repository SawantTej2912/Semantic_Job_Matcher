"""
Job enrichment module using Gemini API with rate limit protection.
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
    Includes retry logic for rate limit errors (429).
    
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
    
    # Retry loop for handling 429 errors
    for attempt in range(MAX_RETRIES):
        try:
            # Wait for rate limit before making API call
            _wait_for_rate_limit()
            
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
                    temperature=0.3,
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
                "skills": skills[:15],
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
            error_str = str(e)
            
            # Check for 429 rate limit error
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "quota" in error_str.lower():
                if attempt < MAX_RETRIES - 1:
                    print(f"⚠️  Rate limit hit (429). Waiting {RETRY_DELAY}s before retry {attempt + 2}/{MAX_RETRIES}...")
                    time.sleep(RETRY_DELAY)
                    continue
                else:
                    print(f"❌ Rate limit hit after {MAX_RETRIES} retries. Using placeholder.")
            else:
                print(f"⚠️  Gemini API error: {e}")
            
            # Fallback to placeholder
            return {
                "skills": extract_skills_placeholder(description),
                "seniority": extract_seniority_placeholder(description),
                "summary": summarize_job_placeholder(description)
            }
    
    # If we exhausted all retries, return placeholder
    return {
        "skills": extract_skills_placeholder(description),
        "seniority": extract_seniority_placeholder(description),
        "summary": summarize_job_placeholder(description)
    }


def get_gemini_embedding(text: str) -> List[float]:
    """
    Generate embedding vector using Gemini's text-embedding-004 model.
    Includes retry logic for rate limit errors (429).
    
    Args:
        text: Text to generate embedding for.
        
    Returns:
        Embedding vector (list of floats).
    """
    if not gemini_client:
        # Fallback to placeholder embedding
        return generate_embedding_placeholder(text)
    
    # Retry loop for handling 429 errors
    for attempt in range(MAX_RETRIES):
        try:
            # Wait for rate limit before making API call
            _wait_for_rate_limit()
            
            # Call Gemini embeddings API
            result = gemini_client.models.embed_content(
                model='text-embedding-004',
                contents=text
            )
            
            # Extract embedding vector
            embedding = result.embeddings[0].values
            
            return list(embedding)
            
        except Exception as e:
            error_str = str(e)
            
            # Check for 429 rate limit error
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "quota" in error_str.lower():
                if attempt < MAX_RETRIES - 1:
                    print(f"⚠️  Rate limit hit (429) on embedding. Waiting {RETRY_DELAY}s before retry {attempt + 2}/{MAX_RETRIES}...")
                    time.sleep(RETRY_DELAY)
                    continue
                else:
                    print(f"❌ Rate limit hit after {MAX_RETRIES} retries. Using placeholder embedding.")
            else:
                print(f"⚠️  Gemini embedding error: {e}")
            
            # Fallback to placeholder
            return generate_embedding_placeholder(text)
    
    # If we exhausted all retries, return placeholder
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
    Determine seniority level using keyword matching.
    Fallback when Gemini API is not available.
    """
    description_lower = description.lower()
    
    if any(word in description_lower for word in ['senior', 'sr.', 'lead', 'principal', 'staff']):
        return 'Senior'
    elif any(word in description_lower for word in ['junior', 'entry', 'associate']):
        return 'Junior'
    else:
        return 'Mid'


def summarize_job_placeholder(description: str) -> str:
    """
    Create a simple summary by taking the first 200 characters.
    Fallback when Gemini API is not available.
    """
    # Clean HTML tags
    clean_desc = re.sub(r'<[^>]+>', '', description)
    # Take first 200 characters
    summary = clean_desc[:200].strip()
    if len(clean_desc) > 200:
        summary += "..."
    return summary


def generate_embedding_placeholder(text: str) -> List[float]:
    """
    Generate a placeholder embedding vector.
    Fallback when Gemini API is not available.
    """
    # Use hash to generate consistent placeholder
    hash_value = int(hashlib.md5(text.encode()).hexdigest(), 16)
    # Generate 384-dim vector (smaller than real 768)
    import random
    random.seed(hash_value)
    return [random.random() for _ in range(384)]


def enrich_job(job_data: Dict) -> Dict:
    """
    Main enrichment function that combines Gemini enrichment and embedding.
    Ensures sequential execution with delays between calls.
    
    Args:
        job_data: Job dictionary with description and other fields.
        
    Returns:
        Enriched job dictionary with skills, seniority, summary, and embedding.
    """
    description = job_data.get('description', '')
    position = job_data.get('position', '')
    
    # Step 1: Enrich with Gemini (skills, seniority, summary)
    enrichment = enrich_job_with_gemini(description, position)
    
    # Step 2: Generate embedding (with automatic delay from rate limiting)
    full_text = f"{position}. {description}"
    embedding = get_gemini_embedding(full_text)
    
    # Combine original job data with enrichment
    enriched_job = {
        **job_data,
        'skills': enrichment['skills'],
        'seniority': enrichment['seniority'],
        'summary': enrichment['summary'],
        'embedding': embedding
    }
    
    return enriched_job
