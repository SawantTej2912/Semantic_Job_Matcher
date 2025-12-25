"""
Reusable UI components for the frontend.
"""
import streamlit as st


def render_similarity_badge(similarity: float) -> str:
    """
    Render a colored similarity badge based on score.
    
    Args:
        similarity: Similarity score (0-1)
        
    Returns:
        HTML string for the badge
    """
    percentage = int(similarity * 100)
    
    if similarity >= 0.7:
        badge_class = "similarity-high"
        label = "Excellent Match"
    elif similarity >= 0.5:
        badge_class = "similarity-medium"
        label = "Good Match"
    else:
        badge_class = "similarity-low"
        label = "Potential Match"
    
    return f"""
    <div class="similarity-badge {badge_class}">
        {percentage}% {label}
    </div>
    """


def render_circular_progress(value: float, label: str = "Match Score") -> None:
    """
    Render a circular progress indicator with color coding.
    
    Args:
        value: Progress value (0-1)
        label: Label for the progress
    """
    percentage = int(value * 100)
    
    # Determine color
    if value >= 0.7:
        color = "#10b981"  # Green
    elif value >= 0.5:
        color = "#f59e0b"  # Yellow
    else:
        color = "#ef4444"  # Red
    
    html = f"""
    <div style="text-align: center; margin: 20px 0;">
        <div style="position: relative; width: 150px; height: 150px; margin: 0 auto;">
            <svg width="150" height="150" style="transform: rotate(-90deg);">
                <circle cx="75" cy="75" r="65" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="10"/>
                <circle cx="75" cy="75" r="65" fill="none" stroke="{color}" stroke-width="10" 
                        stroke-dasharray="{408 * value} 408" stroke-linecap="round"
                        style="transition: stroke-dasharray 1s ease;"/>
            </svg>
            <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); 
                        font-size: 2rem; font-weight: 700; color: {color};">
                {percentage}%
            </div>
        </div>
        <div style="color: #ffffff; font-size: 1rem; margin-top: 10px; font-weight: 500;">
            {label}
        </div>
    </div>
    """
    
    st.markdown(html, unsafe_allow_html=True)


def render_skill_tags(skills: list, tag_type: str = "default") -> str:
    """
    Render skill tags with appropriate styling.
    
    Args:
        skills: List of skill names
        tag_type: Type of tag (default, missing, matching)
        
    Returns:
        HTML string for skill tags
    """
    if not skills:
        return ""
    
    tag_class = {
        "default": "skill-tag",
        "missing": "skill-tag skill-tag-missing",
        "matching": "skill-tag skill-tag-matching"
    }.get(tag_type, "skill-tag")
    
    tags_html = "".join([
        f'<span class="{tag_class}">{skill}</span>'
        for skill in skills
    ])
    
    return f'<div style="margin: 10px 0;">{tags_html}</div>'


def render_job_card(job: dict, index: int) -> None:
    """
    Render a beautiful job card with glassmorphism effect.
    
    Args:
        job: Job dictionary with all details
        index: Job index for ranking
    """
    similarity = job.get('similarity', 0)
    skill_gap = job.get('skill_gap')
    
    # Card HTML
    card_html = f"""
    <div class="job-card">
        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 15px;">
            <div>
                <h3 style="color: #ffffff; margin: 0; font-size: 1.5rem;">
                    #{index + 1} {job.get('position', 'Unknown Position')}
                </h3>
                <p style="color: #a78bfa; margin: 5px 0; font-size: 1.1rem; font-weight: 500;">
                    {job.get('company', 'Unknown Company')}
                </p>
                <p style="color: #9ca3af; margin: 5px 0;">
                    📍 {job.get('location', 'Location not specified')}
                </p>
            </div>
            <div>
                {render_similarity_badge(similarity)}
            </div>
        </div>
    """
    
    st.markdown(card_html, unsafe_allow_html=True)
    
    # Skills section
    if job.get('skills'):
        st.markdown("**Required Skills:**")
        st.markdown(render_skill_tags(job['skills'][:10], "default"), unsafe_allow_html=True)
    
    # Skill gap analysis
    if skill_gap:
        with st.expander("🎯 Skill Gap Analysis", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### ✅ Your Strengths")
                matching = skill_gap.get('matching_skills', [])
                if matching:
                    st.markdown(render_skill_tags(matching[:8], "matching"), unsafe_allow_html=True)
                else:
                    st.info("No direct skill matches found")
            
            with col2:
                st.markdown("### 📚 Skills to Learn")
                missing = skill_gap.get('missing_skills', [])
                if missing:
                    st.markdown(render_skill_tags(missing, "missing"), unsafe_allow_html=True)
                else:
                    st.success("You have all required skills!")
            
            # Recommendations
            recommendations = skill_gap.get('recommendations', [])
            if recommendations:
                st.markdown("### 💡 Recommendations")
                for rec in recommendations:
                    st.markdown(f"- {rec}")
    
    # Job link
    if job.get('url'):
        st.markdown(f"[🔗 View Job Posting]({job['url']})", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)


def render_profile_summary(profile: dict) -> None:
    """
    Render professional profile summary in a glass card.
    
    Args:
        profile: Profile dictionary
    """
    
    st.markdown("## 👤 Your Professional Profile")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="Experience",
            value=f"{profile.get('experience_years', 0)} years",
            delta=None
        )
    
    with col2:
        st.metric(
            label="Skills",
            value=len(profile.get('skills', [])),
            delta=None
        )
    
    with col3:
        st.metric(
            label="Education",
            value=profile.get('education', 'N/A')[:20] + "..." if len(profile.get('education', '')) > 20 else profile.get('education', 'N/A'),
            delta=None
        )
    
    # Summary
    st.markdown("### 📝 Summary")
    st.write(profile.get('summary', 'No summary available'))
    
    # Skills
    if profile.get('skills'):
        st.markdown("### 🛠️ Your Skills")
        st.markdown(render_skill_tags(profile['skills'][:15], "matching"), unsafe_allow_html=True)
    
    # Key Strengths
    if profile.get('key_strengths'):
        st.markdown("### 💪 Key Strengths")
        for strength in profile['key_strengths']:
            st.markdown(f"- {strength}")
    


def render_system_health(api_keys_count: int = 3) -> None:
    """
    Render system health status in sidebar.
    
    Args:
        api_keys_count: Number of API keys available
    """
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🏥 System Health")
    
    # API Status
    status_html = f"""
    <div class="metric-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="color: #9ca3af;">API Status</span>
            <span style="color: #10b981; font-weight: 600;">● Online</span>
        </div>
    </div>
    """
    st.sidebar.markdown(status_html, unsafe_allow_html=True)
    
    # Active Keys
    keys_html = f"""
    <div class="metric-card" style="margin-top: 10px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="color: #9ca3af;">Active Keys</span>
            <span style="color: #8b5cf6; font-weight: 600;">{api_keys_count}/3</span>
        </div>
    </div>
    """
    st.sidebar.markdown(keys_html, unsafe_allow_html=True)
    
    # Model Info
    model_html = """
    <div class="metric-card" style="margin-top: 10px;">
        <div style="color: #9ca3af; font-size: 0.85rem;">Model</div>
        <div style="color: #ffffff; font-weight: 600; margin-top: 5px;">gemini-2.5-flash-lite</div>
        <div style="color: #10b981; font-size: 0.75rem; margin-top: 3px;">30 RPM per key</div>
    </div>
    """
    st.sidebar.markdown(model_html, unsafe_allow_html=True)
