# Assignment Fee Feature - Migration Plan

## Problem Analysis

### What Went Wrong Last Time

1. **Migration Script Ran Locally**: The migration script was run locally using a local `DATABASE_URL` environment variable
2. **Different Database**: The local `DATABASE_URL` was pointing to a different database than production
3. **False Positive**: The script reported "columns already exist" because it was checking the wrong database
4. **Production Failure**: When code deployed to Render, it tried to query `assignment_fee` columns that didn't exist in the production database
5. **No Shell Access**: Render free tier doesn't provide shell access to run migrations manually

### Root Cause

The migration script (`migrate_add_assignment_fee.py`) requires manual execution, but:
- Local execution used wrong database
- No way to run on Render (free tier limitation)
- Migration didn't run automatically on deployment

## Solution: Automatic Migration on App Startup

### Implementation

The migration is now integrated into the existing `initialize_database()` function in `backend/app.py`, which:
- ✅ Runs automatically on every app startup
- ✅ Uses the correct database (Render's `DATABASE_URL` environment variable)
- ✅ Is idempotent (safe to run multiple times)
- ✅ Checks if columns exist before adding them
- ✅ Works with both PostgreSQL (production) and SQLite (local)

### Migration Code Location

The migration code is in `backend/app.py`, in the `initialize_database()` function:

```python
# Check if accounts table exists and add assignment_fee if needed
if 'accounts' in inspector.get_table_names():
    accounts_columns = [col['name'] for col in inspector.get_columns('accounts')]
    
    with db.engine.connect() as conn:
        if 'assignment_fee' not in accounts_columns:
            print("Adding assignment_fee column to accounts table...")
            conn.execute(text("ALTER TABLE accounts ADD COLUMN assignment_fee NUMERIC(10, 2) DEFAULT 0"))
            conn.commit()
            print("✓ Added assignment_fee column to accounts table")

# In trades table migration section:
if 'assignment_fee' not in columns:
    print("Adding assignment_fee column to trades table...")
    conn.execute(text("ALTER TABLE trades ADD COLUMN assignment_fee NUMERIC(10, 2) DEFAULT 0"))
    conn.commit()
    print("✓ Added assignment_fee column to trades table")
```

### How It Works

1. **On App Startup**: `initialize_database()` is called automatically (line 313 in app.py)
2. **Checks Tables**: Verifies `accounts` and `trades` tables exist
3. **Checks Columns**: Inspects existing columns in each table
4. **Adds Missing Columns**: Only adds `assignment_fee` if it doesn't exist
5. **Idempotent**: Safe to run multiple times - won't duplicate columns

### Deployment Flow

1. Code is pushed to `main` branch
2. Render detects changes and starts deployment
3. Build completes, app starts
4. `initialize_database()` runs automatically
5. Migration checks for `assignment_fee` columns
6. If missing, adds them with `DEFAULT 0`
7. App continues normal startup
8. ✅ Production database now has required columns

### Verification

After deployment, check Render logs for:
```
Adding assignment_fee column to accounts table...
✓ Added assignment_fee column to accounts table
Adding assignment_fee column to trades table...
✓ Added assignment_fee column to trades table
```

Or verify via API:
- App should start without errors
- `/api/accounts` endpoint should work
- No more "no such column: accounts.assignment_fee" errors

## Rollout Plan

### Step 1: Test Locally
- [x] Verify migration code is correct
- [x] Test on local SQLite database
- [ ] Test on local PostgreSQL (if available)

### Step 2: Deploy to Production
- [ ] Merge `assignment-fee-feature` branch to `main`
- [ ] Monitor Render deployment logs
- [ ] Verify migration runs successfully
- [ ] Check that app starts without errors

### Step 3: Verify Functionality
- [ ] Test creating account with assignment_fee
- [ ] Test closing CSP as "Assigned" with assignment fee
- [ ] Test closing Covered Call as "Called Away" with assignment fee
- [ ] Verify P&L calculations include assignment fees

### Step 4: Monitor
- [ ] Check error logs for any database issues
- [ ] Verify no performance impact
- [ ] Confirm all features work as expected

## Benefits of This Approach

1. **Automatic**: No manual intervention needed
2. **Safe**: Idempotent - won't break if run multiple times
3. **Correct Database**: Always uses the database the app is connected to
4. **Works on Free Tier**: No shell access required
5. **Consistent**: Uses same pattern as other migrations in the codebase

## Rollback Plan

If issues occur:
1. Revert to previous commit (before assignment fee feature)
2. Database columns can remain (they're harmless with DEFAULT 0)
3. Or manually remove columns if needed:
   ```sql
   ALTER TABLE accounts DROP COLUMN assignment_fee;
   ALTER TABLE trades DROP COLUMN assignment_fee;
   ```

