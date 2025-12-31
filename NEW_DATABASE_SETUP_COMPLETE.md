# New Database Setup - Complete ✅

## Status: New Database Ready for v1.4.0

### What Was Done

1. ✅ **Created new Vercel Postgres instance**: `options_tracker_new_db`
2. ✅ **Initialized with v1.4.0 schema**:
   - Base tables (users, accounts, trades, deposits, withdrawals)
   - Stock Positions table
   - Close fields (close_price, close_fees, close_premium, close_method)
   - Default fee column (accounts.default_fee)
   - Stock position linking (stock_position_id, shares_used)

### Database Connection Info

**New Database (v1.4.0):**
- **External URL**: `postgresql://options_tracker_new_db_user:J7qsnDUWd1Y7yKgOLjFX2qnnimMU60vp@dpg-d5aleduuk2gs73er5c40-a.ohio-postgres.render.com/options_tracker_new_db`
- **Status**: ✅ Initialized and ready
- **Schema**: v1.4.0 complete

**Old Database (Production - v1.3.0):**
- **External URL**: `postgresql://options_tracker_user:KLvsWK9feDVuydyrPA7RftVNeyYeUXEE@dpg-d53g04tactks73edsctg-a.ohio-postgres.render.com/options_tracker_peqw`
- **Status**: Still running production
- **Schema**: v1.3.0

## Next Steps

### Option A: Test New Database First (Recommended)

1. **Point backend to new database temporarily** (for testing)
2. **Test all v1.4.0 features** on new database
3. **If everything works**, proceed with data migration
4. **If issues found**, fix them before migrating data

### Option B: Migrate Data Now

1. **Run data migration script** to copy all data from old → new
2. **Verify data integrity**
3. **Switch production to new database**
4. **Keep old database as backup**

## Data Migration Script

I've created `migrate_data_to_new_db.py` which will:
- Copy all users
- Copy all accounts
- Copy all trades
- Copy all deposits/withdrawals
- Copy stock positions (if any exist)
- Verify data integrity

### To Run Data Migration:

```bash
cd backend

# Set both database URLs
export OLD_DATABASE_URL="postgresql://options_tracker_user:KLvsWK9feDVuydyrPA7RftVNeyYeUXEE@dpg-d53g04tactks73edsctg-a.ohio-postgres.render.com/options_tracker_peqw"
export NEW_DATABASE_URL="postgresql://options_tracker_new_db_user:J7qsnDUWd1Y7yKgOLjFX2qnnimMU60vp@dpg-d5aleduuk2gs73er5c40-a.ohio-postgres.render.com/options_tracker_new_db"

# Run migration
python3 migrate_data_to_new_db.py
```

**OR** use command line arguments:

```bash
python3 migrate_data_to_new_db.py \
  --old-db-url "postgresql://options_tracker_user:KLvsWK9feDVuydyrPA7RftVNeyYeUXEE@dpg-d53g04tactks73edsctg-a.ohio-postgres.render.com/options_tracker_peqw" \
  --new-db-url "postgresql://options_tracker_new_db_user:J7qsnDUWd1Y7yKgOLjFX2qnnimMU60vp@dpg-d5aleduuk2gs73er5c40-a.ohio-postgres.render.com/options_tracker_new_db"
```

## Testing New Database

### Test Locally First

1. **Update local .env** to point to new database:
   ```bash
   DATABASE_URL="postgresql://options_tracker_new_db_user:J7qsnDUWd1Y7yKgOLjFX2qnnimMU60vp@dpg-d5aleduuk2gs73er5c40-a.ohio-postgres.render.com/options_tracker_new_db"
   ```

2. **Start backend** and test:
   - Login
   - Create account
   - Create trade
   - Test new features (stock positions, close workflow, default fees)

3. **If everything works**, proceed with data migration

## Deployment Plan

### Phase 1: Test New Database (Current)
- ✅ New database created and initialized
- ⏳ Test locally with new database
- ⏳ Verify all v1.4.0 features work

### Phase 2: Migrate Data
- ⏳ Run data migration script
- ⏳ Verify data integrity
- ⏳ Test with migrated data

### Phase 3: Switch Production
- ⏳ Update Render backend DATABASE_URL
- ⏳ Monitor for issues
- ⏳ Keep old database as backup for 1-2 weeks

## Safety Features

- ✅ **Old database untouched** - Serves as backup
- ✅ **Can rollback** - Switch back to old database if needed
- ✅ **Testable** - Can test thoroughly before switching
- ✅ **No data loss** - Old data remains intact

## Files Created

1. `initialize_new_database.py` - Initializes new DB with v1.4.0 schema
2. `migrate_data_to_new_db.py` - Migrates data from old to new DB
3. `DEPLOYMENT_PLAN_V1.4.0.md` - Full deployment plan
4. `DATABASE_STRATEGY_ANALYSIS.md` - Strategy analysis

## Questions?

Let me know if you want to:
1. **Test the new database first** (recommended)
2. **Migrate data now**
3. **Make any changes** to the migration scripts

