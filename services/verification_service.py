# app/services/verification_service.py
"""
Verification Service following Design Flow:
BIO-008 to BIO-010: Liveness Detection
BIO-011 to BIO-015: KYC Verification
"""

from database.mongodb import MongoDB
from services.sumsub_service import SumsubService
from models.schemas import VerificationStatus
from datetime import datetime
import logging
from typing import Optional, Union
import uuid
import base64

logger = logging.getLogger(__name__)

class VerificationService:
    """
    Main service following complete design flow
    """
    
    def __init__(self):
        self.sumsub = SumsubService()
        self.liveness_sessions = MongoDB.get_collection("liveness_sessions")
        self.kyc_sessions = MongoDB.get_collection("kyc_sessions")
        self.users_collection = MongoDB.get_collection("users")
    
    # ==================== LIVENESS FLOW (BIO-008 to BIO-010) ====================
    
    async def start_liveness_detection(self, user_id: str) -> dict:
        """BIO-008: Start Face Liveness Detection"""
        try:
            result = await self.sumsub.start_liveness_session(user_id)
            
            if result.get("success"):
                session_doc = {
                    "session_id": result["session_id"],
                    "user_id": user_id,
                    "external_user_id": result["external_user_id"],
                    "verification_type": "liveness",
                    "status": "initiated",
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                await self.liveness_sessions.insert_one(session_doc)
                
                return {
                    "success": True,
                    "session_id": result["session_id"],
                    "status": "initiated"
                }
            
            return result
        except Exception as e:
            logger.error(f"Start liveness error: {str(e)}")
            raise
    
    async def process_liveness_selfie(
        self, 
        session_id: str,
        image_base64: str
    ) -> dict:
        """BIO-009: Process Face Liveness Check (Look left, Blink, Look right)"""
        try:
            # Get session
            session = await self.liveness_sessions.find_one({"session_id": session_id})
            if not session:
                return {"success": False, "error": "Session not found"}
            
            applicant_id = session["session_id"]
            
            # Decode base64 with proper padding
            try:
                missing_padding = len(image_base64) % 4
                if missing_padding:
                    image_base64 += '=' * (4 - missing_padding)
                image_bytes = base64.b64decode(image_base64)
            except Exception as decode_error:
                logger.error(f"Base64 decode error: {str(decode_error)}")
                return {"success": False, "error": f"Invalid base64 image: {str(decode_error)}"}
            
            result = await self.sumsub.add_liveness_selfie(applicant_id, image_bytes)
            
            if result.get("success"):
                await self.liveness_sessions.update_one(
                    {"session_id": session_id},
                    {"$set": {
                        "selfie_added": True,
                        "is_live": result.get("is_live"),
                        "confidence": result.get("confidence"),
                        "updated_at": datetime.utcnow()
                    }}
                )
            
            return result
        except Exception as e:
            logger.error(f"Process liveness error: {str(e)}")
            raise
    
    async def complete_liveness_enrollment(
        self,
        session_id: str,
        user_id: str
    ) -> dict:
        """BIO-010: Complete Liveness Enrollment → 'Liveness Enrolled Successfully'"""
        try:
            session = await self.liveness_sessions.find_one({"session_id": session_id})
            if not session:
                return {"success": False, "error": "Session not found"}
            
            applicant_id = session["session_id"]
            result = await self.sumsub.complete_liveness_verification(applicant_id)
            
            if result.get("success"):
                await self.liveness_sessions.update_one(
                    {"session_id": session_id},
                    {"$set": {
                        "status": "completed",
                        "is_live": True,
                        "updated_at": datetime.utcnow()
                    }}
                )
                
                # Update user
                await self.users_collection.update_one(
                    {"user_id": user_id},
                    {"$set": {
                        "liveness_completed": True,
                        "liveness_session_id": session_id,
                        "updated_at": datetime.utcnow()
                    }},
                    upsert=True
                )
            
            return result
        except Exception as e:
            logger.error(f"Complete liveness error: {str(e)}")
            raise
    
    # ==================== KYC FLOW (BIO-011 to BIO-015) ====================
    
    async def start_kyc_verification(self, user_id: str) -> dict:
        """BIO-011: Start KYC Verification"""
        try:
            result = await self.sumsub.create_kyc_applicant(user_id)
            
            if result.get("success"):
                session_doc = {
                    "kyc_session_id": result["kyc_session_id"],
                    "user_id": user_id,
                    "external_user_id": result["external_user_id"],
                    "verification_type": "kyc",
                    "status": "initiated",
                    "steps_completed": [],
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                await self.kyc_sessions.insert_one(session_doc)
                
                return {
                    "success": True,
                    "kyc_session_id": result["kyc_session_id"],
                    "status": "initiated"
                }
            
            return result
        except Exception as e:
            logger.error(f"Start KYC error: {str(e)}")
            raise
    
    async def scan_document_front(
        self,
        kyc_session_id: str,
        image: Union[bytes, bytearray, str],
        doc_type: str = "PASSPORT",
        country: str = "USA"
    ) -> dict:
        """BIO-012: Scan ID - Front (accepts bytes or base64)"""
        try:
            session = await self.kyc_sessions.find_one({"kyc_session_id": kyc_session_id})
            if not session:
                return {"success": False, "error": "KYC session not found"}

            # Normalize payload to bytes
            try:
                if isinstance(image, str):
                    missing_padding = len(image) % 4
                    if missing_padding:
                        image += "=" * (4 - missing_padding)
                    image_bytes = base64.b64decode(image)
                elif isinstance(image, (bytes, bytearray)):
                    image_bytes = bytes(image)
                else:
                    return {"success": False, "error": "Invalid image payload"}
            except Exception as decode_error:
                logger.error(f"Base64 decode error: {str(decode_error)}")
                return {"success": False, "error": f"Invalid image data: {str(decode_error)}"}

            applicant_id = kyc_session_id
            result = await self.sumsub.scan_document_front(
                applicant_id,
                image_bytes,
                doc_type,
                country
            )

            if result.get("success"):
                await self.kyc_sessions.update_one(
                    {"kyc_session_id": kyc_session_id},
                    {"$set": {
                        "document_front_added": True,
                        "document_type": doc_type,
                        "country": country,
                        "updated_at": datetime.utcnow()
                    },
                    "$push": {"steps_completed": "document_front"}}
                )

            return result
        except Exception as e:
            logger.error(f"Scan document front error: {str(e)}", exc_info=True)
            raise
    
    
    async def verify_kyc_selfie(
        self,
        kyc_session_id: str,
        image_base64: str
    ) -> dict:
        """BIO-013: Take a Selfie and match with document"""
        try:
            session = await self.kyc_sessions.find_one({"kyc_session_id": kyc_session_id})
            if not session:
                return {"success": False, "error": "KYC session not found"}
            
            applicant_id = kyc_session_id
            
            # Decode base64 with proper padding
            try:
                missing_padding = len(image_base64) % 4
                if missing_padding:
                    image_base64 += '=' * (4 - missing_padding)
                image_bytes = base64.b64decode(image_base64)
            except Exception as decode_error:
                logger.error(f"Base64 decode error: {str(decode_error)}")
                return {"success": False, "error": f"Invalid base64 image: {str(decode_error)}"}
            
            result = await self.sumsub.verify_kyc_selfie(applicant_id, image_bytes)
            
            if result.get("success"):
                await self.kyc_sessions.update_one(
                    {"kyc_session_id": kyc_session_id},
                    {"$set": {
                        "selfie_added": True,
                        "matches_document": result.get("matches_document"),
                        "face_match_score": result.get("face_match_score"),
                        "updated_at": datetime.utcnow()
                    },
                    "$push": {"steps_completed": "selfie"}}
                )
            
            return result
        except Exception as e:
            logger.error(f"Verify selfie error: {str(e)}")
            raise
    
    async def check_kyc_verification_status(self, kyc_session_id: str) -> dict:
        """BIO-014: Verification in Progress"""
        try:
            session = await self.kyc_sessions.find_one({"kyc_session_id": kyc_session_id})
            if not session:
                return {"success": False, "error": "KYC session not found"}
            
            result = await self.sumsub.check_kyc_status(kyc_session_id)
            return result
        except Exception as e:
            logger.error(f"Check KYC status error: {str(e)}")
            raise
    
    async def complete_kyc_verification(self, kyc_session_id: str, user_id: str) -> dict:
        """BIO-015: KYC Approved - Complete verification"""
        try:
            session = await self.kyc_sessions.find_one({"kyc_session_id": kyc_session_id})
            if not session:
                return {"success": False, "error": "KYC session not found"}
            
            applicant_id = kyc_session_id
            result = await self.sumsub.complete_kyc_verification(applicant_id)
            
            if result.get("success"):
                await self.kyc_sessions.update_one(
                    {"kyc_session_id": kyc_session_id},
                    {"$set": {
                        "status": "completed",
                        "verified": True,
                        "updated_at": datetime.utcnow()
                    },
                    "$push": {"steps_completed": "kyc_complete"}}
                )
                
                # Update user
                await self.users_collection.update_one(
                    {"user_id": user_id},
                    {"$set": {
                        "kyc_completed": True,
                        "verified": True,
                        "kyc_session_id": kyc_session_id,
                        "updated_at": datetime.utcnow()
                    }},
                    upsert=True
                )
            
            return result
        except Exception as e:
            logger.error(f"Complete KYC error: {str(e)}")
            raise
    
    async def scan_document_back(
        self,
        kyc_session_id: str,
        image: Union[bytes, bytearray, str],
        doc_type: str = "PASSPORT",
        country: str = "USA"
    ) -> dict:
        """BIO-012: Scan ID - Back (accepts bytes or base64)"""
        try:
            session = await self.kyc_sessions.find_one({"kyc_session_id": kyc_session_id})
            if not session:
                return {"success": False, "error": "KYC session not found"}

            try:
                if isinstance(image, str):
                    missing_padding = len(image) % 4
                    if missing_padding:
                        image += "=" * (4 - missing_padding)
                    image_bytes = base64.b64decode(image)
                elif isinstance(image, (bytes, bytearray)):
                    image_bytes = bytes(image)
                else:
                    return {"success": False, "error": "Invalid image payload"}
            except Exception as decode_error:
                logger.error(f"Base64 decode error: {str(decode_error)}")
                return {"success": False, "error": f"Invalid image data: {str(decode_error)}"}

            applicant_id = kyc_session_id
            result = await self.sumsub.scan_document_back(
                applicant_id,
                image_bytes,
                doc_type,
                country
            )

            if result.get("success"):
                await self.kyc_sessions.update_one(
                    {"kyc_session_id": kyc_session_id},
                    {"$set": {
                        "document_back_added": True,
                        "document_type": doc_type,
                        "country": country,
                        "updated_at": datetime.utcnow()
                    },
                    "$push": {"steps_completed": "document_back"}}
                )

            return result
        except Exception as e:
            logger.error(f"Scan document back error: {str(e)}")
            raise
    
    async def get_user_verification_status(self, user_id: str) -> dict:
        """Get overall verification status following design"""
        try:
            user = await self.users_collection.find_one({"user_id": user_id})
            
            liveness_session = await self.liveness_sessions.find_one(
                {"user_id": user_id},
                sort=[("created_at", -1)]
            )
            
            kyc_session = await self.kyc_sessions.find_one(
                {"user_id": user_id},
                sort=[("created_at", -1)]
            )
            
            return {
                "user_id": user_id,
                "overall_status": "verified" if user and user.get("verified") else "not_started",
                "verified": user.get("verified", False) if user else False,
                "liveness": {
                    "status": "completed" if liveness_session and liveness_session.get("status") == "completed" else "pending",
                    "is_live": liveness_session.get("is_live") if liveness_session else None,
                    "completed_at": liveness_session.get("updated_at") if liveness_session else None,
                    "message": "Liveness Enrolled Successfully" if liveness_session and liveness_session.get("status") == "completed" else None
                },
                "kyc": {
                    "status": "completed" if kyc_session and kyc_session.get("status") == "completed" else "pending",
                    "verified": kyc_session.get("verified", False) if kyc_session else False,
                    "completed_at": kyc_session.get("updated_at") if kyc_session else None,
                    "message": "KYC Approved" if kyc_session and kyc_session.get("verified") else None
                }
            }
        except Exception as e:
            logger.error(f"Get user status error: {str(e)}")
            raise
    
    # ==================== WEBHOOK HANDLERS ====================
    
    async def update_liveness_webhook_result(
        self,
        external_user_id: str,
        applicant_id: str,
        review_status: str,
        webhook_data: dict
    ) -> dict:
        """Handle webhook response from SumSub for liveness verification"""
        try:
            # Find session by external_user_id
            session = await self.liveness_sessions.find_one(
                {"external_user_id": external_user_id}
            )
            
            if not session:
                logger.warning(f"Liveness session not found for {external_user_id}")
                return {"success": False, "error": "Session not found"}
            
            # Update session based on review status
            status_map = {
                "approved": "completed",
                "rejected": "failed",
                "pending": "pending"
            }
            
            session_status = status_map.get(review_status, "pending")
            is_live = review_status == "approved"
            
            await self.liveness_sessions.update_one(
                {"_id": session["_id"]},
                {"$set": {
                    "status": session_status,
                    "is_live": is_live,
                    "review_status": review_status,
                    "webhook_data": webhook_data,
                    "updated_at": datetime.utcnow()
                }}
            )
            
            # Update user
            user_id = session.get("user_id")
            if user_id:
                await self.users_collection.update_one(
                    {"user_id": user_id},
                    {"$set": {
                        "liveness_completed": session_status == "completed",
                        "liveness_verified": is_live,
                        "liveness_review_status": review_status,
                        "updated_at": datetime.utcnow()
                    }},
                    upsert=True
                )
            
            logger.info(f"Liveness webhook processed: {external_user_id} - {review_status}")
            return {
                "success": True,
                "message": f"Liveness verification {review_status}"
            }
            
        except Exception as e:
            logger.error(f"Liveness webhook error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def update_kyc_webhook_result(
        self,
        external_user_id: str,
        applicant_id: str,
        review_status: str,
        webhook_data: dict
    ) -> dict:
        """Handle webhook response from SumSub for KYC verification"""
        try:
            # Find session by external_user_id (without the liveness prefix)
            session = await self.kyc_sessions.find_one(
                {"external_user_id": external_user_id}
            )
            
            if not session:
                logger.warning(f"KYC session not found for {external_user_id}")
                return {"success": False, "error": "KYC session not found"}
            
            # Update session based on review status
            status_map = {
                "approved": "completed",
                "rejected": "failed",
                "pending": "pending"
            }
            
            session_status = status_map.get(review_status, "pending")
            is_verified = review_status == "approved"
            
            await self.kyc_sessions.update_one(
                {"_id": session["_id"]},
                {"$set": {
                    "status": session_status,
                    "verified": is_verified,
                    "review_status": review_status,
                    "webhook_data": webhook_data,
                    "updated_at": datetime.utcnow()
                }}
            )
            
            # Update user
            user_id = session.get("user_id")
            if user_id:
                await self.users_collection.update_one(
                    {"user_id": user_id},
                    {"$set": {
                        "kyc_completed": session_status == "completed",
                        "verified": is_verified,
                        "kyc_review_status": review_status,
                        "updated_at": datetime.utcnow()
                    }},
                    upsert=True
                )
            
            logger.info(f"KYC webhook processed: {external_user_id} - {review_status}")
            return {
                "success": True,
                "message": f"KYC verification {review_status}"
            }
            
        except Exception as e:
            logger.error(f"KYC webhook error: {str(e)}")
            return {"success": False, "error": str(e)}
