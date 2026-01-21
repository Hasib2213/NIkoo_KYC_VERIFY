from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API Configuration
    API_TITLE: str = "Biometric Verification API"
    API_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database
    MONGODB_URL: str = "mongodb+srv://localhost:27017"
    DATABASE_NAME: str = "biometric_db"
    
    # Sumsub Configuration
    SUMSUB_API_KEY: str = ""
    SUMSUB_SECRET_KEY: str = ""
    SUMSUB_APP_TOKEN: str = ""
    SUMSUB_LEVEL_NAME: str = "basic-kyc-level"
    SUMSUB_WEBHOOK_SECRET: str = ""
    SUMSUB_BASE_URL: str = "https://api.sandbox.sumsub.com"
    SUMSUB_LIVENESS_ENDPOINT: str = "/v1/liveness/verify"
    SUMSUB_DOCUMENT_ENDPOINT: str = "/v1/document/verify"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Verification Settings
    LIVENESS_CONFIDENCE_THRESHOLD: float = 0.85
    DOCUMENT_CONFIDENCE_THRESHOLD: float = 0.80
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    REQUEST_TIMEOUT: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()