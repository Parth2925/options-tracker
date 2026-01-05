# Quick Fix: Add Missing Columns to Production Database

## Option 1: Wait for Automatic Migration (Recommended)

The code we just deployed includes automatic migration in `backend/app.py`. When Render deploys the new code, the `initialize_database()` function will automatically add all missing columns.

**Just wait for deployment to complete** - the migration will run automatically.

## Option 2: Run Migration Script Manually (If Needed)

If you want to fix it immediately before deployment completes, run:

```bash
cd /Users/parthsoni/Documents/options-tracker
python3 scripts/fix_prod_missing_columns.py
```

This script will:
- Connect to production database (uses DATABASE_URL from environment)
- Check for missing columns
- Add: `close_price`, `close_fees`, `close_premium`, `close_method`, `assignment_fee`, `stock_position_id`, `shares_used` to trades table
- Add: `assignment_fee` to accounts table

## Missing Columns Detected

From the production database check:
- **Trades table**: Missing `close_price`, `close_fees`, `close_premium`, `close_method`
- **Accounts table**: Already has all required columns

The automatic migration in `app.py` will add all of these when the app starts.

