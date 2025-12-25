#!/usr/bin/env python3
"""
Test script for semantic search API.

Script Type: ONE-TIME UTILITY (for testing)
Purpose: Verify that the semantic search endpoint is working correctly
Should be run: After starting the FastAPI server to test functionality
"""
import requests
import json
import time

# API base URL
BASE_URL = "http://localhost:8000"


def print_separator(char="=", length=80):
    """Print a separator line."""
    print(char * length)


def print_section(title):
    """Print a section header."""
    print_separator()
    print(f"  {title}")
    print_separator()


def test_health_check():
    """Test the health check endpoint."""
    print_section("🏥 HEALTH CHECK")
    
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_search_stats():
    """Test the search stats endpoint."""
    print_section("📊 SEARCH STATISTICS")
    
    try:
        response = requests.get(f"{BASE_URL}/api/search/stats")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Search Index Stats:")
            print(f"   Total jobs: {data['total_jobs']}")
            print(f"   Jobs with embeddings: {data['jobs_with_embeddings']}")
            print(f"   Embedding dimension: {data['embedding_dimension']}")
            print(f"   Unique skills: {data['unique_skills']}")
            print(f"\n   Seniority distribution:")
            for level, count in data['seniority_distribution'].items():
                print(f"      {level}: {count}")
            print(f"\n   Top skills: {', '.join(data['top_skills'][:10])}")
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_semantic_search(query: str, limit: int = 5):
    """Test semantic search endpoint."""
    print_section(f"🔍 SEMANTIC SEARCH: '{query}'")
    
    try:
        payload = {
            "query": query,
            "limit": limit,
            "min_similarity": 0.5
        }
        
        print(f"\nRequest payload:")
        print(json.dumps(payload, indent=2))
        
        start_time = time.time()
        response = requests.post(f"{BASE_URL}/api/search/semantic", json=payload)
        elapsed = (time.time() - start_time) * 1000
        
        print(f"\nStatus: {response.status_code}")
        print(f"Response time: {elapsed:.2f}ms")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Found {data['count']} results (processing: {data['processing_time_ms']:.2f}ms)")
            
            for i, job in enumerate(data['results'], 1):
                print(f"\n{i}. {job['position']} at {job['company']}")
                print(f"   Similarity: {job['similarity']:.4f}")
                print(f"   Seniority: {job['seniority']}")
                print(f"   Skills: {', '.join(job['skills'][:5])}")
                print(f"   Summary: {job['summary'][:100]}...")
            
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_similar_jobs(job_id: str, limit: int = 3):
    """Test similar jobs endpoint."""
    print_section(f"🔗 SIMILAR JOBS TO: {job_id}")
    
    try:
        payload = {
            "job_id": job_id,
            "limit": limit
        }
        
        response = requests.post(f"{BASE_URL}/api/search/similar", json=payload)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Found {data['count']} similar jobs")
            
            for i, job in enumerate(data['results'], 1):
                print(f"\n{i}. {job['position']} at {job['company']}")
                print(f"   Similarity: {job['similarity']:.4f}")
                print(f"   Seniority: {job['seniority']}")
                print(f"   Skills: {', '.join(job['skills'][:5])}")
            
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_get_job(job_id: str):
    """Test get job by ID endpoint."""
    print_section(f"📄 GET JOB: {job_id}")
    
    try:
        response = requests.get(f"{BASE_URL}/api/search/job/{job_id}")
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            job = response.json()
            print(f"\n✅ Job Details:")
            print(f"   Position: {job['position']}")
            print(f"   Company: {job['company']}")
            print(f"   Location: {job['location']}")
            print(f"   Seniority: {job['seniority']}")
            print(f"   Skills: {', '.join(job['skills'])}")
            print(f"   Summary: {job['summary']}")
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Run all tests."""
    print_section("🧪 SEMANTIC SEARCH API TESTS")
    print(f"\nAPI Base URL: {BASE_URL}")
    print(f"Make sure the FastAPI server is running!")
    print()
    
    # Test health check
    if not test_health_check():
        print("\n❌ Server is not running. Start it with:")
        print("   cd backend && uvicorn app.main:app --reload")
        return
    
    print()
    
    # Test search stats
    test_search_stats()
    print()
    
    # Test semantic search with various queries
    test_queries = [
        "Python machine learning engineer",
        "Senior DevOps with Kubernetes",
        "Frontend developer React",
        "Data scientist with SQL experience"
    ]
    
    for query in test_queries:
        test_semantic_search(query, limit=3)
        print()
    
    # Test similar jobs (using a known job ID)
    print("\n💡 To test similar jobs, first get a job ID from search results")
    print("   Then run: test_similar_jobs('job-id-here')")
    
    # Test get job
    print("\n💡 To test get job, use a job ID from search results")
    print("   Then run: test_get_job('job-id-here')")
    
    print_separator()
    print("\n✅ Tests complete!")
    print("\nNext steps:")
    print("  1. Try different search queries")
    print("  2. Test with filters (seniority, skills)")
    print("  3. Test similar jobs endpoint")
    print("  4. Integrate with frontend")


if __name__ == "__main__":
    main()
