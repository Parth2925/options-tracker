#!/usr/bin/env python3
"""
Database migration script to add default_fee column to accounts table.

This migration:
1. Adds default_fee column to accounts table (Numeric(10, 2), default=0)

Usage:
    python migrate_add_default_fee.py [--database-url DATABASE_URL]
    
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
    print("Add Default Fee Column Migration")
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
                print("   It will be created when you run db.create_all()")
                trans.rollback()
                return
            
            # Check if column already exists
            if check_column_exists(engine, 'accounts', 'default_fee'):
                print("✓ Column 'default_fee' already exists in 'accounts' table")
                trans.rollback()
                return
            
            # Add default_fee column
            print("Adding 'default_fee' column to 'accounts' table...")
            
            if database_url.startswith('sqlite'):
                # SQLite syntax
                conn.execute(text("""
                    ALTER TABLE accounts 
                    ADD COLUMN default_fee NUMERIC(10, 2) DEFAULT 0
                """))
            else:
                # PostgreSQL syntax
                conn.execute(text("""
                    ALTER TABLE accounts 
                    ADD COLUMN default_fee NUMERIC(10, 2) DEFAULT 0
                """))
            
            # Commit transaction
            trans.commit()
            print("✓ Successfully added 'default_fee' column to 'accounts' table")
            
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
        print("Error: DATABASE_URL not set")
        print("Usage: python migrate_add_default_fee.py [--database-url DATABASE_URL]")
        print("Or set DATABASE_URL environment variable")
        sys.exit(1)
    
    try:
        migrate_database(database_url)
        print("\n✓ Migration completed successfully!")
    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()

