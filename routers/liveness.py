# app/routers/liveness.py
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from services.verification_service import VerificationService
from utils.auth import verify_api_key
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/liveness", tags=["Face Liveness Detection"])

# Request/Response Models
class StartLivenessRequest(BaseModel):
    user_id: str
    metadata: Optional[dict] = None

class StartLivenessResponse(BaseModel):
    session_id: str
    status: str
    message: str = "Liveness detection session started"

class ProcessLivenessRequest(BaseModel):
    session_id: str
    image_base64: str
    check_type: str = "orientation"  # orientation, blink, etc

class ProcessLivenessResponse(BaseModel):
    is_live: bool
    confidence: float
    checks_passed: dict
    face_detected: bool
    message: str

class CompleteLivenessRequest(BaseModel):
    session_id: str
    user_id: str
    is_live: bool

class CompleteLivenessResponse(BaseModel):
    message: str
    status: str
    liveness_id: str

# BIO-008: Start Face Liveness Detection
@router.post("/start", response_model=StartLivenessResponse)
async def start_liveness_detection(
    request: StartLivenessRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    BIO-008: Initiate face liveness detection
    Returns session_id for next steps
    """
    try:
        service = VerificationService()
        result = await service.start_liveness_detection(request.user_id)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to start liveness detection")
            )
        
        return StartLivenessResponse(
            session_id=result["session_id"],
            status=result["status"]
        )
    except Exception as e:
        logger.error(f"Start liveness error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start liveness detection"
        )

# BIO-009: Process Face Liveness Check
@router.post("/check", response_model=ProcessLivenessResponse)
async def process_liveness_check(
    request: ProcessLivenessRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    BIO-009: Process face liveness check
    Supports: Look left, Blink, Look right
    """
    try:
        service = VerificationService()
        # Align router call with service implementation name
        result = await service.process_liveness_selfie(
            request.session_id,
            request.image_base64
        )
        
        if not result.get("success"):
            error_detail = result.get("error", "Liveness check failed")
            # 404 from our DB lookup
            if error_detail == "Session not found":
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Session not found. Call /api/v1/liveness/start and use the returned session_id."
                )
            # 404 bubbled from Sumsub (invalid applicant)
            if result.get("status_code") == 404 or "Status 404" in error_detail:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Applicant not found at Sumsub. Use the exact session_id returned by /liveness/start in this environment."
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_detail
            )
        
        return ProcessLivenessResponse(
            is_live=result.get("is_live", False),
            confidence=result.get("confidence", 0),
            checks_passed=result.get("checks_passed", {}),
            face_detected=result.get("face_detected", False),
            message="Liveness check completed"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Liveness check error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Liveness check failed"
        )

# BIO-010: Complete Liveness Enrollment
@router.post("/complete", response_model=CompleteLivenessResponse)
async def complete_liveness_enrollment(
    request: CompleteLivenessRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    BIO-010: Complete liveness enrollment
    Returns: "Liveness Enrolled Successfully"
    """
    try:
        service = VerificationService()
        # Align router call with service implementation signature
        result = await service.complete_liveness_enrollment(
            request.session_id,
            request.user_id
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to complete liveness")
            )
        
        return CompleteLivenessResponse(
            message=result.get("message", "Liveness Enrolled Successfully"),
            status=result.get("status", "completed"),
            liveness_id=request.session_id
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Complete liveness error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete liveness enrollment"
        )

# Get Liveness Status
@router.get("/status/{user_id}")
async def get_liveness_status(
    user_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Get user's liveness verification status"""
    try:
        service = VerificationService()
        status_data = await service.get_user_verification_status(user_id)
        return status_data
    except Exception as e:
        logger.error(f"Get liveness status error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get liveness status"
        )

# Check Advanced Liveness Result
@router.get("/result/{session_id}")
async def check_liveness_result(
    session_id: str,
    api_key: str = Depends(verify_api_key)
):
    """
    BIO-009: Check advanced face liveness verification result
    Polls Sumsub for active liveness check status (look left, blink, look right)
    Status: approved/rejected/pending
    """
    try:
        service = VerificationService()
        result = await service.check_liveness_status(session_id)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.get("error", "Failed to check liveness result")
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Check liveness result error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check liveness result"
        )