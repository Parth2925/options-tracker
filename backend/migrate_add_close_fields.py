#!/usr/bin/env python3
"""
Migration script to add close fields to trades table for single-entry close approach.

Adds fields:
- close_price: Price per contract when closed
- close_fees: Fees when closed
- close_premium: Calculated closing premium
- close_method: 'buy_to_close', 'sell_to_close', 'expired', 'assigned', 'exercise'

Usage:
    python migrate_add_close_fields.py [--database-url DATABASE_URL]
"""
import os
import sys
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import OperationalError, NoSuchTableError
from datetime import datetime
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

def get_db_url():
    return os.getenv('DATABASE_URL', 'sqlite:///options_tracker.db')

def is_postgresql(engine):
    return engine.name == 'postgresql'

def check_table_exists(engine, table_name):
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()

def check_column_exists(engine, table_name, column_name):
    inspector = inspect(engine)
    try:
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        return column_name in columns
    except NoSuchTableError:
        return False

def migrate_database():
    db_url = get_db_url()
    engine = create_engine(db_url)
    
    print(f"\n{'='*80}")
    print(f"Add Close Fields Migration")
    print(f"{'='*80}")
    print(f"Database: {db_url[:50]}...")

    with engine.connect() as connection:
        trans = connection.begin()
        try:
            if not check_table_exists(engine, 'trades'):
                print("⚠ trades table does not exist yet. It will be created when you run db.create_all()")
                trans.commit()
                return
            
            # 1. Add close_price column
            if not check_column_exists(engine, 'trades', 'close_price'):
                print("Adding close_price column to trades table...")
                if is_postgresql(engine):
                    connection.execute(text("ALTER TABLE trades ADD COLUMN close_price NUMERIC(10, 2)"))
                else:  # SQLite
                    connection.execute(text("ALTER TABLE trades ADD COLUMN close_price NUMERIC(10, 2)"))
                print("✓ close_price added")
            else:
                print("✓ close_price column already exists")
            
            # 2. Add close_fees column
            if not check_column_exists(engine, 'trades', 'close_fees'):
                print("Adding close_fees column to trades table...")
                if is_postgresql(engine):
                    connection.execute(text("ALTER TABLE trades ADD COLUMN close_fees NUMERIC(10, 2)"))
                else:  # SQLite
                    connection.execute(text("ALTER TABLE trades ADD COLUMN close_fees NUMERIC(10, 2)"))
                print("✓ close_fees added")
            else:
                print("✓ close_fees column already exists")
            
            # 3. Add close_premium column
            if not check_column_exists(engine, 'trades', 'close_premium'):
                print("Adding close_premium column to trades table...")
                if is_postgresql(engine):
                    connection.execute(text("ALTER TABLE trades ADD COLUMN close_premium NUMERIC(15, 2)"))
                else:  # SQLite
                    connection.execute(text("ALTER TABLE trades ADD COLUMN close_premium NUMERIC(15, 2)"))
                print("✓ close_premium added")
            else:
                print("✓ close_premium column already exists")
            
            # 4. Add close_method column
            if not check_column_exists(engine, 'trades', 'close_method'):
                print("Adding close_method column to trades table...")
                if is_postgresql(engine):
                    connection.execute(text("ALTER TABLE trades ADD COLUMN close_method VARCHAR(20)"))
                else:  # SQLite
                    connection.execute(text("ALTER TABLE trades ADD COLUMN close_method VARCHAR(20)"))
                print("✓ close_method added")
            else:
                print("✓ close_method column already exists")
            
            trans.commit()
            print(f"\n{'='*80}")
            print(f"✅ Migration completed successfully!")
            print(f"{'='*80}\n")
            
        except OperationalError as e:
            trans.rollback()
            print(f"\n❌ Migration failed: {e.orig}")
            print(f"   Error type: {type(e.orig).__name__}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
        except Exception as e:
            trans.rollback()
            print(f"\n❌ Migration failed: {e}")
            print(f"   Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == '__main__':
    migrate_database()
