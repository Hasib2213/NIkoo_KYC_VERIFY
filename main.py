# app/main.py - Update with new routers
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database.mongodb import MongoDB
from routers import liveness, kyc, webhook  # Updated imports
from config import settings
import logging
from logging.handlers import RotatingFileHandler
import os

# Configure logging
log_dir = "app/logs"
os.makedirs(log_dir, exist_ok=True)

file_handler = RotatingFileHandler(
    f"{log_dir}/app.log",
    maxBytes=10485760,  # 10MB
    backupCount=5
)
console_handler = logging.StreamHandler()
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler, console_handler]
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await MongoDB.connect_db()
    yield
    # Shutdown
    await MongoDB.close_db()

app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers following design flow
app.include_router(liveness.router)
app.include_router(kyc.router)
app.include_router(webhook.router)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/")
async def root():
    return {
        "message": "Biometric Verification API v1",
        "flows": {
            "liveness_detection": "BIO-008 to BIO-010",
            "kyc_verification": "BIO-011 to BIO-015"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )