# Run Data Migration - Step by Step

## Pre-Migration Checklist

- [x] New database created and initialized with v1.4.0 schema
- [x] Migration script created and tested
- [x] Column filtering logic verified
- [ ] Ready to migrate production data

## Migration Safety Features

✅ **Column Filtering**: Only migrates columns that exist in both databases
✅ **Skips v1.4.0 Columns**: New columns (close_price, default_fee, etc.) will be NULL (correct for old data)
✅ **Transaction Safety**: Each table migration is in a transaction
✅ **Verification**: Counts rows before and after migration
✅ **Backward Compatible**: Old format trades work with v1.4.0 code

## How It Works

### For Accounts Table
- Migrates: `id`, `user_id`, `name`, `account_type`, `initial_balance`, `created_at`
- Skips: `default_fee` (will be NULL, defaults to 0 - safe)

### For Trades Table
- Migrates: All standard columns (`id`, `account_id`, `symbol`, `trade_date`, `trade_action`, `trade_type`, `premium`, `fees`, `status`, `parent_trade_id`, etc.)
- Skips: v1.4.0 columns:
  - `close_price` → NULL (for open trades, correct)
  - `close_fees` → NULL (for open trades, correct)
  - `close_premium` → NULL (for open trades, correct)
  - `close_method` → NULL (for open trades, correct)
  - `stock_position_id` → NULL (old trades don't reference stock positions)
  - `shares_used` → NULL (old trades don't use shares)

### Result
- ✅ All old-format trades preserved exactly as-is
- ✅ `parent_trade_id` relationships maintained
- ✅ v1.4.0 code handles both formats (backward compatible)
- ✅ P&L calculations work for both formats

## Run Migration

### Step 1: Set Environment Variables

```bash
cd backend

export OLD_DATABASE_URL="postgresql://options_tracker_user:KLvsWK9feDVuydyrPA7RftVNeyYeUXEE@dpg-d53g04tactks73edsctg-a.ohio-postgres.render.com/options_tracker_peqw"
export NEW_DATABASE_URL="postgresql://options_tracker_new_db_user:J7qsnDUWd1Y7yKgOLjFX2qnnimMU60vp@dpg-d5aleduuk2gs73er5c40-a.ohio-postgres.render.com/options_tracker_new_db"
```

### Step 2: Run Migration Script

```bash
python3 migrate_data_to_new_db.py
```

The script will:
1. Connect to both databases
2. Verify schemas
3. Migrate data in order (users → accounts → trades → deposits → withdrawals)
4. Verify row counts match
5. Report any issues

### Step 3: Verify Migration

After migration completes, verify:

```bash
# Check row counts
python3 << 'EOF'
from sqlalchemy import create_engine, text

old_url = "postgresql://options_tracker_user:KLvsWK9feDVuydyrPA7RftVNeyYeUXEE@dpg-d53g04tactks73edsctg-a.ohio-postgres.render.com/options_tracker_peqw?sslmode=require"
new_url = "postgresql://options_tracker_new_db_user:J7qsnDUWd1Y7yKgOLjFX2qnnimMU60vp@dpg-d5aleduuk2gs73er5c40-a.ohio-postgres.render.com/options_tracker_new_db?sslmode=require"

old_engine = create_engine(old_url)
new_engine = create_engine(new_url)

tables = ['users', 'accounts', 'trades', 'deposits', 'withdrawals']

print("=== Verification ===")
for table in tables:
    with old_engine.connect() as conn:
        old_count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
    with new_engine.connect() as conn:
        new_count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
    
    status = "✅" if old_count == new_count else "❌"
    print(f"{status} {table}: Old={old_count}, New={new_count}")
EOF
```

## Expected Output

```
[2025-12-31 XX:XX:XX] [INFO] ================================================================================
[2025-12-31 XX:XX:XX] [INFO] Data Migration: Old Database → New Database
[2025-12-31 XX:XX:XX] [INFO] ================================================================================
[2025-12-31 XX:XX:XX] [INFO] Connecting to Old Database...
[2025-12-31 XX:XX:XX] [INFO] ✅ Old Database connection successful
[2025-12-31 XX:XX:XX] [INFO] Connecting to New Database...
[2025-12-31 XX:XX:XX] [INFO] ✅ New Database connection successful

[2025-12-31 XX:XX:XX] [INFO] Verifying database schemas...
[2025-12-31 XX:XX:XX] [INFO] Old DB tables: users, accounts, trades, deposits, withdrawals
[2025-12-31 XX:XX:XX] [INFO] New DB tables: users, accounts, trades, deposits, withdrawals, stock_positions
[2025-12-31 XX:XX:XX] [INFO] ✅ All required tables exist

[2025-12-31 XX:XX:XX] [INFO] ================================================================================
[2025-12-31 XX:XX:XX] [INFO] Starting Data Migration
[2025-12-31 XX:XX:XX] [INFO] ================================================================================

[2025-12-31 XX:XX:XX] [INFO] Migrating users...
[2025-12-31 XX:XX:XX] [INFO]    Old DB: X rows
[2025-12-31 XX:XX:XX] [INFO]    New DB: 0 rows (before migration)
[2025-12-31 XX:XX:XX] [INFO]    Migrating columns: id, email, first_name, ...
[2025-12-31 XX:XX:XX] [INFO]    Read X rows from old database
[2025-12-31 XX:XX:XX] [INFO]    ✅ Migrated X rows in X.XX seconds
[2025-12-31 XX:XX:XX] [INFO]    ✅ Verification passed: X rows

... (similar for accounts, trades, deposits, withdrawals)

[2025-12-31 XX:XX:XX] [INFO] ================================================================================
[2025-12-31 XX:XX:XX] [INFO] Final Verification
[2025-12-31 XX:XX:XX] [INFO] ================================================================================
[2025-12-31 XX:XX:XX] [INFO] ✅ users: X rows (match)
[2025-12-31 XX:XX:XX] [INFO] ✅ accounts: X rows (match)
[2025-12-31 XX:XX:XX] [INFO] ✅ trades: X rows (match)
[2025-12-31 XX:XX:XX] [INFO] ✅ deposits: X rows (match)
[2025-12-31 XX:XX:XX] [INFO] ✅ withdrawals: X rows (match)

[2025-12-31 XX:XX:XX] [INFO] ✅ All data migrated successfully!
[2025-12-31 XX:XX:XX] [INFO] Total rows migrated: XXXX
```

## Post-Migration Testing

After migration, test locally:

1. **Point local .env to new database** (already done)
2. **Start backend and frontend**
3. **Test with migrated data**:
   - Login with existing users
   - View accounts (default_fee should be 0)
   - View trades (all old trades should appear)
   - Check dashboard (P&L should match)
   - Test new features (should work)

## Rollback Plan

If issues are found:
- ✅ Old database is untouched (still has all data)
- ✅ Can switch back by changing DATABASE_URL
- ✅ No data loss
- ✅ Can fix issues and retry migration

## Next Steps After Successful Migration

1. ✅ Verify all data migrated correctly
2. ✅ Test locally with migrated data
3. ⏳ Switch production to new database
4. ⏳ Keep old database as backup for 1-2 weeks

