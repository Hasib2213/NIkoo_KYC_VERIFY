#!/usr/bin/env python3
"""
Debug SumSub signature and request issues
Run this to identify the problem with 401 signature mismatch
"""

import os
import sys
import time
import hashlib
import hmac
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment
load_dotenv()

SUMSUB_SECRET_KEY = os.getenv("SUMSUB_SECRET_KEY")
SUMSUB_APP_TOKEN = os.getenv("SUMSUB_APP_TOKEN")
SUMSUB_BASE_URL = os.getenv("SUMSUB_BASE_URL", "https://api.sumsub.com")

print("=" * 60)
print("SumSub Signature Debug Tool")
print("=" * 60)

# 1. Check credentials
print("\n1. CREDENTIAL CHECK:")
print(f"   SECRET_KEY exists: {bool(SUMSUB_SECRET_KEY)}")
print(f"   SECRET_KEY length: {len(SUMSUB_SECRET_KEY) if SUMSUB_SECRET_KEY else 0}")
print(f"   APP_TOKEN exists: {bool(SUMSUB_APP_TOKEN)}")
print(f"   APP_TOKEN: {SUMSUB_APP_TOKEN[:10]}..." if SUMSUB_APP_TOKEN else "MISSING")
print(f"   BASE_URL: {SUMSUB_BASE_URL}")

if not SUMSUB_SECRET_KEY or not SUMSUB_APP_TOKEN:
    print("\n❌ ERROR: Missing SUMSUB_SECRET_KEY or SUMSUB_APP_TOKEN in .env file")
    sys.exit(1)

# 2. Check server time
print("\n2. SERVER TIME CHECK:")
server_time = int(time.time())
print(f"   Current Unix Timestamp: {server_time}")
print(f"   Current Time (UTC): {datetime.utcnow().isoformat()}")
print(f"   Current Time (Local): {datetime.now().isoformat()}")

# 3. Test signature calculation
print("\n3. SIGNATURE CALCULATION TEST:")

path = "/resources/applicants/test_id/info/idDoc"
method = "POST"
body = b''

data_to_sign = (
    str(server_time).encode('utf-8') +
    method.upper().encode('utf-8') +
    path.encode('utf-8') +
    body
)

print(f"   Method: {method}")
print(f"   Path: {path}")
print(f"   Body (empty for multipart): {len(body)} bytes")
print(f"   Timestamp: {server_time}")

print(f"\n   Data to sign (hex): {data_to_sign.hex()[:100]}...")
print(f"   Data to sign length: {len(data_to_sign)} bytes")

# Try encoding the secret key different ways
print("\n4. SECRET KEY ENCODING TEST:")

# Method 1: Direct encoding
sig1 = hmac.new(
    SUMSUB_SECRET_KEY.encode('utf-8'),
    data_to_sign,
    digestmod=hashlib.sha256
).hexdigest()
print(f"   Method 1 (UTF-8): {sig1[:20]}...")

# Method 2: Try if secret key is already bytes
try:
    sig2 = hmac.new(
        SUMSUB_SECRET_KEY.encode('utf-8'),
        data_to_sign,
        digestmod=hashlib.sha256
    ).hexdigest()
    print(f"   Method 2 (Direct): {sig2[:20]}...")
except Exception as e:
    print(f"   Method 2 (Direct): ERROR - {e}")

print(f"\n   Generated Signature (first 40 chars): {sig1[:40]}")
print(f"   Full Signature: {sig1}")

# 5. Print full request headers
print("\n5. REQUEST HEADERS THAT WILL BE SENT:")
headers = {
    'X-App-Token': SUMSUB_APP_TOKEN,
    'X-App-Access-Ts': str(server_time),
    'X-App-Access-Sig': sig1,
    'Accept': 'application/json',
    'X-Return-Doc-Warnings': 'true',
}

for key, value in headers.items():
    if 'Sig' in key:
        print(f"   {key}: {value[:20]}...")
    elif 'Token' in key:
        print(f"   {key}: {value[:20]}...")
    else:
        print(f"   {key}: {value}")

print("\n" + "=" * 60)
print("ACTION ITEMS TO FIX 401 SIGNATURE MISMATCH:")
print("=" * 60)
print("""
1. VERIFY .env FILE:
   - Check SUMSUB_SECRET_KEY in .env (should be base64 or plain)
   - Check SUMSUB_APP_TOKEN in .env
   - Restart the server after any .env changes

2. CHECK SERVER CLOCK:
   - Ensure system time is synchronized (within 5 seconds of SumSub servers)
   - Run: w32tm /resync (Windows) or ntpdate -s time.nist.gov (Linux)

3. VERIFY SECRET KEY FORMAT:
   - SumSub secret key might need to be decoded if it's base64
   - Check SumSub dashboard for exact key format

4. TEST WITH CURL:
   - Use the signature from this debug output to test with curl
   - Compare with SumSub API response

5. CHECK REQUEST BODY:
   - For multipart uploads, signature MUST use empty body
   - Ensure 'files' and 'data' parameters are set correctly
""")
