#!/usr/bin/env python3
"""
Fix production database schema by running v1.4.0 migrations.

This script will:
1. Check which columns are missing
2. Run migrations to add missing columns
3. Verify all columns exist

Usage:
    python fix_production_schema.py --database-url DATABASE_URL
"""
import os
import sys
import argparse
from sqlalchemy import create_engine, inspect, text
from dotenv import load_dotenv

def check_schema(database_url):
    """Check what columns exist in the database"""
    print("=" * 80)
    print("Checking Database Schema")
    print("=" * 80)
    
    engine = create_engine(database_url, pool_pre_ping=True, connect_args={'connect_timeout': 15})
    inspector = inspect(engine)
    
    # Check trades table
    print("\n=== Trades Table ===")
    try:
        trade_cols = [c['name'] for c in inspector.get_columns('trades')]
        print(f"Existing columns ({len(trade_cols)}): {', '.join(sorted(trade_cols))}")
        
        required_cols = {
            'close_price': 'Numeric(10, 2)',
            'close_fees': 'Numeric(10, 2)',
            'close_premium': 'Numeric(15, 2)',
            'close_method': 'VARCHAR(20)',
            'stock_position_id': 'Integer',
            'shares_used': 'Integer'
        }
        
        missing = [col for col in required_cols.keys() if col not in trade_cols]
        
        if missing:
            print(f"\n❌ Missing columns: {', '.join(missing)}")
            return False, missing
        else:
            print(f"\n✅ All v1.4.0 columns present")
            return True, []
    except Exception as e:
        print(f"❌ Error checking trades table: {e}")
        return False, []
    
def run_migrations(database_url):
    """Run migrations to add missing columns"""
    print("\n" + "=" * 80)
    print("Running Migrations")
    print("=" * 80)
    
    # Import migration functions
    try:
        from migrate_add_stock_positions import migrate_database as migrate_stock_positions
        from migrate_add_close_fields import migrate_database as migrate_close_fields
        from migrate_add_default_fee import migrate_database as migrate_default_fee
    except ImportError as e:
        print(f"❌ Error importing migrations: {e}")
        return False
    
    # Set environment variable for migrations that use it
    os.environ['DATABASE_URL'] = database_url
    
    # Run migrations in order
    migrations = [
        ("Stock Positions", migrate_stock_positions, [database_url]),
        ("Close Fields", migrate_close_fields, []),  # Uses env var
        ("Default Fee", migrate_default_fee, [database_url]),
    ]
    
    for name, func, args in migrations:
        print(f"\n--- Running {name} migration ---")
        try:
            func(*args)
            print(f"✅ {name} migration completed")
        except Exception as e:
            print(f"⚠️  {name} migration: {e}")
            # Continue with other migrations
    
    return True

def main():
    parser = argparse.ArgumentParser(description='Fix production database schema')
    parser.add_argument('--database-url', type=str, help='Database URL to fix')
    args = parser.parse_args()
    
    # Get database URL
    if args.database_url:
        database_url = args.database_url
    else:
        load_dotenv()
        database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("❌ Error: DATABASE_URL not provided")
        print("Usage: python fix_production_schema.py --database-url DATABASE_URL")
        sys.exit(1)
    
    # Check schema
    schema_ok, missing = check_schema(database_url)
    
    if schema_ok:
        print("\n✅ Schema is already correct. No migrations needed.")
        return
    
    # Run migrations
    if missing:
        print(f"\n⚠️  Missing columns detected. Running migrations...")
        success = run_migrations(database_url)
        
        if success:
            # Verify again
            print("\n" + "=" * 80)
            print("Verifying Schema After Migrations")
            print("=" * 80)
            schema_ok, _ = check_schema(database_url)
            
            if schema_ok:
                print("\n✅ Schema is now correct!")
            else:
                print("\n❌ Some columns are still missing. Please check manually.")
        else:
            print("\n❌ Migrations failed. Please check errors above.")

if __name__ == '__main__':
    main()

