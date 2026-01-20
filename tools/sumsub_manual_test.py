#!/usr/bin/env python3
"""
Manual Sumsub API Test - Validates full KYC flow with ACTUAL multipart body signing
Follows official Sumsub pattern for document upload signature
"""

import os
import sys
import json
import time
import hashlib
import hmac
from io import BytesIO
from pathlib import Path
from dotenv import load_dotenv

import requests

# Load environment
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

SUMSUB_SECRET_KEY = os.getenv("SUMSUB_SECRET_KEY")
SUMSUB_APP_TOKEN = os.getenv("SUMSUB_APP_TOKEN")
SUMSUB_BASE_URL = os.getenv("SUMSUB_BASE_URL", "https://api.sandbox.sumsub.com")
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "60"))
SUMSUB_LEVEL_NAME = os.getenv("SUMSUB_LEVEL_NAME", "basic-kyc-level")

print("=" * 80)
print("SUMSUB MANUAL TEST - Full KYC Flow with Correct Multipart Signing")
print("=" * 80)

# 1. VALIDATE CREDENTIALS
print("\n[1/5] CREDENTIAL VALIDATION")
print("-" * 80)

if not SUMSUB_SECRET_KEY or not SUMSUB_APP_TOKEN:
    print("❌ ERROR: Missing SUMSUB_SECRET_KEY or SUMSUB_APP_TOKEN in .env")
    sys.exit(1)

print(f"✅ SUMSUB_SECRET_KEY: {SUMSUB_SECRET_KEY[:10]}... (length: {len(SUMSUB_SECRET_KEY)})")
print(f"✅ SUMSUB_APP_TOKEN: {SUMSUB_APP_TOKEN[:15]}...")
print(f"✅ SUMSUB_BASE_URL: {SUMSUB_BASE_URL}")
print(f"✅ SUMSUB_LEVEL_NAME: {SUMSUB_LEVEL_NAME}")

# 2. CREATE APPLICANT
print("\n[2/5] CREATE APPLICANT")
print("-" * 80)

def sign_request_old(method, path_url, body=b''):
    """Sign with empty body (old, buggy way)"""
    now = int(time.time())
    data_to_sign = (
        str(now).encode('utf-8') +
        method.upper().encode('utf-8') +
        path_url.encode('utf-8') +
        body
    )
    signature = hmac.new(
        SUMSUB_SECRET_KEY.encode('utf-8'),
        data_to_sign,
        digestmod=hashlib.sha256
    ).hexdigest()
    
    headers = {
        'X-App-Token': SUMSUB_APP_TOKEN,
        'X-App-Access-Ts': str(now),
        'X-App-Access-Sig': signature,
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }
    return headers

import uuid
external_user_id = f"test_{uuid.uuid4().hex[:12]}"

create_body = json.dumps({'externalUserId': external_user_id})
path = f'/resources/applicants?levelName={SUMSUB_LEVEL_NAME}'
headers = sign_request_old('POST', path, create_body.encode('utf-8'))

response = requests.post(
    f"{SUMSUB_BASE_URL}{path}",
    headers=headers,
    data=create_body,
    timeout=REQUEST_TIMEOUT
)

print(f"Request: POST {SUMSUB_BASE_URL}{path}")
print(f"Status: {response.status_code}")

if response.status_code != 201:
    print(f"❌ Failed to create applicant: {response.text}")
    sys.exit(1)

applicant_data = response.json()
applicant_id = applicant_data['id']
print(f"✅ Applicant created: {applicant_id}")
print(f"   External User ID: {external_user_id}")

# 3. CREATE TEST IMAGE
print("\n[3/5] CREATE TEST IMAGE")
print("-" * 80)

# Download sample image from web
try:
    img_response = requests.get(
        'https://fv2-1.failiem.lv/thumb_show.php?i=gdmn9sqy&view',
        timeout=10
    )
    if img_response.status_code == 200:
        image_bytes = img_response.content
        print(f"✅ Downloaded test image: {len(image_bytes)} bytes")
    else:
        raise Exception("Download failed")
except Exception as e:
    print(f"⚠️  Could not download test image: {e}")
    print("   Creating minimal test JPG...")
    # Create minimal valid JPEG
    image_bytes = bytes([
        0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01,
        0x01, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0xFF, 0xD9
    ])
    print(f"   Created minimal JPEG: {len(image_bytes)} bytes")

# 4. UPLOAD DOCUMENT - OLD WAY (BUGGY)
print("\n[4/5] UPLOAD DOCUMENT - OLD METHOD (empty body signature)")
print("-" * 80)

path_doc = f'/resources/applicants/{applicant_id}/info/idDoc'
metadata = json.dumps({
    "idDocType": "PASSPORT",
    "country": "USA",
    "idDocSubType": "FRONT_SIDE"
})

# OLD BUGGY METHOD: sign with empty body
now = int(time.time())
data_to_sign_old = (
    str(now).encode('utf-8') +
    b'POST' +
    path_doc.encode('utf-8') +
    b''  # ← EMPTY BODY - WRONG!
)
signature_old = hmac.new(
    SUMSUB_SECRET_KEY.encode('utf-8'),
    data_to_sign_old,
    digestmod=hashlib.sha256
).hexdigest()

headers_old = {
    'X-App-Token': SUMSUB_APP_TOKEN,
    'X-App-Access-Ts': str(now),
    'X-App-Access-Sig': signature_old,
    'Accept': 'application/json',
}

files = {'content': ('front.jpg', BytesIO(image_bytes), 'image/jpeg')}
data = {'metadata': metadata}

response_old = requests.post(
    f"{SUMSUB_BASE_URL}{path_doc}",
    headers=headers_old,
    files=files,
    data=data,
    timeout=REQUEST_TIMEOUT
)

print(f"Request: POST {SUMSUB_BASE_URL}{path_doc}")
print(f"Method: empty body signature")
print(f"Status: {response_old.status_code}")

if response_old.status_code in [200, 201]:
    print(f"✅ Upload succeeded (lucky!)")
    image_id_old = response_old.headers.get('X-Image-Id', '')
    print(f"   Image ID: {image_id_old}")
else:
    print(f"❌ Upload failed (as expected)")
    print(f"   Error: {response_old.text[:200]}")

# 5. UPLOAD DOCUMENT - NEW WAY (CORRECT)
print("\n[5/5] UPLOAD DOCUMENT - NEW METHOD (ACTUAL multipart body signature)")
print("-" * 80)

# NEW CORRECT METHOD: sign with ACTUAL multipart body
full_url = f"{SUMSUB_BASE_URL}{path_doc}"
req = requests.Request('POST', full_url, files=files, data=data)
prepared = req.prepare()

now = int(time.time())
path_url = prepared.path_url

data_to_sign_new = (
    str(now).encode('utf-8') +
    b'POST' +
    path_url.encode('utf-8') +
    prepared.body  # ← ACTUAL multipart bytes - CORRECT!
)

signature_new = hmac.new(
    SUMSUB_SECRET_KEY.encode('utf-8'),
    data_to_sign_new,
    digestmod=hashlib.sha256
).hexdigest()

headers_new = {
    'X-App-Token': SUMSUB_APP_TOKEN,
    'X-App-Access-Ts': str(now),
    'X-App-Access-Sig': signature_new,
    'Accept': 'application/json',
    'X-Return-Doc-Warnings': 'true',
}

if 'Content-Type' in prepared.headers:
    headers_new['Content-Type'] = prepared.headers['Content-Type']

prepared.headers.update(headers_new)
session = requests.Session()
response_new = session.send(prepared, timeout=REQUEST_TIMEOUT)

print(f"Request: POST {SUMSUB_BASE_URL}{path_doc}")
print(f"Method: ACTUAL multipart body signature")
print(f"Multipart body size: {len(prepared.body)} bytes")
print(f"Status: {response_new.status_code}")

if response_new.status_code in [200, 201]:
    print(f"✅ Upload succeeded!")
    image_id_new = response_new.headers.get('X-Image-Id', '')
    print(f"   Image ID: {image_id_new}")
else:
    print(f"❌ Upload failed")
    print(f"   Error: {response_new.text[:200]}")

# COMPARISON
print("\n" + "=" * 80)
print("RESULT COMPARISON")
print("=" * 80)
print(f"Old method (empty body):      {response_old.status_code}")
print(f"New method (actual body):     {response_new.status_code}")

if response_new.status_code in [200, 201]:
    print("\n✅ SUCCESS: The fix works! Use the new method in production.")
    print("\nKey differences:")
    print(f"  Old signature: {signature_old[:40]}...")
    print(f"  New signature: {signature_new[:40]}...")
    print(f"\n  Timestamp: {now}")
    print(f"  Secret key length: {len(SUMSUB_SECRET_KEY)}")
    print(f"  Path URL: {path_url}")
    print(f"  Old body length: 0 bytes")
    print(f"  New body length: {len(prepared.body)} bytes")
elif response_old.status_code in [200, 201]:
    print("\n⚠️  WARNING: Old method worked but new method failed.")
    print("   This is unusual. Check if there's a regional/account-specific difference.")
else:
    print("\n❌ Both methods failed. Check credentials and network connectivity.")

print("\n" + "=" * 80)
