# Pre-Merge Checklist

## ✅ Pre-Merge Tasks

### 1. Code Cleanup
- [ ] Remove all debug instrumentation logs from `backend/routes/auth.py`
- [ ] Remove all debug instrumentation logs from `frontend/src/components/Trades/Trades.js`
- [ ] Verify no `console.log` statements remain (except intentional ones)
- [ ] Check for any TODO/FIXME comments that need attention

### 2. Version Management
- [ ] Decide on version bump (recommended: 1.3.0 → 1.4.0 for major feature release)
- [ ] Update `backend/version.py`
- [ ] Update `frontend/src/utils/version.js`
- [ ] Update `frontend/package.json` (if needed)
- [ ] Run `increment-version.sh` script if using automated versioning

### 3. Database Migrations
**Migration Order (MUST RUN IN THIS ORDER):**
1. [ ] `migrate_add_stock_positions.py` - Creates stock_positions table and adds columns to trades
2. [ ] `migrate_add_close_fields.py` - Adds close_price, close_fees, close_premium, close_method to trades
3. [ ] `migrate_add_default_fee.py` - Adds default_fee to accounts
4. [ ] `migrate_existing_data.py` - Migrates existing data (optional, but recommended)

**Production Migration Steps:**
```bash
# Set production database URL
export DATABASE_URL="postgresql://user:pass@host/dbname"

# Run migrations in order
cd backend
python3 migrate_add_stock_positions.py
python3 migrate_add_close_fields.py
python3 migrate_add_default_fee.py
python3 migrate_existing_data.py  # Optional: for existing data
```

### 4. Testing
- [ ] Run full test suite: `cd backend && pytest tests/ -v`
- [ ] Verify all tests pass
- [ ] Test backward compatibility with old-format trades
- [ ] Test new features (stock positions, enhanced close workflow)
- [ ] Test import/export with both old and new formats

### 5. Documentation
- [ ] Update `MIGRATION_NOTES.md` with all migration scripts
- [ ] Verify `BACKWARD_COMPATIBILITY_VERIFICATION.md` is accurate
- [ ] Update `README.md` if needed
- [ ] Check that `TEST_PLAN_STOCK_POSITIONS.md` is complete

### 6. Production Readiness
- [ ] Verify environment variables are documented
- [ ] Check that all API keys (Finnhub) are configured
- [ ] Verify CORS settings are correct
- [ ] Ensure error handling is comprehensive
- [ ] Check mobile responsiveness

### 7. Final Verification
- [ ] Code review completed
- [ ] All linter errors resolved
- [ ] No breaking changes for existing users
- [ ] Backward compatibility verified
- [ ] UI/UX consistency checked

## 🚨 Critical Items

1. **Debug Logs Removal** - MUST remove before merge
2. **Migration Order** - MUST run migrations in correct order
3. **Version Bump** - Should increment for this major feature release
4. **Test Suite** - MUST pass before merge

## 📝 Post-Merge Tasks

After merging to main:
1. Run migrations on production database
2. Deploy backend
3. Deploy frontend
4. Verify production deployment
5. Monitor for any issues
6. Update release notes

