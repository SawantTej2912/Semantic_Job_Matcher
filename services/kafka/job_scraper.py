"""
Job scraper module for fetching job postings from RemoteOK API.
"""
import requests


def fetch_jobs():
    """
    Fetches job postings from RemoteOK public API.
    
    Returns:
        list: A list of cleaned job dictionaries.
    """
    try:
        # Fetch jobs from RemoteOK API
        response = requests.get("https://remoteok.com/api", timeout=10)
        response.raise_for_status()
        
        raw_jobs = response.json()
        
        # Filter out non-dictionary items (like metadata at index 0)
        jobs = [item for item in raw_jobs if isinstance(item, dict)]
        
        # Clean and extract relevant fields
        cleaned_jobs = []
        for job in jobs:
            cleaned_job = {
                "id": job.get("id", ""),
                "company": job.get("company", ""),
                "position": job.get("position", ""),
                "tags": job.get("tags", []),
                "description": job.get("description", ""),
                "location": job.get("location", ""),
                "url": job.get("url", "")
            }
            cleaned_jobs.append(cleaned_job)
        
        print(f"Successfully fetched {len(cleaned_jobs)} jobs from RemoteOK")
        return cleaned_jobs
        
    except requests.RequestException as e:
        print(f"Error fetching jobs: {e}")
        return []


if __name__ == "__main__":
    # Test the scraper
    jobs = fetch_jobs()
    
    if jobs:
        print("\n=== First 2 Jobs ===")
        for job in jobs[:2]:
            print(f"\nID: {job['id']}")
            print(f"Company: {job['company']}")
            print(f"Position: {job['position']}")
            print(f"Location: {job['location']}")
            print(f"Tags: {job['tags']}")
            print(f"URL: {job['url']}")
            print(f"Description: {job['description'][:100]}...")  # First 100 chars
    else:
        print("No jobs fetched.")
