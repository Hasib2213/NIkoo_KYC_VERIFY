# KYC Check Nikoo - Biometric Verification API

A FastAPI-based biometric verification system that implements face liveness detection and KYC (Know Your Customer) verification using Sumsub integration.

## Overview

This application provides APIs for:
- **Face Liveness Detection** (BIO-008 to BIO-010): Verify that a user is alive and present
- **KYC Verification** (BIO-011 to BIO-015): Document verification and identity checks

## Project Structure

```
KYC_Check_Nikoo/
├── config.py              # Configuration settings
├── main.py                # FastAPI application entry point
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables
├── app/
│   └── logs/             # Application logs
├── database/
│   ├── __init__.py
│   └── mongodb.py        # MongoDB connection & management
├── models/
│   ├── __init__.py
│   └── schemas.py        # Pydantic models & schemas
├── routers/
│   ├── __init__.py
│   ├── liveness.py       # Liveness detection endpoints
│   └── kyc.py            # KYC verification endpoints
├── services/
│   ├── __init__.py
│   ├── sumsub_service.py # Sumsub API integration
│   └── verification_service.py # Verification business logic
└── utils/
    ├── __init__.py
    ├── auth.py           # API key authentication
    └── exceptions.py     # Custom exceptions
```

## Key Components

### 1. Configuration (config.py)
Manages application settings using Pydantic BaseSettings:
- API configuration
- MongoDB connection details
- Sumsub API credentials
- Security settings (JWT tokens)
- Verification thresholds and limits

### 2. Database (database/mongodb.py)
- Async MongoDB connection using Motor
- Collection management
- Connection lifecycle handling

### 3. Models (models/schemas.py)
Defines Pydantic models for:
- `LivenessVerificationRequest/Response`
- `DocumentVerificationRequest/Response`
- `VerificationHistory`
- `VerificationStatus` enum

### 4. Services

#### Sumsub Service (services/sumsub_service.py)
Handles Sumsub API integration:
- **Liveness Flow** (BIO-008 to BIO-010):
  - `start_liveness_session()`: Initiate liveness session
  - `add_liveness_selfie()`: Process selfie with liveness checks
  - `complete_liveness_verification()`: Complete enrollment
  
- **KYC Flow** (BIO-011 to BIO-015):
  - `create_kyc_applicant()`: Start KYC process
  - `upload_document()`: Upload identity documents
  - `verify_selfie()`: Verify face matches document
  - `check_kyc_status()`: Get verification status

- **Signature & Authentication**:
  - HMAC-SHA256 request signing for Sumsub API
  - Timestamp-based signatures

#### Verification Service (services/verification_service.py)
Business logic layer:
- Orchestrates between Sumsub and Database
- Manages session states
- Updates user verification status
- Handles both liveness and KYC flows

### 5. API Routers

#### Liveness Router (routers/liveness.py)
- `POST /api/v1/liveness/start` - BIO-008: Start liveness detection
- `POST /api/v1/liveness/check` - BIO-009: Process liveness checks
- `POST /api/v1/liveness/complete` - BIO-010: Complete enrollment

#### KYC Router (routers/kyc.py)
- `POST /api/v1/liveness/start` - BIO-008: Start Face Liveness
- `POST /api/v1/liveness/check` - BIO-009: Process Face Liveness
- `POST /api/v1/liveness/complete` - BIO-010: Complete Liveness
- `POST /api/v1/kyc/start` - BIO-011: Start KYC Verification
- `POST /api/v1/kyc/scan-document` - BIO-012: Document Scanning
- `POST /api/v1/kyc/verify-selfie` - BIO-013: Selfie Verification
- `POST /api/v1/kyc/check-status` - BIO-014: Check verification status
- `POST /api/v1/kyc/complete` - BIO-015: Complete KYC verification

### 6. Utilities

#### Auth (utils/auth.py)
- API Key authentication via `X-API-Key` header
- `verify_api_key()` dependency

#### Exceptions (utils/exceptions.py)
Custom HTTP exceptions:
- `InvalidAPIKeyException` (401)
- `VerificationException` (400)
- `VerificationFailedException` (400)
- `DocumentVerificationException` (400)

## Installation

### Prerequisites
- Python 3.8+
- MongoDB (local or cloud)
- Sumsub API credentials

### Setup Steps

1. **Clone or setup the project**
```bash
cd KYC_Check_Nikoo
```

2. **Create virtual environment** (optional but recommended)
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
Create a `.env` file based on `.env.example`:
```bash
cp .env.example .env
```

Edit `.env` with your configuration:
```env
# API Configuration
API_TITLE=Biometric Verification API
API_VERSION=1.0.0
DEBUG=False

# MongoDB
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=biometric_db

# Sumsub API
SUMSUB_API_KEY=your_api_key_here
SUMSUB_SECRET_KEY=your_secret_key_here
SUMSUB_APP_TOKEN=your_app_token_here
SUMSUB_LEVEL_NAME=your_level_name_here
SUMSUB_BASE_URL=https://api.sumsub.io

# Security
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Verification Settings
LIVENESS_CONFIDENCE_THRESHOLD=0.85
DOCUMENT_CONFIDENCE_THRESHOLD=0.80
MAX_FILE_SIZE=10485760
REQUEST_TIMEOUT=30
```

5. **Ensure MongoDB is running**
```bash
# If using local MongoDB
mongod
```

## Running the Application

### Development Server
```bash
python main.py
# or
uvicorn app.main:app --reload
```

Server runs at: `http://localhost:8000`

### API Documentation
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Health Check
```bash
curl http://localhost:8000/health
```

## API Usage Examples

### 1. Start Liveness Detection
```bash
curl -X POST http://localhost:8000/api/v1/liveness/start \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key" \
  -d '{"user_id": "user123"}'
```

**Response:**
```json
{
  "session_id": "session_12345",
  "status": "initiated",
  "message": "Liveness detection session started"
}
```

### 2. Process Liveness Check
```bash
curl -X POST http://localhost:8000/api/v1/liveness/check \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key" \
  -d {
    "session_id": "session_12345",
    "image_base64": "base64_encoded_image",
    "check_type": "orientation"
  }'
```

**Response:**
```json
{
  "is_live": true,
  "confidence": 0.95,
  "checks_passed": {"orientation": true, "blink": true},
  "face_detected": true,
  "message": "Liveness check completed"
}
```

### 3. Complete Liveness Enrollment
```bash
curl -X POST http://localhost:8000/api/v1/liveness/complete \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key" \
  -d {
    "session_id": "session_12345",
    "user_id": "user123",
    "is_live": true
  }'
```

**Response:**
```json
{
  "message": "Liveness Enrolled Successfully",
  "status": "completed",
  "liveness_id": "session_12345"
}
```

## Database Schema

### Collections

#### `liveness_sessions`
```json
{
  "_id": "ObjectId",
  "session_id": "string",
  "user_id": "string",
  "external_user_id": "string",
  "verification_type": "liveness",
  "status": "initiated|completed|failed",
  "selfie_added": "boolean",
  "is_live": "boolean",
  "confidence": "float",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

#### `kyc_sessions`
```json
{
  "_id": "ObjectId",
  "kyc_session_id": "string",
  "user_id": "string",
  "external_user_id": "string",
  "verification_type": "kyc",
  "status": "initiated|pending|completed|rejected",
  "steps_completed": ["array"],
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

#### `users`
```json
{
  "_id": "ObjectId",
  "user_id": "string",
  "liveness_completed": "boolean",
  "liveness_session_id": "string",
  "kyc_completed": "boolean",
  "kyc_session_id": "string",
  "updated_at": "datetime"
}
```

## Dependencies

- **fastapi**: Web framework
- **uvicorn**: ASGI server
- **motor**: Async MongoDB driver
- **pymongo**: MongoDB driver
- **pydantic**: Data validation
- **pydantic-settings**: Settings management
- **requests**: HTTP client
- **httpx**: Async HTTP client
- **python-jose**: JWT handling
- **passlib**: Password hashing
- **python-dotenv**: Environment variables
- **Pillow**: Image processing
- **aiofiles**: Async file handling

## Error Handling

All endpoints return appropriate HTTP status codes:
- `200`: Success
- `201`: Created
- `400`: Bad Request / Validation Error
- `401`: Unauthorized (Invalid API Key)
- `500`: Internal Server Error

Error response format:
```json
{
  "detail": "Error message describing what went wrong"
}
```

## Logging

Application logs are stored in `app/logs/app.log` with:
- Log rotation (10MB per file, 5 backup files)
- Console and file output
- Format: `timestamp - logger - level - message`

## Security Considerations

1. **API Key Authentication**: All endpoints require valid `X-API-Key` header
2. **HMAC-SHA256 Signing**: Sumsub requests are signed with timestamp-based signatures
3. **JWT Tokens**: Configurable expiration (default 30 minutes)
4. **Environment Variables**: Sensitive data stored in `.env` file (not version controlled)
5. **CORS**: Configured to allow all origins (can be restricted)

## Development

### Adding a New Endpoint

1. Create request/response models in `models/schemas.py`
2. Implement business logic in `services/`
3. Create endpoint in appropriate router (`routers/liveness.py` or `routers/kyc.py`)
4. Add dependency injection for `verify_api_key`

### Testing

Run endpoints using Swagger UI at `http://localhost:8000/docs`

## Troubleshooting

### MongoDB Connection Error
- Ensure MongoDB is running
- Check `MONGODB_URL` in `.env`
- Verify network connectivity

### Sumsub API Errors
- Validate API credentials in `.env`
- Check request signatures (HMAC-SHA256)
- Ensure correct endpoint URLs
- Verify request body format

### 401 Unauthorized
- Check `X-API-Key` header is present
- Verify API key matches `SUMSUB_API_KEY` in config

### Request Timeout
- Increase `REQUEST_TIMEOUT` in `.env`
- Check network connectivity
- Verify Sumsub API is accessible

## License

Proprietary - All rights reserved

## Support

For issues or questions, contact the development team.
