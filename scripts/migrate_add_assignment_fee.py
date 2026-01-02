#!/usr/bin/env python3
"""
Migration script to add assignment_fee field to accounts and trades tables.

This migration:
1. Adds assignment_fee column to accounts table (default: 0)
2. Adds assignment_fee column to trades table (default: 0)

Usage:
    python3 migrate_add_assignment_fee.py [--database-url DATABASE_URL]
    
    Or set DATABASE_URL environment variable
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
    print("Add Assignment Fee Column Migration")
    print(f"{'='*80}")
    print(f"Database: {database_url[:50]}...\n")
    
    with engine.connect() as conn:
        # Start transaction
        trans = conn.begin()
        
        try:
            # Check if accounts table exists
            inspector = inspect(engine)
            if 'accounts' not in inspector.get_table_names():
                print("⚠️  Warning: 'accounts' table does not exist.")
                trans.rollback()
                return
            
            # Add assignment_fee to accounts table if it doesn't exist
            if check_column_exists(engine, 'accounts', 'assignment_fee'):
                print("✓ Column 'assignment_fee' already exists in 'accounts' table")
            else:
                print("Adding 'assignment_fee' column to 'accounts' table...")
                conn.execute(text("ALTER TABLE accounts ADD COLUMN assignment_fee NUMERIC(10, 2) DEFAULT 0"))
                print("✓ Successfully added 'assignment_fee' column to 'accounts' table")
            
            # Check if trades table exists
            if 'trades' not in inspector.get_table_names():
                print("⚠️  Warning: 'trades' table does not exist.")
                trans.rollback()
                return
            
            # Add assignment_fee to trades table if it doesn't exist
            if check_column_exists(engine, 'trades', 'assignment_fee'):
                print("✓ Column 'assignment_fee' already exists in 'trades' table")
            else:
                print("Adding 'assignment_fee' column to 'trades' table...")
                conn.execute(text("ALTER TABLE trades ADD COLUMN assignment_fee NUMERIC(10, 2) DEFAULT 0"))
                print("✓ Successfully added 'assignment_fee' column to 'trades' table")
            
            # Commit transaction
            trans.commit()
            print("\n✅ Migration completed successfully!")
            
        except Exception as e:
            trans.rollback()
            print(f"❌ Error during migration: {str(e)}")
            raise

def main():
    """Main entry point"""
    # Get database URL from environment or command line
    database_url = os.getenv('DATABASE_URL')
    
    if '--database-url' in sys.argv:
        idx = sys.argv.index('--database-url')
        if idx + 1 < len(sys.argv):
            database_url = sys.argv[idx + 1]
    
    if not database_url:
        # Default to local SQLite if no DATABASE_URL set
        database_url = 'sqlite:///backend/options_tracker.db'
        print(f"No DATABASE_URL found, using default: {database_url}")
    
    try:
        migrate_database(database_url)
    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    print("Starting migration: Add assignment_fee columns...")
    main()

