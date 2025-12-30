# Migration Notes - Version 1.4.0

This document outlines all database migrations required when deploying version 1.4.0 to production.

## Overview

Version 1.4.0 introduces major new features:
- Stock Positions tracking
- Enhanced close workflow (single-entry system)
- Default fees for accounts
- Close fields for trades (close_price, close_fees, close_premium, close_method)

## Migration Order (CRITICAL - MUST RUN IN THIS ORDER)

The migrations must be run in the exact order listed below:

### 1. Stock Positions Migration
**Script:** `backend/migrate_add_stock_positions.py`

**What It Does:**
- Creates the `stock_positions` table
- Adds `stock_position_id` column to `trades` table (for linking covered calls to stock positions)
- Adds `shares_used` column to `trades` table (for tracking shares used by covered calls)

**Usage:**
```bash
cd backend
python3 migrate_add_stock_positions.py [--database-url DATABASE_URL]
```

Or set the DATABASE_URL environment variable:
```bash
export DATABASE_URL="postgresql://user:pass@host/dbname"
python3 migrate_add_stock_positions.py
```

### 2. Close Fields Migration
**Script:** `backend/migrate_add_close_fields.py`

**What It Does:**
- Adds `close_price` column (Numeric(10, 2)) to `trades` table
- Adds `close_fees` column (Numeric(10, 2)) to `trades` table
- Adds `close_premium` column (Numeric(10, 2)) to `trades` table
- Adds `close_method` column (VARCHAR(30)) to `trades` table

These fields enable the single-entry close system where full closes update the original trade entry.

**Usage:**
```bash
cd backend
python3 migrate_add_close_fields.py [--database-url DATABASE_URL]
```

### 3. Default Fee Migration
**Script:** `backend/migrate_add_default_fee.py`

**What It Does:**
- Adds `default_fee` column (Numeric(10, 2), default=0) to `accounts` table
- Allows users to set a default fee per contract for each account

**Usage:**
```bash
cd backend
python3 migrate_add_default_fee.py [--database-url DATABASE_URL]
```

### 4. Data Migration (Optional but Recommended)
**Script:** `backend/migrate_existing_data.py`

**What It Does:**
- Creates stock positions from existing Assignment trades
- Links existing Covered Call trades to stock positions (or creates positions if needed)
- Handles partial assignments and multiple covered calls

**Note:** This migration is optional but recommended if you have existing Assignment or Covered Call trades. It will help maintain data consistency.

**Usage:**
```bash
cd backend
python3 migrate_existing_data.py [--database-url DATABASE_URL] [--dry-run]
```

Use `--dry-run` to see what changes would be made without actually applying them.

## Production Migration Steps

### Step 1: Backup Database
**IMPORTANT:** Always backup your production database before running migrations.

```bash
# For PostgreSQL (Render)
pg_dump "postgresql://user:pass@host/dbname" > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Step 2: Set Database URL
```bash
export DATABASE_URL="postgresql://options_tracker_user:KLvsWK9feDVuydyrPA7RftVNeyYeUXEE@dpg-d53g04tactks73edsctg-a.ohio-postgres.render.com/options_tracker_peqw"
```

### Step 3: Run Migrations in Order
```bash
cd backend

# Migration 1: Stock Positions
python3 migrate_add_stock_positions.py

# Migration 2: Close Fields
python3 migrate_add_close_fields.py

# Migration 3: Default Fee
python3 migrate_add_default_fee.py

# Migration 4: Data Migration (Optional)
python3 migrate_existing_data.py
```

### Step 4: Verify Migrations
After running all migrations, verify they worked:

```python
from sqlalchemy import create_engine, inspect

engine = create_engine('your_database_url')
inspector = inspect(engine)

# Check stock_positions table exists
print('stock_positions table exists:', 'stock_positions' in inspector.get_table_names())

# Check trades table has new columns
trades_cols = [c['name'] for c in inspector.get_columns('trades')]
print('stock_position_id exists:', 'stock_position_id' in trades_cols)
print('shares_used exists:', 'shares_used' in trades_cols)
print('close_price exists:', 'close_price' in trades_cols)
print('close_fees exists:', 'close_fees' in trades_cols)
print('close_premium exists:', 'close_premium' in trades_cols)
print('close_method exists:', 'close_method' in trades_cols)

# Check accounts table has default_fee
accounts_cols = [c['name'] for c in inspector.get_columns('accounts')]
print('default_fee exists:', 'default_fee' in accounts_cols)
```

## Backward Compatibility

**IMPORTANT:** This version is fully backward compatible with existing data.

- Existing trades using the old two-entry system (separate open and close trades) will continue to work
- New trades will use the single-entry system for full closes
- Partial closes will still create child trades (hybrid approach)
- All P&L calculations correctly handle both old and new formats
- Dashboard metrics correctly filter and calculate for both formats

See `BACKWARD_COMPATIBILITY_VERIFICATION.md` for detailed verification.

## Rollback Plan

If you need to rollback, the new columns can be left in place (they're nullable) and the application will continue to work with old-format trades. However, if you want to remove the columns:

**WARNING:** Only do this if you have NOT created any new stock positions or used the new close fields.

```sql
-- PostgreSQL
ALTER TABLE trades DROP COLUMN IF EXISTS stock_position_id;
ALTER TABLE trades DROP COLUMN IF EXISTS shares_used;
ALTER TABLE trades DROP COLUMN IF EXISTS close_price;
ALTER TABLE trades DROP COLUMN IF EXISTS close_fees;
ALTER TABLE trades DROP COLUMN IF EXISTS close_premium;
ALTER TABLE trades DROP COLUMN IF EXISTS close_method;
ALTER TABLE accounts DROP COLUMN IF EXISTS default_fee;
DROP TABLE IF EXISTS stock_positions;
```

## Troubleshooting

### Migration Fails with "Column Already Exists"
This means the migration was already run. The scripts check for existing columns and skip if they exist, so this shouldn't happen. If it does, verify the column exists and move to the next migration.

### Migration Fails with "Table Already Exists"
Similar to above - the migration was already run. Verify the table/columns exist and continue.

### Data Migration Fails
If `migrate_existing_data.py` fails, you can:
1. Check the error message
2. Fix any data inconsistencies manually
3. Re-run the migration (it's idempotent and safe to run multiple times)

## Post-Migration Checklist

- [ ] All migrations completed successfully
- [ ] Database backup created
- [ ] Verification script confirms all columns/tables exist
- [ ] Test application with existing data
- [ ] Verify P&L calculations are correct
- [ ] Test new features (stock positions, enhanced close workflow)
- [ ] Monitor for any errors in production logs
