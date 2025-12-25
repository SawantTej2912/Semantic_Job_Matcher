#!/usr/bin/env python3
"""
Test script for resume upload and job matching.

Script Type: ONE-TIME UTILITY (for testing)
Purpose: Simulate PDF upload and verify resume matching functionality
Should be run: After starting the FastAPI server to test resume endpoints
"""
import requests
import json
import sys
from pathlib import Path

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


def create_sample_resume_pdf():
    """
    Create a sample resume PDF for testing.
    
    Returns:
        Path to the created PDF file
    """
    try:
        import fitz  # PyMuPDF
        
        # Create a simple PDF with resume content
        doc = fitz.open()
        page = doc.new_page()
        
        # Sample resume text
        resume_text = """
JOHN DOE
Senior Software Engineer
Email: john.doe@example.com | Phone: (555) 123-4567

PROFESSIONAL SUMMARY
Experienced Senior Software Engineer with 8+ years of expertise in full-stack development,
cloud architecture, and machine learning. Proven track record of building scalable systems
using Python, React, and AWS. Passionate about AI/ML and data-driven solutions.

TECHNICAL SKILLS
• Programming: Python, JavaScript, TypeScript, Java, SQL
• Frameworks: React, Node.js, FastAPI, Django, TensorFlow, PyTorch
• Cloud & DevOps: AWS (EC2, S3, Lambda), Docker, Kubernetes, CI/CD
• Databases: PostgreSQL, MongoDB, Redis
• ML/AI: Machine Learning, Deep Learning, NLP, Computer Vision
• Tools: Git, JIRA, Kafka, Elasticsearch

PROFESSIONAL EXPERIENCE

Senior Software Engineer | Tech Innovations Inc. | 2020 - Present
• Led development of ML-powered recommendation system serving 1M+ users
• Architected microservices infrastructure using Docker and Kubernetes on AWS
• Implemented real-time data pipeline using Kafka and PostgreSQL
• Mentored team of 5 junior developers

Software Engineer | DataCorp Solutions | 2017 - 2020
• Developed RESTful APIs using Python FastAPI and Node.js
• Built responsive frontend applications with React and TypeScript
• Optimized database queries reducing response time by 60%
• Implemented CI/CD pipelines using Jenkins and GitHub Actions

Junior Developer | StartupXYZ | 2016 - 2017
• Developed web applications using Python Django and JavaScript
• Collaborated with cross-functional teams in Agile environment
• Wrote unit tests achieving 85% code coverage

EDUCATION
Master of Science in Computer Science | Stanford University | 2016
Bachelor of Science in Software Engineering | MIT | 2014

CERTIFICATIONS
• AWS Certified Solutions Architect
• Google Cloud Professional Data Engineer
• Certified Kubernetes Administrator (CKA)

PROJECTS
• Open-source contributor to TensorFlow and scikit-learn
• Built personal project: AI-powered job matching platform
• Published 3 technical articles on Medium with 10K+ views
"""
        
        # Add text to page
        text_rect = fitz.Rect(50, 50, 550, 750)
        page.insert_textbox(
            text_rect,
            resume_text,
            fontsize=10,
            fontname="helv",
            align=0
        )
        
        # Save PDF
        pdf_path = "sample_resume.pdf"
        doc.save(pdf_path)
        doc.close()
        
        print(f"✅ Created sample resume: {pdf_path}")
        return pdf_path
        
    except ImportError:
        print("❌ PyMuPDF not installed. Install with: pip install pymupdf")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error creating sample PDF: {e}")
        sys.exit(1)


def test_resume_match(pdf_path: str, limit: int = 5):
    """
    Test resume matching endpoint.
    
    Args:
        pdf_path: Path to resume PDF file
        limit: Number of job matches to return
    """
    print_section(f"📄 TESTING RESUME MATCH: {pdf_path}")
    
    try:
        # Check if file exists
        if not Path(pdf_path).exists():
            print(f"❌ File not found: {pdf_path}")
            return False
        
        # Prepare file upload
        with open(pdf_path, 'rb') as f:
            files = {'file': (pdf_path, f, 'application/pdf')}
            params = {
                'limit': limit,
                'min_similarity': 0.3,
                'include_skill_gap': True
            }
            
            print(f"\n📤 Uploading resume...")
            print(f"   File: {pdf_path}")
            print(f"   Limit: {limit}")
            print(f"   Min similarity: 0.3")
            print(f"   Include skill gap: True")
            
            # Make request
            response = requests.post(
                f"{BASE_URL}/api/resume/match",
                files=files,
                params=params
            )
        
        print(f"\n📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Display profile
            print_section("👤 EXTRACTED PROFILE")
            profile = data['profile']
            print(f"\n📝 Summary:")
            print(f"   {profile['summary']}")
            print(f"\n💼 Experience: {profile['experience_years']} years")
            print(f"\n🎓 Education: {profile.get('education', 'Not specified')}")
            print(f"\n💪 Key Strengths:")
            for strength in profile['key_strengths']:
                print(f"   • {strength}")
            print(f"\n🛠️  Skills ({len(profile['skills'])}):")
            for skill in profile['skills'][:15]:
                print(f"   • {skill}")
            if len(profile['skills']) > 15:
                print(f"   ... and {len(profile['skills']) - 15} more")
            
            # Display matches
            print_section(f"🎯 TOP {len(data['matches'])} JOB MATCHES")
            
            for i, match in enumerate(data['matches'], 1):
                print(f"\n{'='*80}")
                print(f"MATCH #{i}: {match['position']} at {match['company']}")
                print(f"{'='*80}")
                print(f"\n📍 Location: {match['location']}")
                print(f"🎯 Seniority: {match['seniority']}")
                print(f"🔗 URL: {match['url']}")
                print(f"\n📊 Similarity Score: {match['similarity']:.4f} ({match['similarity']*100:.1f}%)")
                
                print(f"\n💼 Required Skills:")
                for skill in match['skills'][:10]:
                    print(f"   • {skill}")
                if len(match['skills']) > 10:
                    print(f"   ... and {len(match['skills']) - 10} more")
                
                print(f"\n📝 Job Summary:")
                print(f"   {match['summary'][:200]}...")
                
                # Display skill gap analysis
                if match.get('skill_gap'):
                    print(f"\n{'─'*80}")
                    print(f"🔍 SKILL GAP ANALYSIS")
                    print(f"{'─'*80}")
                    
                    gap = match['skill_gap']
                    
                    print(f"\n✅ Matching Skills ({len(gap['matching_skills'])}):")
                    for skill in gap['matching_skills'][:10]:
                        print(f"   ✓ {skill}")
                    
                    print(f"\n❌ Missing Skills (Top 3 to learn):")
                    for j, skill in enumerate(gap['missing_skills'], 1):
                        print(f"   {j}. {skill}")
                    
                    print(f"\n💡 Recommendations:")
                    for j, rec in enumerate(gap['recommendations'], 1):
                        print(f"   {j}. {rec}")
            
            # Summary
            print_section("📈 SUMMARY")
            print(f"\n✅ Total matches found: {data['total_matches']}")
            print(f"⏱️  Processing time: {data['processing_time_ms']:.2f}ms")
            print(f"\n🎯 Best match: {data['matches'][0]['position']} at {data['matches'][0]['company']}")
            print(f"   Similarity: {data['matches'][0]['similarity']:.4f} ({data['matches'][0]['similarity']*100:.1f}%)")
            
            return True
            
        else:
            print(f"\n❌ Error Response:")
            print(json.dumps(response.json(), indent=2))
            return False
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_resume_analyze(pdf_path: str):
    """Test resume analysis endpoint (profile extraction only)."""
    print_section(f"🔍 TESTING RESUME ANALYSIS: {pdf_path}")
    
    try:
        with open(pdf_path, 'rb') as f:
            files = {'file': (pdf_path, f, 'application/pdf')}
            response = requests.post(
                f"{BASE_URL}/api/resume/analyze",
                files=files
            )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Profile Extracted:")
            print(json.dumps(data['profile'], indent=2))
            print(f"\nText length: {data['text_length']} characters")
            print(f"Embedding dimension: {data['embedding_dimension']}")
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Run resume upload tests."""
    print_section("🧪 RESUME UPLOAD & MATCHING TESTS")
    print(f"\nAPI Base URL: {BASE_URL}")
    print(f"Make sure the FastAPI server is running!")
    print()
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code != 200:
            print("❌ Server is not responding. Start it with:")
            print("   cd backend && uvicorn app.main:app --reload")
            return
    except:
        print("❌ Cannot connect to server. Start it with:")
        print("   cd backend && uvicorn app.main:app --reload")
        return
    
    print("✅ Server is running!\n")
    
    # Create or use existing resume
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        print(f"Using provided resume: {pdf_path}")
    else:
        print("No resume provided. Creating sample resume...")
        pdf_path = create_sample_resume_pdf()
    
    print()
    
    # Test resume matching
    test_resume_match(pdf_path, limit=5)
    
    print()
    print_separator()
    print("\n✅ Tests complete!")
    print("\nNext steps:")
    print("  1. Try with your own resume PDF")
    print("  2. Adjust similarity threshold")
    print("  3. Test with different resumes")
    print("  4. Check Swagger docs: http://localhost:8000/docs")


if __name__ == "__main__":
    main()
