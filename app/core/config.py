from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/finance_tracker"
    DASHBOARD_URL: str = "http://localhost:5173"
    # Authentication
    JWT_SECRET_KEY: str = "your-super-secret-jwt-key-change-this-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # OpenAI
    # OPENAI_API_KEY: str = "AIzaSyDcv9Rl8w4BvcWCQC_rNiMyeUJTnDQM9cQ"
    GEMINI_API_KEY: str = "placeholder"
    
    # Twilio
    TWILIO_ACCOUNT_SID: str = "placeholder-account-sid"
    TWILIO_AUTH_TOKEN: str = "placeholder-auth-token"
    TWILIO_WHATSAPP_NUMBER: str = "whatsapp:+14155238886"
    
    # App Settings
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()