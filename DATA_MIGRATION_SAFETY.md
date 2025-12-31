# Data Migration Safety - v1.4.0 Compatibility

## Overview

This document explains how the data migration ensures compatibility between v1.3.0 (old database) and v1.4.0 (new database) schemas.

## Schema Differences

### Old Database (v1.3.0)
- ✅ users table
- ✅ accounts table (no `default_fee` column)
- ✅ trades table (no close fields, no stock_position_id, no shares_used)
- ✅ deposits table
- ✅ withdrawals table
- ❌ stock_positions table (doesn't exist)

### New Database (v1.4.0)
- ✅ users table (same)
- ✅ accounts table (+ `default_fee` column)
- ✅ trades table (+ `close_price`, `close_fees`, `close_premium`, `close_method`, `stock_position_id`, `shares_used`)
- ✅ deposits table (same)
- ✅ withdrawals table (same)
- ✅ stock_positions table (new)

## Migration Strategy

### 1. Column Handling

**For accounts table:**
- Old DB has: `id`, `user_id`, `name`, `account_type`, `initial_balance`, `created_at`
- New DB has: All above + `default_fee`
- **Migration**: Skip `default_fee` column (will be NULL, which defaults to 0)
- **Result**: ✅ All accounts migrated, `default_fee` will be 0 (safe default)

**For trades table:**
- Old DB has: Standard trade columns (no close fields, no stock_position_id, no shares_used)
- New DB has: All above + v1.4.0 columns
- **Migration**: Skip all v1.4.0 columns:
  - `close_price` → NULL (for open trades, this is correct)
  - `close_fees` → NULL (for open trades, this is correct)
  - `close_premium` → NULL (for open trades, this is correct)
  - `close_method` → NULL (for open trades, this is correct)
  - `stock_position_id` → NULL (old trades don't reference stock positions)
  - `shares_used` → NULL (old trades don't use shares)
- **Result**: ✅ All trades migrated, new fields are NULL (correct for old-format trades)

### 2. Trade Format Compatibility

**Old Format (v1.3.0):**
- Opening trade: `trade_action = 'Sold to Open'` or `'Bought to Open'`
- Closing trade: `trade_action = 'Bought to Close'` or `'Sold to Close'`, with `parent_trade_id` pointing to opening trade
- Status: Determined by presence of closing trade

**New Format (v1.4.0):**
- Single entry: Opening trade with `close_price`, `close_fees`, `close_premium`, `close_method` filled when closed
- OR: Still supports old format (two-entry system) for backward compatibility

**Migration Result:**
- ✅ Old format trades are preserved exactly as-is
- ✅ `parent_trade_id` relationships are maintained
- ✅ v1.4.0 code handles both formats (backward compatible)
- ✅ P&L calculations work for both formats

### 3. Foreign Key Relationships

All relationships are preserved:
- ✅ users → accounts (via `user_id`)
- ✅ accounts → trades (via `account_id`)
- ✅ trades → trades (via `parent_trade_id` for old format)
- ✅ accounts → deposits (via `account_id`)
- ✅ accounts → withdrawals (via `account_id`)

### 4. Data Integrity

**Verification Steps:**
1. Row counts match between old and new databases
2. Foreign key relationships are intact
3. No data loss
4. NULL values in new columns are correct (expected for old data)

## Safety Features

### 1. Column Filtering
- Only migrates columns that exist in both databases
- Skips new v1.4.0 columns (they'll be NULL, which is correct)
- Logs which columns are skipped

### 2. Transaction Safety
- Each table migration is in a transaction
- If migration fails, transaction is rolled back
- No partial data corruption

### 3. Verification
- Counts rows before and after migration
- Verifies final counts match
- Reports any mismatches

### 4. Idempotency
- Can check if data already exists
- Warns before adding duplicate data
- Safe to run verification multiple times

## What Won't Break

### ✅ Backward Compatibility
- Old format trades (2-entry system) continue to work
- P&L calculations handle both formats
- Dashboard filters correctly exclude closing trades
- All existing functionality preserved

### ✅ New Features
- New v1.4.0 features work with migrated data
- Default fees can be set after migration
- Stock positions can be created as needed
- Close workflow works for new trades

### ✅ Data Integrity
- All relationships preserved
- No data loss
- No corruption
- All foreign keys intact

## Post-Migration Steps

After migration completes:

1. **Verify Data Counts**
   - Users: Should match
   - Accounts: Should match
   - Trades: Should match
   - Deposits/Withdrawals: Should match

2. **Test Functionality**
   - Login with existing users
   - View accounts (default_fee should be 0 or NULL)
   - View trades (should show all old trades)
   - Test dashboard (P&L should match)
   - Test new features (should work)

3. **Optional: Set Default Fees**
   - Edit accounts to set default fees
   - This is optional, not required

4. **Optional: Create Stock Positions**
   - If you have Assignment trades, you can create stock positions manually
   - Or use the migration script `migrate_existing_data.py` later

## Rollback Plan

If migration fails or issues are found:

1. **New database is separate** - Old database is untouched
2. **Can switch back** - Just change DATABASE_URL back to old database
3. **No data loss** - Old database remains intact
4. **Can retry** - Fix issues and run migration again

## Expected Behavior After Migration

### For Users
- ✅ Can log in with existing credentials
- ✅ See all their accounts
- ✅ See all their trades
- ✅ Dashboard shows correct P&L
- ✅ All existing data visible

### For New Features
- ✅ Can set default fees on accounts
- ✅ Can create stock positions
- ✅ Can use new close workflow for new trades
- ✅ Old trades continue to work as before

## Migration Script Safety

The migration script:
- ✅ Only reads from old database (never modifies it)
- ✅ Only writes to new database
- ✅ Uses transactions for safety
- ✅ Verifies data integrity
- ✅ Provides detailed logging
- ✅ Handles errors gracefully

