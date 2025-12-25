#!/usr/bin/env python3
"""
Test script for Gemini API integration in job enrichment.
Run this to verify your Gemini API key is working correctly.
"""

import os
import sys

# Add project to path
sys.path.insert(0, '/Users/sawanttej/Desktop/W')

from services.kafka.enrichment import (
    enrich_job_with_gemini,
    get_gemini_embedding,
    enrich_job
)


def print_header(title):
    """Print formatted header"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def test_gemini_enrichment():
    """Test Gemini job enrichment"""
    print_header("🧪 Testing Gemini Job Enrichment")
    
    # Check API key
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        print("❌ GEMINI_API_KEY not set!")
        print("   Please set it with: export GEMINI_API_KEY='your_key_here'")
        return False
    
    print(f"✅ API Key found: {api_key[:10]}...{api_key[-4:]}")
    
    # Test job
    test_description = """
    We are seeking a Senior Full Stack Engineer to join our growing team. 
    The ideal candidate will have 5+ years of experience with React, Node.js, 
    and PostgreSQL. You'll be responsible for building scalable microservices 
    and modern web applications. Experience with AWS, Docker, and Kubernetes 
    is highly valued. Strong communication skills and ability to mentor junior 
    developers are essential.
    """
    
    test_position = "Senior Full Stack Engineer"
    
    print(f"\n📝 Test Job:")
    print(f"   Position: {test_position}")
    print(f"   Description: {test_description[:100]}...")
    
    # Test enrichment
    print(f"\n🔄 Calling Gemini API for enrichment...")
    try:
        result = enrich_job_with_gemini(test_description, test_position)
        
        print(f"\n✅ Enrichment Successful!")
        print(f"\n   📊 Skills Extracted ({len(result['skills'])} total):")
        for skill in result['skills'][:10]:
            print(f"      • {skill}")
        if len(result['skills']) > 10:
            print(f"      ... and {len(result['skills']) - 10} more")
        
        print(f"\n   🎯 Seniority Level: {result['seniority']}")
        
        print(f"\n   📄 Summary:")
        print(f"      {result['summary']}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Enrichment Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_gemini_embedding():
    """Test Gemini embedding generation"""
    print_header("🧪 Testing Gemini Embeddings")
    
    test_text = "Senior Python Developer with AWS and Docker experience"
    
    print(f"📝 Test Text: {test_text}")
    print(f"\n🔄 Generating embedding...")
    
    try:
        embedding = get_gemini_embedding(test_text)
        
        print(f"\n✅ Embedding Generated!")
        print(f"   Dimension: {len(embedding)}")
        print(f"   Sample values: {embedding[:5]}")
        print(f"   Type: {type(embedding[0])}")
        
        # Verify dimension
        if len(embedding) == 768:
            print(f"\n✅ Correct dimension (768) for text-embedding-004")
        else:
            print(f"\n⚠️  Unexpected dimension: {len(embedding)}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Embedding Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_full_pipeline():
    """Test complete enrichment pipeline"""
    print_header("🧪 Testing Full Enrichment Pipeline")
    
    test_job = {
        'id': 'test-gemini-123',
        'company': 'TechCorp AI',
        'position': 'Machine Learning Engineer',
        'description': """
        Join our ML team to build cutting-edge AI solutions. We're looking for 
        an experienced ML engineer with strong Python skills, experience with 
        TensorFlow/PyTorch, and knowledge of MLOps practices. You'll work on 
        deploying models to production using Kubernetes and AWS SageMaker. 
        Experience with data pipelines, feature engineering, and model monitoring 
        is essential. This is a senior-level position requiring 4+ years of 
        relevant experience.
        """,
        'location': 'Remote',
        'url': 'https://example.com/job/ml-engineer',
        'tags': ['machine-learning', 'python', 'ai']
    }
    
    print(f"📝 Test Job:")
    print(f"   ID: {test_job['id']}")
    print(f"   Position: {test_job['position']}")
    print(f"   Company: {test_job['company']}")
    
    print(f"\n🔄 Running full enrichment pipeline...")
    
    try:
        enriched = enrich_job(test_job)
        
        print(f"\n✅ Pipeline Complete!")
        print(f"\n   📊 Enriched Data:")
        print(f"      ID: {enriched['id']}")
        print(f"      Company: {enriched['company']}")
        print(f"      Position: {enriched['position']}")
        print(f"      Seniority: {enriched['seniority']}")
        print(f"      Skills ({len(enriched['skills'])}): {', '.join(enriched['skills'][:5])}...")
        print(f"      Summary: {enriched['summary'][:100]}...")
        print(f"      Embedding dimension: {len(enriched['embedding'])}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Pipeline Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("  🚀 GEMINI API INTEGRATION TEST SUITE")
    print("="*70)
    
    results = {
        "Enrichment": test_gemini_enrichment(),
        "Embeddings": test_gemini_embedding(),
        "Full Pipeline": test_full_pipeline()
    }
    
    # Summary
    print_header("📊 TEST SUMMARY")
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status} - {test_name}")
    
    all_passed = all(results.values())
    
    print(f"\n{'='*70}")
    if all_passed:
        print("✅ ALL TESTS PASSED - Gemini integration is working!")
    else:
        print("⚠️  SOME TESTS FAILED - Check errors above")
    print(f"{'='*70}\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
