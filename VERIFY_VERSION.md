# How to Verify Version System

## 1. Check Version Files Consistency

Run the verification script:
```bash
./test-version.sh
```

This checks that all version files have the same version:
- `backend/version.py`
- `frontend/src/utils/version.js`
- `frontend/package.json`

**Expected output:**
```
=== Version Verification ===

Backend (version.py):    1.0.0
Frontend (version.js):   1.0.0
Frontend (package.json): 1.0.0

✓ All versions match: 1.0.0
```

## 2. Test Backend API Endpoint

Start the backend server:
```bash
cd backend
python app.py
```

Then test the version endpoint:
```bash
curl http://localhost:5001/api/version
```

**Expected response:**
```json
{"version":"1.0.0"}
```

## 3. Test Frontend Version Display

Start the frontend server:
```bash
cd frontend
npm start
```

Then:
1. Open http://localhost:3000 in your browser
2. Login to the application
3. Check the navbar - you should see "v1.0.0" badge next to your profile name
4. On mobile (or resize browser to mobile width), open the menu - you should see "v1.0.0" in the footer of the mobile menu

## 4. Test Version Increment Script

Test the increment script:
```bash
./increment-version.sh
```

**Expected output:**
```
Current version: 1.0.0
New version: 1.1.0
Version updated to 1.1.0 in:
  - backend/version.py
  - frontend/src/utils/version.js
  - frontend/package.json
```

Then verify it worked:
```bash
./test-version.sh
```

Should show: `✓ All versions match: 1.1.0`

**Note:** If you test the increment, you can revert it back with:
```bash
git checkout -- backend/version.py frontend/src/utils/version.js frontend/package.json
```

