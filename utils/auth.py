# app/utils/auth.py
from fastapi import Depends, status
from fastapi.security import APIKeyHeader
from utils.exceptions import InvalidAPIKeyException
from config import settings

api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Depends(api_key_header)) -> str:
    if api_key != settings.SUMSUB_API_KEY:
        raise InvalidAPIKeyException()
    return api_key