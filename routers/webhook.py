# app/routers/webhook.py
"""
Webhook endpoints for handling SumSub callbacks
"""

from fastapi import APIRouter, Request, HTTPException, status
from pydantic import BaseModel
from typing import Optional, Dict, Any
from services.verification_service import VerificationService
from config import settings
import logging
import hmac
import hashlib
import json

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["Webhook"])


class WebhookPayload(BaseModel):
    """SumSub Webhook Payload"""
    externalUserId: str
    applicantId: str
    inspectionId: Optional[str] = None
    correlationId: Optional[str] = None
    levelName: str
    reviewStatus: str  # approved, rejected, pending
    reviewResult: Optional[Dict[str, Any]] = None
    verificationResult: Optional[Dict[str, Any]] = None


def verify_webhook_signature(body: bytes, signature: str) -> bool:
    """
    Verify SumSub webhook signature using HMAC-SHA256
    SumSub sends: X-Webhook-Signature header with signature
    """
    try:
        if not signature:
            logger.warning("Missing signature header")
            return False
        
        secret_key = str(settings.SUMSUB_SECRET_KEY).strip()
        if not secret_key or secret_key == "":
            logger.error("SUMSUB_SECRET_KEY not configured. Check .env file and restart the server.")
            return False
        
        # Calculate expected signature
        expected_signature = hmac.new(
            secret_key.encode('utf-8'),
            body,
            hashlib.sha256
        ).hexdigest()
        
        # Compare signatures
        is_valid = hmac.compare_digest(signature, expected_signature)
        
        if not is_valid:
            logger.warning(f"Signature mismatch. Received: {signature}, Expected: {expected_signature}")
        
        return is_valid
    except Exception as e:
        logger.error(f"Signature verification error: {str(e)}")
        return False


@router.post("/webhook/sumsub")
async def sumsub_webhook(request: Request):
    """
    Handle SumSub webhook callbacks for verification results
    
    Events:
    - Liveness verification completed
    - KYC verification completed  
    - Document review completed
    """
    try:
        # Get raw body for signature verification
        body = await request.body()
        
        # Verify webhook signature
        signature = request.headers.get("X-Webhook-Signature", "")
        if not verify_webhook_signature(body, signature):
            logger.warning("Webhook signature verification failed")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature"
            )
        
        # Parse payload
        data = json.loads(body.decode('utf-8'))
        external_user_id = data.get("externalUserId", "")
        applicant_id = data.get("applicantId", "")
        review_status = data.get("reviewStatus", "")
        
        logger.info(f"Webhook received for user: {external_user_id}, status: {review_status}")
        
        # Initialize service
        service = VerificationService()
        
        # Update verification result based on user type
        if "liveness" in external_user_id.lower():
            result = await service.update_liveness_webhook_result(
                external_user_id=external_user_id,
                applicant_id=applicant_id,
                review_status=review_status,
                webhook_data=data
            )
        else:
            result = await service.update_kyc_webhook_result(
                external_user_id=external_user_id,
                applicant_id=applicant_id,
                review_status=review_status,
                webhook_data=data
            )
        
        if not result.get("success"):
            logger.error(f"Failed to process webhook: {result.get('error')}")
            return {
                "status": "error",
                "message": result.get("error", "Failed to process webhook")
            }
        
        logger.info(f"Webhook processed successfully for {external_user_id}")
        return {
            "status": "success",
            "message": "Webhook processed",
            "external_user_id": external_user_id
        }
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in webhook: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload"
        )
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing failed"
        )


@router.get("/webhook/health")
async def webhook_health():
    """Health check for webhook endpoint"""
    return {
        "status": "healthy",
        "message": "Webhook endpoint is operational"
    }
