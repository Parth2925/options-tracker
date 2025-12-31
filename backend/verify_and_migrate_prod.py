#!/usr/bin/env python3
"""
Script to verify and run all migrations on production database
"""
import os
from sqlalchemy import create_engine, inspect, text

DATABASE_URL = "postgresql://options_tracker_user:KLvsWK9feDVuydyrPA7RftVNeyYeUXEE@dpg-d53g04tactks73edsctg-a.ohio-postgres.render.com/options_tracker_peqw?sslmode=require"
engine = create_engine(DATABASE_URL)
inspector = inspect(engine)

print("=== Production Database Schema Status ===")
print()

print("[Step 1/4] Checking current database schema...")
# Check accounts columns
accounts_cols = [c['name'] for c in inspector.get_columns('accounts')]
print("Accounts columns:")
for col in sorted(accounts_cols):
    print(f"  - {col}")

# Check trades columns
trades_cols = [c['name'] for c in inspector.get_columns('trades')]
print("\nTrades columns (key ones):")
key_cols = ['stock_position_id', 'shares_used', 'close_price', 'close_fees', 'close_premium', 'close_method']
for col in key_cols:
    exists = col in trades_cols
    print(f"  {'✓' if exists else '✗'} {col}")

# Check stock_positions table
has_stock_positions = 'stock_positions' in inspector.get_table_names()
print(f"\nstock_positions table: {'✓ EXISTS' if has_stock_positions else '✗ MISSING'}")

# Run missing migrations
print("\n=== Running Missing Migrations ===")
print("[Step 2/4] Connecting to database...")
with engine.connect() as conn:
    print("[Step 3/4] Starting transaction...")
    trans = conn.begin()
    try:
        # 1. Add default_fee if missing
        if 'default_fee' not in accounts_cols:
            print("[Migration 1/3] Adding default_fee to accounts table...")
            print("   Executing: ALTER TABLE accounts ADD COLUMN default_fee NUMERIC(10, 2) DEFAULT 0")
            conn.execute(text("ALTER TABLE accounts ADD COLUMN default_fee NUMERIC(10, 2) DEFAULT 0"))
            print("   ✓ Column added successfully")
        else:
            print("[Migration 1/3] ✓ default_fee already exists - skipping")
        
        # 2. Create stock_positions table if missing
        if not has_stock_positions:
            print("[Migration 2/3] Creating stock_positions table...")
            print("   This may take a few seconds...")
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
            print("   Table created. Creating indexes...")
            conn.execute(text("CREATE INDEX idx_stock_positions_symbol ON stock_positions(symbol)"))
            conn.execute(text("CREATE INDEX idx_stock_positions_account_id ON stock_positions(account_id)"))
            print("   ✓ Table and indexes created successfully")
        else:
            print("[Migration 2/3] ✓ stock_positions table already exists - skipping")
        
        # 3. Add trades columns if missing
        print("[Migration 3/3] Checking/adding trades table columns...")
        cols_to_add = [
            ('stock_position_id', 'INTEGER'),
            ('shares_used', 'INTEGER'),
            ('close_price', 'NUMERIC(10, 2)'),
            ('close_fees', 'NUMERIC(10, 2)'),
            ('close_premium', 'NUMERIC(15, 2)'),
            ('close_method', 'VARCHAR(20)')
        ]
        for col_name, col_type in cols_to_add:
            if col_name not in trades_cols:
                print(f"   Adding {col_name} to trades table...")
                conn.execute(text(f"ALTER TABLE trades ADD COLUMN {col_name} {col_type}"))
                print(f"   ✓ Added {col_name}")
            else:
                print(f"   ✓ {col_name} already exists - skipping")
        
        print("[Step 4/4] Committing all changes...")
        trans.commit()
        print("\n✅ All migrations completed successfully!")
        
    except Exception as e:
        trans.rollback()
        print(f"\n❌ Error: {e}")
        raise

# Final verification
print("\n=== Final Verification ===")
inspector = inspect(engine)
accounts_cols = [c['name'] for c in inspector.get_columns('accounts')]
trades_cols = [c['name'] for c in inspector.get_columns('trades')]
has_stock_positions = 'stock_positions' in inspector.get_table_names()

all_good = (
    'default_fee' in accounts_cols and
    all(col in trades_cols for col in key_cols) and
    has_stock_positions
)

if all_good:
    print("✅ ALL MIGRATIONS VERIFIED - Database schema is complete!")
else:
    print("❌ Some migrations may have failed - please check above")

