# Improved Migration Script Plan

## Current Migration Scripts
1. `migrate_add_stock_positions.py` - Creates stock_positions table, adds columns to trades
2. `migrate_add_close_fields.py` - Adds close-related columns to trades
3. `migrate_add_default_fee.py` - Adds default_fee to accounts

## Issues to Fix

### 1. Connection Timeout & Hanging
**Problem**: Scripts hang when connecting to production PostgreSQL
**Solution**:
- Add explicit connection timeout (10-15 seconds)
- Use `connect_timeout` in connection string
- Add timeout wrapper for long operations
- Use `statement_timeout` for PostgreSQL queries

### 2. Progress Visibility
**Problem**: No feedback during execution, appears hung
**Solution**:
- Add timestamped logging at every step
- Show progress percentage
- Log to both console and file
- Use `sys.stdout.flush()` to ensure immediate output

### 3. Error Handling
**Problem**: Generic errors, hard to diagnose
**Solution**:
- Catch specific exception types
- Provide context in error messages
- Log full stack traces to file
- Suggest common fixes

### 4. Verification
**Problem**: No way to verify migrations completed
**Solution**:
- Create separate verification script
- Check schema after each migration
- Provide clear pass/fail status
- List what's missing if verification fails

### 5. Idempotency
**Problem**: Running migrations twice might fail
**Solution**:
- Check if changes already exist before applying
- Make operations safe to run multiple times
- Skip if already complete (with clear message)

## Proposed New Script Structure

### Enhanced Migration Script Template
```python
#!/usr/bin/env python3
"""
Enhanced migration script with:
- Progress logging
- Timeout handling
- Error recovery
- Verification
"""
import os
import sys
import time
from datetime import datetime
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import OperationalError, ProgrammingError

# Configuration
CONNECTION_TIMEOUT = 15  # seconds
STATEMENT_TIMEOUT = 30   # seconds
LOG_FILE = 'migration.log'

def log(message, level='INFO'):
    """Log with timestamp"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_msg = f"[{timestamp}] [{level}] {message}"
    print(log_msg)
    sys.stdout.flush()
    
    # Also log to file
    with open(LOG_FILE, 'a') as f:
        f.write(log_msg + '\n')

def create_engine_with_timeout(database_url):
    """Create engine with proper timeout settings"""
    if database_url.startswith('postgresql://') or database_url.startswith('postgres://'):
        # Add connection timeout
        if '?' in database_url:
            database_url += '&connect_timeout=15'
        else:
            database_url += '?connect_timeout=15'
        
        return create_engine(
            database_url,
            pool_pre_ping=True,
            pool_recycle=300,
            connect_args={
                'connect_timeout': 15,
                'options': f'-c statement_timeout={STATEMENT_TIMEOUT * 1000}'
            }
        )
    else:
        # SQLite
        from sqlalchemy.pool import NullPool
        return create_engine(
            database_url,
            poolclass=NullPool,
            connect_args={'check_same_thread': False}
        )

def run_migration_with_retry(operation, max_retries=3):
    """Run operation with retry logic"""
    for attempt in range(1, max_retries + 1):
        try:
            log(f"Attempt {attempt}/{max_retries}")
            return operation()
        except OperationalError as e:
            if attempt < max_retries:
                wait_time = 2 ** attempt  # Exponential backoff
                log(f"Connection error, retrying in {wait_time}s: {e}")
                time.sleep(wait_time)
            else:
                log(f"Failed after {max_retries} attempts: {e}", 'ERROR')
                raise
        except Exception as e:
            log(f"Unexpected error: {e}", 'ERROR')
            raise

def verify_migration(engine, checks):
    """Verify migration completed successfully"""
    log("Verifying migration...")
    inspector = inspect(engine)
    
    for check_name, check_func in checks.items():
        try:
            result = check_func(inspector)
            if result:
                log(f"✓ {check_name}: PASS")
            else:
                log(f"✗ {check_name}: FAIL", 'ERROR')
                return False
        except Exception as e:
            log(f"✗ {check_name}: ERROR - {e}", 'ERROR')
            return False
    
    log("✓ All verifications passed")
    return True

# Main migration logic would go here...
```

### Verification Script
```python
#!/usr/bin/env python3
"""
Migration verification script
Usage: python verify_migrations.py [--all|--check <migration_name>]
"""
import sys
from sqlalchemy import create_engine, inspect

def verify_all(engine):
    """Verify all migrations"""
    inspector = inspect(engine)
    
    checks = {
        'default_fee': lambda: 'default_fee' in [c['name'] for c in inspector.get_columns('accounts')],
        'stock_positions_table': lambda: 'stock_positions' in inspector.get_table_names(),
        'stock_position_id': lambda: 'stock_position_id' in [c['name'] for c in inspector.get_columns('trades')],
        'close_price': lambda: 'close_price' in [c['name'] for c in inspector.get_columns('trades')],
        # ... more checks
    }
    
    results = {}
    for name, check in checks.items():
        try:
            results[name] = check()
        except Exception as e:
            results[name] = f"ERROR: {e}"
    
    return results

# Print results...
```

## Implementation Priority

1. **High Priority** (Must have before production):
   - Progress logging with timestamps
   - Connection timeout handling
   - Verification script
   - Better error messages

2. **Medium Priority** (Nice to have):
   - Retry logic
   - Log file output
   - Progress percentage

3. **Low Priority** (Future improvements):
   - Migration rollback
   - Dry-run mode
   - Migration history tracking

