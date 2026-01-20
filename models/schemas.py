# app/models/schemas.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

class VerificationStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"

class LivenessVerificationRequest(BaseModel):
    user_id: str
    image_base64: str
    metadata: Optional[Dict[str, Any]] = None

class LivenessVerificationResponse(BaseModel):
    verification_id: str
    status: VerificationStatus
    is_live: bool
    confidence: float
    message: str
    timestamp: datetime

class DocumentVerificationRequest(BaseModel):
    user_id: str
    document_type: str  # passport, driver_license, national_id
    front_image_base64: str
    back_image_base64: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class DocumentVerificationResponse(BaseModel):
    verification_id: str
    status: VerificationStatus
    document_valid: bool
    confidence: float
    extracted_data: Optional[Dict[str, Any]]
    message: str
    timestamp: datetime

class VerificationHistory(BaseModel):
    user_id: str
    verification_type: str  # liveness or document
    status: VerificationStatus
    confidence: float
    timestamp: datetime
    details: Dict[str, Any]