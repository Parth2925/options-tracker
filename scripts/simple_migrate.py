#!/usr/bin/env python3
"""
Simple, direct migration script with clear progress logging.
Runs one operation at a time to avoid hanging.
"""
import os
import sys
from sqlalchemy import create_engine, text, inspect
import time

DATABASE_URL = "postgresql://options_tracker_user:KLvsWK9feDVuydyrPA7RftVNeyYeUXEE@dpg-d53g04tactks73edsctg-a.ohio-postgres.render.com/options_tracker_peqw?sslmode=require"

def log(message):
    """Print timestamped log message"""
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")
    sys.stdout.flush()  # Force immediate output

def check_column_exists(engine, table_name, column_name):
    """Check if a column exists"""
    try:
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        return column_name in columns
    except Exception as e:
        log(f"Error checking column: {e}")
        return False

def check_table_exists(engine, table_name):
    """Check if a table exists"""
    try:
        inspector = inspect(engine)
        return table_name in inspector.get_table_names()
    except Exception as e:
        log(f"Error checking table: {e}")
        return False

def main():
    log("=" * 80)
    log("Simple Migration Script - Running one operation at a time")
    log("=" * 80)
    
    log("Connecting to database...")
    try:
        engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args={'connect_timeout': 10})
        log("✓ Connection established")
    except Exception as e:
        log(f"❌ Failed to connect: {e}")
        return 1
    
    # Test connection
    log("Testing connection...")
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).scalar()
            log(f"✓ Connection test successful: {result}")
    except Exception as e:
        log(f"❌ Connection test failed: {e}")
        return 1
    
    # Migration 1: Add default_fee to accounts
    log("\n" + "=" * 80)
    log("MIGRATION 1: Add default_fee to accounts table")
    log("=" * 80)
    
    try:
        with engine.connect() as conn:
            log("Checking if default_fee column exists...")
            if check_column_exists(engine, 'accounts', 'default_fee'):
                log("✓ default_fee already exists - skipping")
            else:
                log("✗ default_fee does not exist - adding now...")
                log("   Executing: ALTER TABLE accounts ADD COLUMN default_fee NUMERIC(10, 2) DEFAULT 0")
                start_time = time.time()
                conn.execute(text("ALTER TABLE accounts ADD COLUMN default_fee NUMERIC(10, 2) DEFAULT 0"))
                conn.commit()
                elapsed = time.time() - start_time
                log(f"✓ Column added successfully (took {elapsed:.2f} seconds)")
    except Exception as e:
        log(f"❌ Error: {e}")
        return 1
    
    # Migration 2: Create stock_positions table
    log("\n" + "=" * 80)
    log("MIGRATION 2: Create stock_positions table")
    log("=" * 80)
    
    try:
        with engine.connect() as conn:
            log("Checking if stock_positions table exists...")
            if check_table_exists(engine, 'stock_positions'):
                log("✓ stock_positions table already exists - skipping")
            else:
                log("✗ stock_positions table does not exist - creating now...")
                log("   This may take a few seconds...")
                start_time = time.time()
                
                # Create table
                conn.execute(text("""
                    CREATE TABLE stock_positions (
                        id SERIAL PRIMARY KEY,
                        account_id INTEGER NOT NULL,
                        symbol VARCHAR(20) NOT NULL,
                        shares INTEGER NOT NULL,
                        cost_basis_per_share NUMERIC(10, 2) NOT NULL,
                        acquired_date DATE NOT NULL,
                        status VARCHAR(20) DEFAULT 'Open',
                        source_trade_id INTEGER,
                        notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE,
                        FOREIGN KEY (source_trade_id) REFERENCES trades(id) ON DELETE SET NULL
                    )
                """))
                log("   Table created. Creating indexes...")
                
                # Create indexes
                conn.execute(text("CREATE INDEX idx_stock_positions_symbol ON stock_positions(symbol)"))
                conn.execute(text("CREATE INDEX idx_stock_positions_account_id ON stock_positions(account_id)"))
                
                conn.commit()
                elapsed = time.time() - start_time
                log(f"✓ Table and indexes created successfully (took {elapsed:.2f} seconds)")
    except Exception as e:
        log(f"❌ Error: {e}")
        return 1
    
    # Migration 3: Add columns to trades table
    log("\n" + "=" * 80)
    log("MIGRATION 3: Add columns to trades table")
    log("=" * 80)
    
    columns_to_add = [
        ('stock_position_id', 'INTEGER'),
        ('shares_used', 'INTEGER'),
        ('close_price', 'NUMERIC(10, 2)'),
        ('close_fees', 'NUMERIC(10, 2)'),
        ('close_premium', 'NUMERIC(15, 2)'),
        ('close_method', 'VARCHAR(20)')
    ]
    
    try:
        with engine.connect() as conn:
            for col_name, col_type in columns_to_add:
                log(f"Checking {col_name}...")
                if check_column_exists(engine, 'trades', col_name):
                    log(f"  ✓ {col_name} already exists - skipping")
                else:
                    log(f"  ✗ {col_name} does not exist - adding now...")
                    log(f"     Executing: ALTER TABLE trades ADD COLUMN {col_name} {col_type}")
                    start_time = time.time()
                    conn.execute(text(f"ALTER TABLE trades ADD COLUMN {col_name} {col_type}"))
                    conn.commit()
                    elapsed = time.time() - start_time
                    log(f"  ✓ {col_name} added successfully (took {elapsed:.2f} seconds)")
    except Exception as e:
        log(f"❌ Error: {e}")
        return 1
    
    # Final verification
    log("\n" + "=" * 80)
    log("FINAL VERIFICATION")
    log("=" * 80)
    
    try:
        inspector = inspect(engine)
        
        # Check accounts
        accounts_cols = [c['name'] for c in inspector.get_columns('accounts')]
        has_default_fee = 'default_fee' in accounts_cols
        log(f"accounts.default_fee: {'✓' if has_default_fee else '✗'}")
        
        # Check stock_positions
        has_stock_positions = 'stock_positions' in inspector.get_table_names()
        log(f"stock_positions table: {'✓' if has_stock_positions else '✗'}")
        
        # Check trades columns
        trades_cols = [c['name'] for c in inspector.get_columns('trades')]
        key_cols = ['stock_position_id', 'shares_used', 'close_price', 'close_fees', 'close_premium', 'close_method']
        for col in key_cols:
            exists = col in trades_cols
            log(f"trades.{col}: {'✓' if exists else '✗'}")
        
        all_good = (
            has_default_fee and
            has_stock_positions and
            all(col in trades_cols for col in key_cols)
        )
        
        if all_good:
            log("\n✅ ALL MIGRATIONS COMPLETE!")
            return 0
        else:
            log("\n❌ Some migrations are still missing")
            return 1
            
    except Exception as e:
        log(f"❌ Verification error: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())

