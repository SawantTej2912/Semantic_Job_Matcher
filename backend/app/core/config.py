
import os
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    # API Configuration
    PROJECT_NAME: str = "Job Recommendation System"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # PostgreSQL Configuration
    POSTGRES_HOST: str = "localhost"
    POSTGRES_DB: str = "jobs"
    POSTGRES_USER: str = "user"
    POSTGRES_PASSWORD: str = "pass"
    POSTGRES_PORT: str = "5432"
    
    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    
    # Kafka Configuration
    KAFKA_BROKER: str = "localhost:9092"
    
    # Gemini API
    GEMINI_API_KEY: str = ""
    
    # Pydantic v2 configuration - allow extra fields
    model_config = ConfigDict(
        env_file=".env",
        extra="allow"  # Allow extra environment variables without validation errors
    )

settings = Settings()
