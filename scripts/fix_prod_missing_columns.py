#!/usr/bin/env python3
"""
Migration script to add all missing columns to production database.

This script adds:
- Trades table: close_price, close_fees, close_premium, close_method, assignment_fee, stock_position_id, shares_used
- Accounts table: assignment_fee

Usage:
    python3 scripts/fix_prod_missing_columns.py

The script uses DATABASE_URL from environment variable (production database).
"""

import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect

# Load environment variables
load_dotenv()

def check_column_exists(engine, table_name, column_name):
    """Check if a column exists in a table"""
    inspector = inspect(engine)
    try:
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        return column_name in columns
    except Exception:
        return False

def migrate_database(database_url):
    """Run the migration"""
    # Create engine
    if database_url.startswith('postgresql://') or database_url.startswith('postgres://'):
        if 'sslmode' not in database_url:
            separator = '&' if '?' in database_url else '?'
            database_url = f"{database_url}{separator}sslmode=require"
    
    engine = create_engine(database_url)
    
    print(f"\n{'='*80}")
    print("Fix Production Database - Add Missing Columns")
    print(f"{'='*80}")
    print(f"Database: {database_url[:50]}...\n")
    
    with engine.connect() as conn:
        inspector = inspect(engine)
        trans = conn.begin()
        
        try:
            migrations_applied = []
            
            # Migrate trades table
            if 'trades' in inspector.get_table_names():
                print("Checking trades table...")
                
                # List of columns to add with their definitions
                trades_columns = [
                    ('close_price', 'NUMERIC(10, 2)'),
                    ('close_fees', 'NUMERIC(10, 2)'),
                    ('close_premium', 'NUMERIC(15, 2)'),
                    ('close_method', 'VARCHAR(20)'),
                    ('assignment_fee', 'NUMERIC(10, 2) DEFAULT 0'),
                    ('stock_position_id', 'INTEGER'),
                    ('shares_used', 'INTEGER'),
                ]
                
                for col_name, col_type in trades_columns:
                    if not check_column_exists(engine, 'trades', col_name):
                        print(f"  Adding {col_name} column to trades table...")
                        conn.execute(text(f"ALTER TABLE trades ADD COLUMN {col_name} {col_type}"))
                        migrations_applied.append(f'trades.{col_name}')
                        print(f"  ✓ Added {col_name}")
                    else:
                        print(f"  ✓ {col_name} already exists")
            
            # Migrate accounts table
            if 'accounts' in inspector.get_table_names():
                print("\nChecking accounts table...")
                
                if not check_column_exists(engine, 'accounts', 'assignment_fee'):
                    print("  Adding assignment_fee column to accounts table...")
                    conn.execute(text("ALTER TABLE accounts ADD COLUMN assignment_fee NUMERIC(10, 2) DEFAULT 0"))
                    migrations_applied.append('accounts.assignment_fee')
                    print("  ✓ Added assignment_fee")
                else:
                    print("  ✓ assignment_fee already exists")
            
            # Commit transaction
            trans.commit()
            
            if migrations_applied:
                print(f"\n✅ Migration completed successfully!")
                print(f"Applied {len(migrations_applied)} changes:")
                for change in migrations_applied:
                    print(f"  - {change}")
            else:
                print("\n✅ All columns already exist - no changes needed")
            
        except Exception as e:
            trans.rollback()
            print(f"\n❌ Error during migration: {str(e)}")
            import traceback
            traceback.print_exc()
            raise

def main():
    """Main entry point"""
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("ERROR: DATABASE_URL environment variable is not set")
        print("Please set it to your production database URL")
        sys.exit(1)
    
    print(f"Using DATABASE_URL: {database_url[:50]}...")
    
    try:
        migrate_database(database_url)
    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    print("Starting migration: Fix missing columns in production database...")
    main()

