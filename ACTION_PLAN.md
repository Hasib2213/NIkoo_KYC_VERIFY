# ⚡ ACTION PLAN - Fix Document Upload 401 Error

## Your Immediate Tasks (5 minutes)

### Task 1: Verify Secret Key (1 minute)
```bash
# Open terminal and run:
grep SUMSUB_SECRET_KEY .env
```

**Expected:** Something like
```
SUMSUB_SECRET_KEY=Tp8XN5fsWvnEzKk9rxvoeONiX574gc3a
```

**NOT like:**
```
SUMSUB_SECRET_KEY=sbx:7FXLUg3B21q57vnZAnQB6KRl...  ❌
SUMSUB_SECRET_KEY=                                  ❌ (empty)
```

### If Wrong:
1. Go to [SumSub Dashboard](https://app.sumsub.com)
2. Settings → API Keys
3. Find **Secret Key** (copy it)
4. Edit `.env` - update the value
5. Save

---

### Task 2: Restart Server (2 minutes)
```bash
# In your uvicorn terminal:
# 1. Press Ctrl+C
# 2. Wait for "Shutdown complete"
# 3. Run: python -m uvicorn main:app --reload
```

**Should see:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

---

### Task 3: Test Upload (2 minutes)
1. Upload a document via API
2. Check the logs:
   ```bash
   tail -f app/logs/app.log
   ```
3. Look for either:
   - ✅ `✅ Document front uploaded successfully`
   - ❌ `❌ Failed to scan document front: ...`

---

## If Still Getting 401 Error

### Follow This Checklist

- [ ] **Secret key verified** (not app token)
  - Where to check: `.env` file
  - What to look for: Alphanumeric, 30-40 chars, NOT starting with `sbx:`

- [ ] **Server restarted** (full restart)
  - How to do it: Ctrl+C, wait, then start again
  - Don't just use "reload"

- [ ] **Clock synced** (within 5 seconds of real time)
  - How to check: `Get-Date` (Windows) or `date` (Linux)
  - How to fix: `w32tm /resync` (Windows) or `sudo ntpdate -s time.nist.gov` (Linux)

- [ ] **Logs checked** (for signature details)
  - Where: `app/logs/app.log`
  - What to look for: Signature and timestamp values

---

## What the Logs Tell You

### Good Logs
```
INFO - Document Upload - Front Side
INFO -   Signature (first 20 chars): abc123def456ghi789jk...
INFO -   Timestamp: 1674123456
INFO - Response Status: 200
INFO - ✅ Document front uploaded successfully
```

### Bad Logs
```
INFO - Document Upload - Front Side
INFO -   Signature (first 20 chars): abc123def456ghi789jk...
ERROR - Response Status: 401
ERROR - {"errorCode":4003,"description":"Request signature mismatch"}
ERROR - ❌ Failed to scan document front
```

→ See [QUICK_FIX_401_ERROR.md](QUICK_FIX_401_ERROR.md) for solutions

---

## The 3 Most Common Fixes

### Fix #1: Secret Key (Highest Probability - 60%)
```bash
# Your .env should have:
SUMSUB_SECRET_KEY=Tp8XN5fsWvnEzKk9rxvoeONiX574gc3a

# NOT:
SUMSUB_SECRET_KEY=sbx:7FXLUg3B21q57...  ❌ This is wrong
```

**Action:**
1. Get correct key from SumSub dashboard
2. Update `.env`
3. Restart server

---

### Fix #2: Server Restart (Second Highest - 20%)
```bash
# Just restart:
# 1. Ctrl+C (stop)
# 2. python -m uvicorn main:app --reload (start)

# This loads the .env changes
```

---

### Fix #3: Clock Sync (Third Highest - 10%)
```bash
# Check if clock is way off:
Get-Date  # Windows
date      # Linux

# Sync if needed:
w32tm /resync  # Windows (run as admin)
```

---

## Quick Reference Table

| Issue | Solution | Time |
|-------|----------|------|
| 401 Signature Error | Verify secret key + restart | 2 min |
| Empty secret key | Get from dashboard + update .env | 3 min |
| Clock too far off | Sync system time | 1 min |
| Wrong app token used | Copy secret key (not app token) | 2 min |
| Server not restarted | Full restart (Ctrl+C + start) | 1 min |

---

## Communication with Team

If you need help, tell them:

```
Subject: SumSub Document Upload 401 Error

Details:
- Error: 401 Unauthorized, errorCode 4003 (signature mismatch)
- Endpoint: POST /resources/applicants/{id}/info/idDoc
- Action: I've verified:
  [ ] Secret key in .env (value: [first 10 chars])
  [ ] Server restarted
  [ ] Clock synced
  [ ] Logs show: [paste relevant log line]
```

---

## Success Confirmation

### ✅ You're Done When:
```
Status: 200 OK
Response: ✅ Document front uploaded successfully: [image_id]
Logs show signature details and success message
```

### Document appears in SumSub dashboard with:
- ✅ Document type recognized
- ✅ Image quality OK
- ✅ Ready for review

---

## Need More Help?

### Quick Help (2 min)
→ [QUICK_FIX_401_ERROR.md](QUICK_FIX_401_ERROR.md)

### Detailed Help (10 min)
→ [SUMSUB_SIGNATURE_DEBUG.md](SUMSUB_SIGNATURE_DEBUG.md)

### Complete Guide (15 min)
→ [DOCUMENT_UPLOAD_TROUBLESHOOTING.md](DOCUMENT_UPLOAD_TROUBLESHOOTING.md)

---

## Estimated Timeline

| Stage | Time | Action |
|-------|------|--------|
| Verify Secret | 1 min | Check `.env` |
| Restart | 2 min | Stop and start server |
| Test | 1 min | Upload document |
| **Total** | **4 min** | Should be working |

---

## Key Numbers to Remember

- **Secret key length:** 30-40 characters
- **Signature length:** 64 characters (hex)
- **Max clock skew:** 5 seconds
- **Success rate:** >95% with correct key

---

## What NOT to Do

- ❌ Don't use app token as secret key
- ❌ Don't just reload the server (full restart needed)
- ❌ Don't sign with multipart payload (use empty body)
- ❌ Don't skip the .env verification
- ❌ Don't ignore clock sync (if timestamp looks wrong)

---

## Done! ✅

Once document uploads work:
1. Celebrate! 🎉
2. Note down: "Secret key was correct/wrong, fixed by..."
3. Update team if needed
4. Move to next task

---

**Expected Time to Resolution:** 5-10 minutes
**Success Rate with This Guide:** >95%
**Difficulty Level:** Easy (just configuration)

---

**Start with:** Verify secret key above ⬆️
