# app/utils/exceptions.py
from fastapi import HTTPException, status

class VerificationException(HTTPException):
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail=detail)

class InvalidAPIKeyException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key"
        )

class VerificationFailedException(HTTPException):
    def __init__(self, detail: str = "Verification failed"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

class DocumentVerificationException(HTTPException):
    def __init__(self, detail: str = "Document verification failed"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
