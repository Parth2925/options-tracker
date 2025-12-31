# Fix Production Schema Issue

## Problem

Production error: `column trades.close_price does not exist`

This means the production database doesn't have the v1.4.0 columns.

## Root Cause

Even though we:
1. ✅ Created a new database
2. ✅ Initialized it with the schema
3. ✅ Migrated data

The production database that Render is connecting to **doesn't have the v1.4.0 columns**.

## Possible Reasons

1. **Render is using the wrong database URL** - Still pointing to old database
2. **New database wasn't initialized properly** - Schema migrations didn't run
3. **Database URL format issue** - Internal vs external URL

## Solution

We need to run the schema migrations on the production database that Render is actually using.

### Step 1: Verify Which Database Render is Using

Check Render dashboard → Environment tab → `DATABASE_URL` value.

It should be:
```
postgresql://options_tracker_new_db_user:J7qsnDUWd1Y7yKgOLjFX2qnnimMU60vp@dpg-d5aleduuk2gs73er5c40-a.ohio-postgres.render.com/options_tracker_new_db?sslmode=require
```

**Important**: Use the **external URL** (with `.ohio-postgres.render.com`), not the internal URL.

### Step 2: Run Schema Migrations on Production Database

Since the columns are missing, we need to run the migration scripts on the production database:

```bash
cd backend

# Set the production database URL (use external URL from Render)
export DATABASE_URL="postgresql://options_tracker_new_db_user:J7qsnDUWd1Y7yKgOLjFX2qnnimMU60vp@dpg-d5aleduuk2gs73er5c40-a.ohio-postgres.render.com/options_tracker_new_db?sslmode=require"

# Run migrations in order
python3 migrate_add_stock_positions.py
python3 migrate_add_close_fields.py
python3 migrate_add_default_fee.py
```

### Step 3: Verify Schema

After migrations, verify:

```bash
python3 << 'EOF'
from sqlalchemy import create_engine, inspect
import os

db_url = os.getenv('DATABASE_URL')
engine = create_engine(db_url, pool_pre_ping=True, connect_args={'connect_timeout': 15})
inspector = inspect(engine)

# Check trades columns
trade_cols = [c['name'] for c in inspector.get_columns('trades')]
required = ['close_price', 'close_fees', 'close_premium', 'close_method', 'stock_position_id', 'shares_used']
missing = [col for col in required if col not in trade_cols]

if missing:
    print(f"❌ Still missing: {missing}")
else:
    print("✅ All v1.4.0 columns present")
EOF
```

### Step 4: Redeploy/Restart Render Service

After migrations complete:
- Render should automatically reconnect
- Or manually restart the service in Render dashboard

## Alternative: Use Initialize Script

If migrations fail, you can use the initialize script (but this will create empty tables - only use if database is empty):

```bash
python3 initialize_new_database.py --database-url "YOUR_PRODUCTION_DATABASE_URL"
```

**WARNING**: Only use this if the database is empty. If you have data, use the migration scripts instead.

