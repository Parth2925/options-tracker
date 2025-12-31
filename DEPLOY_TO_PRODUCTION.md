# Deploy v1.4.0 to Production - Step by Step Guide

## Current Status

✅ **Data Migration**: Complete (91 rows migrated to new database)  
✅ **Version**: 1.4.0 (backend and frontend)  
✅ **Local Testing**: Verified with existing user data  
⏳ **Production Deployment**: Ready to proceed  

## Deployment Steps

### Step 1: Merge Feature Branch to Main (if needed)

**Check current branch:**
```bash
cd /Users/parthsoni/Documents/options-tracker
git branch --show-current
```

**If on `feature/functional-improvements`:**
```bash
# Switch to main
git checkout main

# Merge feature branch
git merge feature/functional-improvements

# Push to remote
git push origin main
```

**Verify version:**
```bash
cat backend/version.py          # Should show: VERSION = "1.4.0"
cat frontend/src/utils/version.js  # Should show: VERSION = "1.4.0"
```

### Step 2: Update Production Database URL (Render)

**This is the critical step - updating Render to use the new database:**

1. **Go to Render Dashboard**
   - Visit: https://dashboard.render.com
   - Navigate to your backend service (the Flask/Python service)

2. **Update Environment Variable**
   - Click on your backend service
   - Go to **Environment** tab (in the left sidebar)
   - Find `DATABASE_URL` in the environment variables list
   - Click **Edit** or the pencil icon
   - **Replace** the old database URL with:
     ```
     postgresql://options_tracker_new_db_user:J7qsnDUWd1Y7yKgOLjFX2qnnimMU60vp@dpg-d5aleduuk2gs73er5c40-a.ohio-postgres.render.com/options_tracker_new_db?sslmode=require
     ```
   - Click **Save Changes**

3. **Render Will Auto-Redeploy**
   - Render automatically detects environment variable changes
   - It will trigger a new deployment
   - Monitor the **Logs** tab to watch deployment progress

**Expected deployment time:** 2-5 minutes

### Step 3: Verify Backend Deployment

**Check Render Logs:**
1. Go to your backend service → **Logs** tab
2. Look for:
   - ✅ "Build successful"
   - ✅ "Starting service"
   - ✅ No database connection errors
   - ✅ Service is running

**Test Backend API:**
```bash
# Replace YOUR_BACKEND_URL with your actual Render URL
curl https://YOUR_BACKEND_URL.onrender.com/api/version

# Expected response:
# {"version": "1.4.0"}
```

**If you see errors:**
- Check the logs for specific error messages
- Verify DATABASE_URL is correct (no typos)
- Ensure new database is accessible

### Step 4: Verify Frontend Deployment

**Frontend should auto-deploy** (if connected to GitHub/Vercel):

1. **Check Vercel Dashboard** (or your frontend hosting)
   - Visit: https://vercel.com/dashboard (or your hosting platform)
   - Find your frontend project
   - Check latest deployment status
   - Should show latest commit from `main` branch

2. **Test Frontend:**
   - Visit your production URL
   - Open browser console (F12)
   - Check for any errors
   - Login and verify:
     - ✅ All accounts visible
     - ✅ All trades visible
     - ✅ Dashboard shows correct data
     - ✅ About page shows version 1.4.0

### Step 5: Verify Database Connection

**Test from production backend:**
```bash
# Test database connection (replace with your backend URL)
curl https://YOUR_BACKEND_URL.onrender.com/api/accounts \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Should return accounts from new database
```

**Or test directly:**
```bash
python3 << 'EOF'
from sqlalchemy import create_engine, text

# New database URL
new_url = "postgresql://options_tracker_new_db_user:J7qsnDUWd1Y7yKgOLjFX2qnnimMU60vp@dpg-d5aleduuk2gs73er5c40-a.ohio-postgres.render.com/options_tracker_new_db?sslmode=require"
engine = create_engine(new_url, pool_pre_ping=True, connect_args={'connect_timeout': 15})

with engine.connect() as conn:
    user_count = conn.execute(text("SELECT COUNT(*) FROM users")).scalar()
    trade_count = conn.execute(text("SELECT COUNT(*) FROM trades")).scalar()
    print(f"✅ Database accessible: {user_count} users, {trade_count} trades")
EOF
```

### Step 6: Production Testing Checklist

**Critical tests to perform after deployment:**

- [ ] **Login**
  - [ ] Login with existing production user credentials
  - [ ] Verify login works correctly

- [ ] **Data Verification**
  - [ ] All accounts are visible
  - [ ] All trades are visible (82 trades should be there)
  - [ ] Dashboard shows correct P&L values
  - [ ] Positions page shows all positions

- [ ] **New Features (v1.4.0)**
  - [ ] "Close" button appears on open trades
  - [ ] Stock Positions page is accessible (from Positions tab)
  - [ ] Default fees can be set on accounts
  - [ ] About page shows version 1.4.0
  - [ ] "How to Use" guide is accessible

- [ ] **Backward Compatibility**
  - [ ] Old-format trades (2-entry) display correctly
  - [ ] P&L calculations match expected values
  - [ ] Dashboard filters work correctly
  - [ ] No data loss or corruption

- [ ] **Error Checking**
  - [ ] No errors in browser console
  - [ ] No errors in Render logs
  - [ ] No database connection errors

### Step 7: Monitor for Issues

**Watch for 24-48 hours after deployment:**

1. **Render Logs**
   - Monitor backend logs for errors
   - Check for database connection issues
   - Watch for any exceptions

2. **User Reports**
   - Monitor for user-reported issues
   - Check if login problems occur
   - Verify data integrity

3. **Performance**
   - Check response times
   - Monitor database query performance
   - Watch for timeouts

### Step 8: Keep Old Database as Backup

**Important:** Don't delete the old database yet!

- **Old Database URL:** `postgresql://options_tracker_user:KLvsWK9feDVuydyrPA7RftVNeyYeUXEE@dpg-d53g04tactks73edsctg-a.ohio-postgres.render.com/options_tracker_peqw`
- **Keep for:** At least 1-2 weeks
- **Purpose:** Rollback option if critical issues found

## Rollback Plan (If Needed)

If critical issues are discovered:

1. **Revert DATABASE_URL in Render**
   - Go to Render dashboard → Environment tab
   - Change `DATABASE_URL` back to old database URL
   - Save changes (will trigger redeploy)

2. **Verify Rollback**
   - Check Render logs for successful deployment
   - Test login and data access
   - Confirm old database is being used

3. **Investigate Issues**
   - Review error logs
   - Test database connection
   - Fix issues before retrying

## Quick Reference

### Database URLs

**New Database (v1.4.0):**
```
postgresql://options_tracker_new_db_user:J7qsnDUWd1Y7yKgOLjFX2qnnimMU60vp@dpg-d5aleduuk2gs73er5c40-a.ohio-postgres.render.com/options_tracker_new_db?sslmode=require
```

**Old Database (v1.3.0 - Backup):**
```
postgresql://options_tracker_user:KLvsWK9feDVuydyrPA7RftVNeyYeUXEE@dpg-d53g04tactks73edsctg-a.ohio-postgres.render.com/options_tracker_peqw?sslmode=require
```

### Version Verification

**Backend:**
```bash
curl https://YOUR_BACKEND_URL.onrender.com/api/version
# Should return: {"version": "1.4.0"}
```

**Frontend:**
- Login to production app
- Go to About page (footer link)
- Should show version 1.4.0

## Troubleshooting

### Issue: Backend won't start
- **Check:** Render logs for specific errors
- **Verify:** DATABASE_URL is correct (no typos)
- **Test:** Database connection directly

### Issue: Database connection errors
- **Check:** Database URL format (should include `?sslmode=require`)
- **Verify:** Database credentials are correct
- **Test:** Connection from local machine

### Issue: Data not showing
- **Check:** Is backend using new database? (check logs)
- **Verify:** Data exists in new database
- **Test:** Direct database query

### Issue: Frontend errors
- **Check:** Browser console for errors
- **Verify:** Frontend is deployed from latest commit
- **Check:** API endpoints are accessible

## Success Criteria

✅ Backend deployed and running  
✅ Frontend deployed and accessible  
✅ DATABASE_URL points to new database  
✅ Users can login  
✅ All data visible (accounts, trades)  
✅ Dashboard shows correct P&L  
✅ New features work (Close button, Stock Positions)  
✅ Version shows 1.4.0  
✅ No errors in logs  

## Next Steps After Deployment

1. **Monitor** for 24-48 hours
2. **Collect** user feedback
3. **Document** any issues
4. **Plan** next version improvements
5. **Consider** deleting old database after 2 weeks (if all is well)

---

**Ready to deploy?** Follow steps 1-6 above, then test thoroughly!

