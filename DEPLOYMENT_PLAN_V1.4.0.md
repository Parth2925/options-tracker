# Deployment Plan for Version 1.4.0

## Overview
This document outlines a safe, stepped approach to deploy v1.4.0 to production, addressing the issues encountered during the previous deployment attempt.

## Issues Encountered Previously

1. **Database Migration Hanging**: Migrations appeared to hang indefinitely when connecting to production PostgreSQL
2. **Missing Schema Changes**: Code deployed but database schema wasn't updated, causing runtime errors
3. **Connection Timeouts**: PostgreSQL connection issues during migration execution
4. **Version Mismatch**: Production showed v1.3.0 instead of v1.4.0

## Pre-Deployment Checklist

### Phase 1: Local Testing & Verification

#### 1.1 Verify Feature Branch
- [ ] All tests pass locally
- [ ] SQLite connection works (already fixed)
- [ ] All v1.4.0 features work in local environment
- [ ] No linter errors
- [ ] Code review completed

#### 1.2 Test Migrations Locally
- [ ] Create a test SQLite database
- [ ] Run all three migrations sequentially:
  - [ ] `migrate_add_stock_positions.py`
  - [ ] `migrate_add_close_fields.py`
  - [ ] `migrate_add_default_fee.py`
- [ ] Verify schema changes applied correctly
- [ ] Test with existing data (import old format trades)
- [ ] Verify backward compatibility

#### 1.3 Test Migrations with PostgreSQL (Local/Staging)
- [ ] Set up local PostgreSQL instance (or use staging database)
- [ ] Test migrations on PostgreSQL
- [ ] Verify connection handling
- [ ] Test with production-like data volume
- [ ] Measure migration execution time

### Phase 2: Migration Script Improvements

#### 2.1 Create Improved Migration Script
**Issues to Address:**
- Connection timeouts
- Hanging operations
- Better progress logging
- Error handling and rollback

**Requirements:**
- [ ] Add connection timeout handling
- [ ] Add progress logging with timestamps
- [ ] Add retry logic for transient failures
- [ ] Add verification step after each migration
- [ ] Add rollback capability
- [ ] Test script thoroughly

#### 2.2 Create Migration Verification Script
- [ ] Script to verify all schema changes are applied
- [ ] Can be run before/after deployment
- [ ] Provides clear pass/fail status

### Phase 3: Staged Deployment

#### 3.1 Database Migration (CRITICAL - Do First)
**Step 1: Backup Production Database**
```bash
# Create a full backup before any changes
pg_dump "postgresql://..." > backup_$(date +%Y%m%d_%H%M%S).sql
```

**Step 2: Run Migrations One at a Time**
```bash
# Migration 1: Stock Positions
python3 migrate_add_stock_positions.py

# Verify
python3 verify_migrations.py --check stock_positions

# Migration 2: Close Fields
python3 migrate_add_close_fields.py

# Verify
python3 verify_migrations.py --check close_fields

# Migration 3: Default Fee
python3 migrate_add_default_fee.py

# Verify
python3 verify_migrations.py --check default_fee
```

**Step 3: Final Verification**
```bash
# Verify all migrations complete
python3 verify_migrations.py --all
```

#### 3.2 Code Deployment
**Only after migrations are verified:**
- [ ] Merge feature branch to main
- [ ] Push to remote
- [ ] Monitor Render deployment logs
- [ ] Monitor Vercel deployment logs
- [ ] Verify version shows 1.4.0

#### 3.3 Post-Deployment Verification
- [ ] Test login
- [ ] Test accounts page (verify default_fee works)
- [ ] Test trades page
- [ ] Test dashboard
- [ ] Test new features (stock positions, close workflow)
- [ ] Verify version in About page

### Phase 4: Rollback Plan

#### 4.1 If Migrations Fail
- [ ] Restore database from backup
- [ ] Verify database restored correctly
- [ ] Document what went wrong
- [ ] Fix issues before retry

#### 4.2 If Code Deployment Fails
- [ ] Revert main branch to previous commit
- [ ] Force push to remote
- [ ] Verify production reverts to v1.3.0
- [ ] Database schema changes can remain (they're backward compatible)

## Migration Script Improvements Needed

### Current Issues
1. **No Progress Feedback**: Scripts appear to hang
2. **No Timeout Handling**: Connections can hang indefinitely
3. **No Retry Logic**: Transient failures cause complete failure
4. **Poor Error Messages**: Hard to diagnose issues

### Proposed Improvements

#### 1. Enhanced Progress Logging
- Timestamp every operation
- Show what's happening at each step
- Estimate time remaining
- Log to file for review

#### 2. Connection Management
- Set explicit connection timeouts
- Use connection pooling correctly
- Handle connection drops gracefully
- Retry with exponential backoff

#### 3. Transaction Safety
- Smaller transactions where possible
- Clear rollback on errors
- Verification after each change
- Idempotent operations (safe to run multiple times)

#### 4. Better Error Handling
- Catch specific error types
- Provide actionable error messages
- Suggest fixes for common issues
- Log full error details for debugging

## Questions for You

1. **Staging Environment**: Do you have a staging database we can test migrations on first?
2. **Maintenance Window**: Is there a preferred time for deployment (low traffic period)?
3. **Backup Strategy**: Do you have automated backups, or should we create manual backup?
4. **Monitoring**: What monitoring/alerting do you have for production?
5. **Rollback Window**: How quickly do you need to be able to rollback if issues occur?

## Next Steps

1. **Create improved migration scripts** with better logging and error handling
2. **Create verification script** to check migration status
3. **Test migrations locally** with PostgreSQL
4. **Get your input** on staging environment and deployment timing
5. **Execute deployment** following the stepped plan

## Timeline Estimate

- **Phase 1 (Local Testing)**: 1-2 hours
- **Phase 2 (Script Improvements)**: 2-3 hours
- **Phase 3 (Actual Deployment)**: 30-60 minutes
- **Total**: ~4-6 hours of work, can be spread over multiple sessions

