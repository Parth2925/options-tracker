# Production Database URL Issue - Resolution Guide

## Problem

✅ New database (`options_tracker_new_db`) has all v1.4.0 columns  
❌ Production error: `column trades.close_price does not exist`  
**Conclusion**: Render is NOT connecting to the new database

## Root Cause

Render's `DATABASE_URL` is either:
1. Still pointing to the old database
2. Using the wrong URL format
3. Not being picked up after update

## Solution

### Step 1: Verify Database URL in Render

1. Go to Render dashboard → Your backend service
2. Go to **Environment** tab
3. Find `DATABASE_URL` environment variable
4. **Check the exact value**

**It should be:**
```
postgresql://options_tracker_new_db_user:J7qsnDUWd1Y7yKgOLjFX2qnnimMU60vp@dpg-d5aleduuk2gs73er5c40-a.ohio-postgres.render.com/options_tracker_new_db?sslmode=require
```

**NOT:**
```
postgresql://options_tracker_user:KLvsWK9feDVuydyrPA7RftVNeyYeUXEE@dpg-d53g04tactks73edsctg-a.ohio-postgres.render.com/options_tracker_peqw?sslmode=require
```
(This is the old database)

### Step 2: Internal vs External URL

You mentioned using the "internal URL". On Render, you can use either:

**External URL (Recommended):**
```
postgresql://options_tracker_new_db_user:J7qsnDUWd1Y7yKgOLjFX2qnnimMU60vp@dpg-d5aleduuk2gs73er5c40-a.ohio-postgres.render.com/options_tracker_new_db?sslmode=require
```

**Internal URL (Only works within Render network):**
```
postgresql://options_tracker_new_db_user:J7qsnDUWd1Y7yKgOLjFX2qnnimMU60vp@dpg-d5aleduuk2gs73er5c40-a/options_tracker_new_db
```

Both should work for Render, but make sure you're using the **new database** URL, not the old one.

### Step 3: Update DATABASE_URL (if needed)

If the URL is wrong:

1. **Edit** the `DATABASE_URL` environment variable
2. **Replace** with the new database URL (external or internal - both work)
3. **Save** changes
4. Render will auto-redeploy

### Step 4: Manual Restart (if needed)

If Render didn't auto-redeploy:

1. Go to your backend service
2. Click **Manual Deploy** → **Deploy latest commit**
3. Or restart the service

### Step 5: Verify Connection

After redeploy, check Render logs for:
- ✅ "Build successful"
- ✅ No database connection errors
- ✅ Service started successfully

Then test the API:
```bash
curl https://YOUR_BACKEND_URL.onrender.com/api/version
# Should return: {"version": "1.4.0"}
```

## Quick Check: Which Database is Render Using?

To verify which database Render is actually using, check the error message. The old database doesn't have `close_price` column, so if you see that error, Render is definitely using the old database.

## Database URLs Reference

**New Database (v1.4.0):**
- External: `postgresql://options_tracker_new_db_user:J7qsnDUWd1Y7yKgOLjFX2qnnimMU60vp@dpg-d5aleduuk2gs73er5c40-a.ohio-postgres.render.com/options_tracker_new_db?sslmode=require`
- Internal: `postgresql://options_tracker_new_db_user:J7qsnDUWd1Y7yKgOLjFX2qnnimMU60vp@dpg-d5aleduuk2gs73er5c40-a/options_tracker_new_db`

**Old Database (v1.3.0 - Backup):**
- External: `postgresql://options_tracker_user:KLvsWK9feDVuydyrPA7RftVNeyYeUXEE@dpg-d53g04tactks73edsctg-a.ohio-postgres.render.com/options_tracker_peqw?sslmode=require`
- Internal: `postgresql://options_tracker_user:KLvsWK9feDVuydyrPA7RftVNeyYeUXEE@dpg-d53g04tactks73edsctg-a/options_tracker_peqw`

## Key Differences

| Database | User | Host (first part) | Database Name |
|----------|------|-------------------|---------------|
| **New** | `options_tracker_new_db_user` | `dpg-d5aleduuk2gs73er5c40-a` | `options_tracker_new_db` |
| **Old** | `options_tracker_user` | `dpg-d53g04tactks73edsctg-a` | `options_tracker_peqw` |

Make sure Render is using the **New** database URL!

