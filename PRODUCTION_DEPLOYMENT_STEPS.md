# Production Deployment Steps - v1.4.0

## Overview

This guide walks through deploying v1.4.0 to production and switching to the new database.

## Prerequisites

- ✅ New database initialized with v1.4.0 schema
- ✅ Data migrated from old database to new database
- ✅ Code tested locally with new database
- ✅ Version numbers updated to 1.4.0

## Deployment Steps

### Step 1: Verify Code is Ready

**Check current branch and version:**
```bash
cd /Users/parthsoni/Documents/options-tracker
git branch --show-current  # Should be 'main' or 'feature/functional-improvements'
cat backend/version.py     # Should show VERSION = "1.4.0"
cat frontend/src/utils/version.js  # Should show VERSION = "1.4.0"
```

**If on feature branch, merge to main:**
```bash
git checkout main
git merge feature/functional-improvements
git push origin main
```

### Step 2: Update Production Database URL (Render)

**Option A: Via Render Dashboard (Recommended)**
1. Go to https://dashboard.render.com
2. Navigate to your backend service
3. Go to **Environment** tab
4. Find `DATABASE_URL` environment variable
5. Update it to:
   ```
   postgresql://options_tracker_new_db_user:J7qsnDUWd1Y7yKgOLjFX2qnnimMU60vp@dpg-d5aleduuk2gs73er5c40-a.ohio-postgres.render.com/options_tracker_new_db?sslmode=require
   ```
6. Click **Save Changes**
7. Render will automatically redeploy the service

**Option B: Via Render CLI**
```bash
# Install Render CLI if not already installed
# npm install -g render-cli

# Update environment variable
render env:set DATABASE_URL="postgresql://options_tracker_new_db_user:J7qsnDUWd1Y7yKgOLjFX2qnnimMU60vp@dpg-d5aleduuk2gs73er5c40-a.ohio-postgres.render.com/options_tracker_new_db?sslmode=require" --service <your-service-name>
```

### Step 3: Verify Backend Deployment

**Check Render deployment logs:**
1. Go to Render dashboard → Your backend service
2. Check **Logs** tab for deployment progress
3. Look for:
   - ✅ Build successful
   - ✅ Service started
   - ✅ No database connection errors

**Test backend health:**
```bash
# Replace with your actual backend URL
curl https://your-backend-url.onrender.com/api/version
# Should return: {"version": "1.4.0"}
```

### Step 4: Verify Frontend Deployment

**Frontend should auto-deploy if connected to GitHub:**
1. Check Vercel dashboard (or your frontend hosting)
2. Verify latest commit is deployed
3. Check deployment logs for any errors

**Test frontend:**
1. Visit your production URL
2. Check browser console for errors
3. Verify version shows 1.4.0 (check About page after login)

### Step 5: Verify Database Connection

**Test database access:**
```bash
# Test from local machine (using new database URL)
python3 << 'EOF'
from sqlalchemy import create_engine, text

new_url = "postgresql://options_tracker_new_db_user:J7qsnDUWd1Y7yKgOLjFX2qnnimMU60vp@dpg-d5aleduuk2gs73er5c40-a.ohio-postgres.render.com/options_tracker_new_db?sslmode=require"
engine = create_engine(new_url, pool_pre_ping=True, connect_args={'connect_timeout': 15})

with engine.connect() as conn:
    # Check user count
    user_count = conn.execute(text("SELECT COUNT(*) FROM users")).scalar()
    print(f"✅ Database accessible: {user_count} users")
    
    # Check trades count
    trade_count = conn.execute(text("SELECT COUNT(*) FROM trades")).scalar()
    print(f"✅ Trades: {trade_count} rows")
    
    # Check v1.4.0 columns exist
    from sqlalchemy import inspect
    inspector = inspect(engine)
    trade_cols = [c['name'] for c in inspector.get_columns('trades')]
    required_cols = ['close_price', 'close_fees', 'close_premium', 'close_method', 'stock_position_id', 'shares_used']
    missing = [col for col in required_cols if col not in trade_cols]
    if missing:
        print(f"❌ Missing columns: {missing}")
    else:
        print(f"✅ All v1.4.0 columns present")
EOF
```

### Step 6: Test Production App

**Critical tests to perform:**

1. **Login**
   - ✅ Login with existing production users
   - ✅ Verify credentials work

2. **Data Verification**
   - ✅ All accounts visible
   - ✅ All trades visible
   - ✅ Dashboard shows correct P&L
   - ✅ Positions page shows all positions

3. **New Features**
   - ✅ "Close" button works on open trades
   - ✅ Stock Positions page accessible
   - ✅ Default fees can be set on accounts
   - ✅ About page shows version 1.4.0

4. **Backward Compatibility**
   - ✅ Old-format trades (2-entry) display correctly
   - ✅ P&L calculations match expected values
   - ✅ Dashboard filters work correctly

### Step 7: Monitor for Issues

**Watch for:**
- Error logs in Render dashboard
- User reports of issues
- Database connection errors
- Performance issues

**If issues occur:**
- Check Render logs for backend errors
- Check browser console for frontend errors
- Verify DATABASE_URL is correct
- Test database connection directly

### Step 8: Keep Old Database as Backup

**Important:** Keep the old database for at least 1-2 weeks as backup:
- Old database URL: `postgresql://options_tracker_user:KLvsWK9feDVuydyrPA7RftVNeyYeUXEE@dpg-d53g04tactks73edsctg-a.ohio-postgres.render.com/options_tracker_peqw`
- Don't delete it immediately
- Can be used for rollback if needed

## Rollback Plan

If critical issues are found:

1. **Revert DATABASE_URL** in Render to old database
2. **Redeploy backend** (Render will auto-redeploy)
3. **Verify** old database connection works
4. **Investigate** issues with new database
5. **Fix** and retry deployment

## Verification Checklist

- [ ] Code merged to main branch
- [ ] Version numbers are 1.4.0
- [ ] DATABASE_URL updated in Render
- [ ] Backend deployed successfully
- [ ] Frontend deployed successfully
- [ ] Database connection verified
- [ ] Login works with existing users
- [ ] All data visible (accounts, trades)
- [ ] Dashboard P&L matches expected
- [ ] New features work (Close button, Stock Positions)
- [ ] About page shows version 1.4.0
- [ ] No errors in logs
- [ ] Old database kept as backup

## Post-Deployment

After successful deployment:

1. **Monitor** for 24-48 hours
2. **Collect** user feedback
3. **Document** any issues
4. **Plan** next version (1.4.1, 1.5.0, etc.)

## Support

If you encounter issues:
- Check Render logs
- Check Vercel logs (if using Vercel)
- Verify environment variables
- Test database connection directly
- Review migration logs

