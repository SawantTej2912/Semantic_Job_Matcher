"""
API client for backend communication.
"""
import requests
from typing import Optional, Dict
import streamlit as st


class BackendAPI:
    """Client for communicating with the backend API."""
    
    def __init__(self, base_url: str = "http://backend:8000"):
        """
        Initialize API client.
        
        Args:
            base_url: Base URL of the backend API
        """
        self.base_url = base_url
    
    def health_check(self) -> bool:
        """
        Check if backend is healthy.
        
        Returns:
            True if backend is responding, False otherwise
        """
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def match_resume(
        self,
        pdf_file,
        limit: int = 5,
        min_similarity: float = 0.3,
        include_skill_gap: bool = True
    ) -> Optional[Dict]:
        """
        Upload resume and get job matches.
        
        Args:
            pdf_file: PDF file object
            limit: Maximum number of matches to return
            min_similarity: Minimum similarity threshold
            include_skill_gap: Whether to include skill gap analysis
            
        Returns:
            Dictionary with profile and matches, or None if error
        """
        try:
            # Prepare files
            files = {
                'file': (pdf_file.name, pdf_file, 'application/pdf')
            }
            
            # Prepare params
            params = {
                'limit': limit,
                'min_similarity': min_similarity,
                'include_skill_gap': include_skill_gap
            }
            
            # Make request
            response = requests.post(
                f"{self.base_url}/api/resume/match",
                files=files,
                params=params,
                timeout=60  # 60 second timeout for processing
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                st.error("⚠️ AI Analysis is busy. Please wait 60 seconds and try again.")
                return None
            else:
                st.error(f"Error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            st.error("⏱️ Request timed out. The resume might be too large or the server is busy.")
            return None
        except Exception as e:
            st.error(f"❌ Error communicating with backend: {str(e)}")
            return None
    
    def get_system_stats(self) -> Optional[Dict]:
        """
        Get system statistics.
        
        Returns:
            Dictionary with system stats, or None if error
        """
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception:
            return None
