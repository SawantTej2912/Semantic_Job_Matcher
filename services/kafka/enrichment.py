"""
Job enrichment module using GeminiProvider with key rotation.
"""
import os
import json
import re
from typing import List, Dict, Optional
import hashlib

# Import GeminiProvider
try:
    from services.kafka.gemini_provider import gemini_provider
    GEMINI_AVAILABLE = gemini_provider is not None
except ImportError:
    GEMINI_AVAILABLE = False
    gemini_provider = None
    print("⚠️  GeminiProvider not available. Using placeholder enrichment.")


def enrich_job_with_gemini(description: str, position: str = "") -> Dict:
    """
    Use Gemini API to extract skills, seniority, and summary from job description.
    Uses gemini-2.5-flash-lite with key rotation.
    
    Args:
        description: Job description text.
        position: Job position/title.
        
    Returns:
        Dictionary containing:
        - skills: List of extracted skills
        - seniority: Seniority level (Junior, Mid, Senior, Lead)
        - summary: 2-sentence summary of the job
    """
    if not gemini_provider:
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

        # Call Gemini API with key rotation
        response_text = gemini_provider.generate_content(prompt, max_output_tokens=1000)
        
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
    Uses key rotation on rate limits.
    
    Args:
        text: Text to generate embedding for.
        
    Returns:
        Embedding vector (list of floats).
    """
    if not gemini_provider:
        # Fallback to placeholder embedding
        return generate_embedding_placeholder(text)
    
    try:
        # Call Gemini embeddings API with key rotation
        embedding = gemini_provider.embed_content(text)
        return embedding
        
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
    # Generate 768-dim vector
    import random
    random.seed(hash_value)
    return [random.random() for _ in range(768)]


def enrich_job(job_data: Dict) -> Dict:
    """
    Main enrichment function that combines Gemini enrichment and embedding.
    
    Args:
        job_data: Job dictionary with description and other fields.
        
    Returns:
        Enriched job dictionary with skills, seniority, summary, and embedding.
    """
    description = job_data.get('description', '')
    position = job_data.get('position', '')
    
    # Step 1: Enrich with Gemini (skills, seniority, summary)
    enrichment = enrich_job_with_gemini(description, position)
    
    # Step 2: Generate embedding (with automatic throttling from provider)
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


# For backward compatibility
gemini_client = gemini_provider
