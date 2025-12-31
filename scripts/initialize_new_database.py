#!/usr/bin/env python3
"""
Initialize new database with v1.4.0 schema.

This script:
1. Creates all base tables (users, accounts, trades, etc.) using Flask models
2. Runs all migrations to add v1.4.0 specific features
3. Verifies the schema is complete

Usage:
    python initialize_new_database.py --database-url DATABASE_URL
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path to import app and models
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def initialize_database(database_url):
    """Initialize database with v1.4.0 schema"""
    print("=" * 80)
    print("Initialize New Database with v1.4.0 Schema")
    print("=" * 80)
    print(f"Database: {database_url[:50]}...\n")
    
    # Set database URL in environment
    os.environ['DATABASE_URL'] = database_url
    
    # Import app and models (this will use the DATABASE_URL from env)
    from app import app, db
    from models import User, Account, Trade, Deposit, Withdrawal, StockPosition
    
    with app.app_context():
        print("Step 1: Creating base schema (users, accounts, trades, etc.)...")
        try:
            # Create all tables
            db.create_all()
            print("✅ Base schema created successfully")
        except Exception as e:
            print(f"❌ Error creating base schema: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Verify base tables exist
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        required_base_tables = ['users', 'accounts', 'trades', 'deposits', 'withdrawals']
        missing = [t for t in required_base_tables if t not in tables]
        
        if missing:
            print(f"❌ Missing base tables: {', '.join(missing)}")
            return False
        
        print(f"✅ Base tables verified: {', '.join(required_base_tables)}")
        
        # Now run migrations for v1.4.0 features
        print("\nStep 2: Running v1.4.0 migrations...")
        
        # Run migrations - each has different function signatures
        print(f"\nRunning Stock Positions migration...")
        try:
            from migrate_add_stock_positions import migrate_database as migrate_stock_positions
            migrate_stock_positions(database_url)
            print(f"✅ Stock Positions migration completed")
        except Exception as e:
            print(f"❌ Stock Positions migration failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        print(f"\nRunning Close Fields migration...")
        try:
            # This migration uses environment variable, so set it
            os.environ['DATABASE_URL'] = database_url
            from migrate_add_close_fields import migrate_database as migrate_close_fields
            migrate_close_fields()  # This one takes no arguments, uses env var
            print(f"✅ Close Fields migration completed")
        except Exception as e:
            print(f"❌ Close Fields migration failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        print(f"\nRunning Default Fee migration...")
        try:
            from migrate_add_default_fee import migrate_database as migrate_default_fee
            migrate_default_fee(database_url)
            print(f"✅ Default Fee migration completed")
        except Exception as e:
            print(f"❌ Default Fee migration failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Final verification
        print("\nStep 3: Verifying v1.4.0 schema...")
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        # Check for stock_positions table
        if 'stock_positions' in tables:
            print("✅ stock_positions table exists")
        else:
            print("❌ stock_positions table missing")
            return False
        
        # Check accounts.default_fee
        accounts_cols = [c['name'] for c in inspector.get_columns('accounts')]
        if 'default_fee' in accounts_cols:
            print("✅ accounts.default_fee column exists")
        else:
            print("❌ accounts.default_fee column missing")
            return False
        
        # Check trades columns
        trades_cols = [c['name'] for c in inspector.get_columns('trades')]
        v1_4_cols = ['close_price', 'close_fees', 'close_premium', 'close_method', 'stock_position_id', 'shares_used']
        all_present = True
        for col in v1_4_cols:
            if col in trades_cols:
                print(f"✅ trades.{col} column exists")
            else:
                print(f"❌ trades.{col} column missing")
                all_present = False
        
        if not all_present:
            return False
        
        print("\n" + "=" * 80)
        print("✅ Database initialized successfully with v1.4.0 schema!")
        print("=" * 80)
        return True

def main():
    """Main entry point"""
    database_url = os.getenv('DATABASE_URL')
    
    if '--database-url' in sys.argv:
        idx = sys.argv.index('--database-url')
        if idx + 1 < len(sys.argv):
            database_url = sys.argv[idx + 1]
    
    if not database_url:
        print("❌ DATABASE_URL not set")
        print("Usage: python initialize_new_database.py [--database-url DATABASE_URL]")
        print("Or set DATABASE_URL environment variable")
        sys.exit(1)
    
    try:
        success = initialize_database(database_url)
        if success:
            print("\n✅ Database initialization completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Database initialization failed. Please review errors above.")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()

