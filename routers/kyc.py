# app/routers/verification.py
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from services.verification_service import VerificationService
from utils.auth import verify_api_key
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["Verification"])

# ============ LIVENESS FLOW ============

class StartLivenessRequest(BaseModel):
    user_id: str

class StartLivenessResponse(BaseModel):
    session_id: str
    status: str

class ProcessLivenessRequest(BaseModel):
    session_id: str
    image_base64: str

class ProcessLivenessResponse(BaseModel):
    is_live: bool
    confidence: float
    message: str

class CompleteLivenessRequest(BaseModel):
    session_id: str
    user_id: str

class CompleteLivenessResponse(BaseModel):
    message: str
    status: str

# BIO-008 - DEPRECATED: Use /api/v1/liveness/start from liveness.py router instead
# All liveness endpoints moved to dedicated routers/liveness.py file

# BIO-009 - DEPRECATED: Use /api/v1/liveness/check from liveness.py router instead

# BIO-010 - DEPRECATED: Use /api/v1/liveness/complete from liveness.py router instead

# ============ KYC FLOW ============

class StartKYCRequest(BaseModel):
    user_id: str

class StartKYCResponse(BaseModel):
    kyc_session_id: str
    status: str

class ScanDocumentRequest(BaseModel):
    kyc_session_id: str
    image_base64: str
    doc_type: str = "PASSPORT"
    country: str = "USA"

class ScanDocumentResponse(BaseModel):
    image_id: str
    document_detected: bool
    message: str

class VerifySelfieRequest(BaseModel):
    kyc_session_id: str
    image_base64: str

class VerifySelfieResponse(BaseModel):
    image_id: str
    matches_document: bool
    face_match_score: float
    message: str

class CheckStatusResponse(BaseModel):
    status: str
    progress: int
    message: str

class CompleteKYCResponse(BaseModel):
    message: str
    status: str

# BIO-011
@router.post("/kyc/start", response_model=StartKYCResponse)
async def start_kyc(
    request: StartKYCRequest,
    api_key: str = Depends(verify_api_key)
):
    """BIO-011: Start KYC Verification"""
    try:
        service = VerificationService()
        result = await service.start_kyc_verification(request.user_id)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return StartKYCResponse(
            kyc_session_id=result["kyc_session_id"],
            status=result["status"]
        )
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed")

# BIO-012 Front
@router.post("/document/scan-front", response_model=ScanDocumentResponse)
async def scan_document_front(
    request: ScanDocumentRequest,
    api_key: str = Depends(verify_api_key)
):
    """BIO-012: Scan ID - Front"""
    try:
        service = VerificationService()
        result = await service.scan_document_front(
            request.kyc_session_id,
            request.image_base64,
            request.doc_type,
            request.country
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return ScanDocumentResponse(
            image_id=result["image_id"],
            document_detected=result.get("document_detected", False),
            message="Document front captured"
        )
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed")

# BIO-012 Back
@router.post("/document/scan-back", response_model=ScanDocumentResponse)
async def scan_document_back(
    request: ScanDocumentRequest,
    api_key: str = Depends(verify_api_key)
):
    """BIO-012: Scan ID - Back"""
    try:
        service = VerificationService()
        result = await service.scan_document_back(
            request.kyc_session_id,
            request.image_base64,
            request.doc_type,
            request.country
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return ScanDocumentResponse(
            image_id=result["image_id"],
            document_detected=result.get("document_detected", False),
            message="Document back captured"
        )
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed")

# BIO-013
@router.post("/selfie/verify", response_model=VerifySelfieResponse)
async def verify_selfie(
    request: VerifySelfieRequest,
    api_key: str = Depends(verify_api_key)
):
    """BIO-013: Take a Selfie"""
    try:
        service = VerificationService()
        result = await service.verify_kyc_selfie(
            request.kyc_session_id,
            request.image_base64
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return VerifySelfieResponse(
            image_id=result["image_id"],
            matches_document=result.get("matches_document", False),
            face_match_score=result.get("face_match_score", 0),
            message="Selfie verified"
        )
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed")

# BIO-014
@router.get("/kyc/status/{kyc_session_id}", response_model=CheckStatusResponse)
async def check_kyc_status(
    kyc_session_id: str,
    api_key: str = Depends(verify_api_key)
):
    """BIO-014: Verification in Progress"""
    try:
        service = VerificationService()
        result = await service.check_kyc_verification_status(kyc_session_id)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return CheckStatusResponse(
            status=result.get("status", "pending"),
            progress=result.get("progress", 0),
            message="Verification in progress"
        )
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed")

# BIO-015
@router.post("/kyc/complete", response_model=CompleteKYCResponse)
async def complete_kyc(
    kyc_session_id: str,
    user_id: str,
    api_key: str = Depends(verify_api_key)
):
    """BIO-015: KYC Approved"""
    try:
        service = VerificationService()
        result = await service.complete_kyc_verification(
            kyc_session_id,
            user_id
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return CompleteKYCResponse(
            message=result.get("message", "KYC Approved"),
            status=result.get("status", "approved")
        )
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed")

# Status Check
@router.get("/user/{user_id}/status")
async def get_user_status(
    user_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Get overall user verification status"""
    try:
        service = VerificationService()
        result = await service.get_user_verification_status(user_id)
        return result
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed")