"""
Resume Intelligence System - Premium Streamlit Frontend

A beautiful, high-end interface for AI-powered resume matching and skill gap analysis.
"""
import streamlit as st
import sys
import os

# Add components to path
sys.path.insert(0, os.path.dirname(__file__))

from components.ui_components import (
    render_job_card,
    render_profile_summary,
    render_system_health,
    render_circular_progress
)
from utils.styles import CUSTOM_CSS
from utils.api_client import BackendAPI


# Page Configuration
st.set_page_config(
    page_title="Resume Intelligence System",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply Custom CSS
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Initialize API Client
api = BackendAPI()


def render_header():
    """Render the main header with branding."""
    st.markdown("""
        <div style="text-align: center; padding: 20px 0;">
            <h1 style="font-size: 3.5rem; margin-bottom: 10px; color: #ffffff;">
                🎯 Resume Intelligence System
            </h1>
            <p style="color: #a78bfa; font-size: 1.2rem; font-weight: 500;">
                AI-Powered Job Matching & Career Intelligence
            </p>
            <p style="color: #9ca3af; font-size: 0.95rem;">
                Powered by Multi-Key Gemini AI with Advanced Skill Gap Analysis
            </p>
        </div>
    """, unsafe_allow_html=True)


def render_sidebar():
    """Render the sidebar with branding and controls."""
    # Logo Placeholder
    st.sidebar.markdown("""
        <div style="text-align: center; padding: 20px 0;">
            <div style="width: 100px; height: 100px; margin: 0 auto; 
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        border-radius: 20px; display: flex; align-items: center; 
                        justify-content: center; font-size: 3rem; box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);">
                🎯
            </div>
            <h2 style="color: #ffffff; margin-top: 15px; font-size: 1.5rem;">
                Resume AI
            </h2>
            <p style="color: #a78bfa; font-size: 0.85rem;">
                v2.0 - Multi-Key Edition
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    st.sidebar.markdown("---")
    
    # Settings
    st.sidebar.markdown("### ⚙️ Settings")
    
    num_matches = st.sidebar.slider(
        "Number of Matches",
        min_value=1,
        max_value=10,
        value=5,
        help="Maximum number of job matches to return"
    )
    
    min_similarity = st.sidebar.slider(
        "Minimum Similarity",
        min_value=0.0,
        max_value=1.0,
        value=0.3,
        step=0.05,
        help="Minimum similarity threshold (0-1)"
    )
    
    include_skill_gap = st.sidebar.checkbox(
        "Include Skill Gap Analysis",
        value=True,
        help="Analyze skill gaps for top matches"
    )
    
    # System Health
    render_system_health(api_keys_count=3)
    
    # About
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ℹ️ About")
    st.sidebar.info("""
        This system uses advanced AI to:
        - Extract professional profiles from resumes
        - Match you with relevant job opportunities
        - Analyze skill gaps and provide recommendations
        
        **Features:**
        - Multi-key rotation (3x capacity)
        - Real-time skill gap analysis
        - 768-dim semantic embeddings
        - Glassmorphism UI design
    """)
    
    return num_matches, min_similarity, include_skill_gap


def main():
    """Main application logic."""
    # Render header
    render_header()
    
    # Render sidebar and get settings
    num_matches, min_similarity, include_skill_gap = render_sidebar()
    
    # Check backend health
    if not api.health_check():
        st.error("""
            ❌ **Backend is not responding!**
            
            Please ensure the backend service is running:
            ```bash
            docker-compose up backend
            ```
        """)
        return
    
    # Main content area
    # Main content area - Upload section
    st.markdown("## 📄 Upload Your Resume")
    st.markdown("Upload your resume in PDF format to get AI-powered job recommendations and skill gap analysis.")
    
    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=["pdf"],
        help="Upload your resume in PDF format (max 10MB)"
    )
    
    if uploaded_file is not None:
        # Display file info
        file_size = len(uploaded_file.getvalue()) / 1024  # KB
        st.success(f"✅ File uploaded: **{uploaded_file.name}** ({file_size:.1f} KB)")
        
        # Analyze button
        if st.button("🚀 Analyze Resume & Find Matches", type="primary", use_container_width=True):
            # Show loading state with status
            with st.status("🤖 AI is analyzing your resume...", expanded=True) as status:
                st.write("📄 Extracting text from PDF...")
                st.write("🧠 Creating professional profile with Gemini AI...")
                st.write("🔄 Rotating through API keys for optimal performance...")
                st.write("🎯 Generating 768-dimensional semantic embedding...")
                st.write("🔍 Searching for matching job opportunities...")
                
                if include_skill_gap:
                    st.write("📊 Analyzing skill gaps with combined AI analysis...")
                
                # Make API call
                result = api.match_resume(
                    pdf_file=uploaded_file,
                    limit=num_matches,
                    min_similarity=min_similarity,
                    include_skill_gap=include_skill_gap
                )
                
                if result:
                    status.update(label="✅ Analysis Complete!", state="complete", expanded=False)
                else:
                    status.update(label="❌ Analysis Failed", state="error", expanded=False)
                    return
            
            # Display results
            if result:
                profile = result.get('profile', {})
                matches = result.get('matches', [])
                processing_time = result.get('processing_time_ms', 0)
                
                # Show processing time
                st.info(f"⚡ Processing completed in {processing_time / 1000:.2f} seconds")
                
                # Profile Summary
                render_profile_summary(profile)
                
                # Job Matches
                if matches:
                    st.markdown(f"## 🎯 Top {len(matches)} Job Matches")
                    st.markdown(f"Found **{len(matches)}** matching opportunities based on your profile")
                    
                    # Show average similarity
                    avg_similarity = sum(m.get('similarity', 0) for m in matches) / len(matches)
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Total Matches", len(matches))
                    
                    with col2:
                        st.metric("Average Match", f"{int(avg_similarity * 100)}%")
                    
                    with col3:
                        best_match = max(matches, key=lambda x: x.get('similarity', 0))
                        st.metric("Best Match", f"{int(best_match.get('similarity', 0) * 100)}%")
                    
                    # Render each job card
                    for idx, job in enumerate(matches):
                        render_job_card(job, idx)
                else:
                    st.warning("No matching jobs found. Try lowering the minimum similarity threshold.")


if __name__ == "__main__":
    main()
