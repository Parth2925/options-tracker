#!/usr/bin/env python3
"""
Database migration script to add StockPosition table and update Trade table.

This migration:
1. Creates the stock_positions table
2. Adds stock_position_id and shares_used columns to trades table

Usage:
    python migrate_add_stock_positions.py [--database-url DATABASE_URL]
    
    Or set DATABASE_URL environment variable
"""
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker

# Load environment variables
load_dotenv()

def check_table_exists(engine, table_name):
    """Check if a table exists in the database"""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()

def check_column_exists(engine, table_name, column_name):
    """Check if a column exists in a table"""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns

def migrate_database(database_url):
    """Run the migration"""
    # Create engine
    if database_url.startswith('postgresql://') or database_url.startswith('postgres://'):
        if 'sslmode' not in database_url:
            separator = '&' if '?' in database_url else '?'
            database_url = f"{database_url}{separator}sslmode=require"
    
    engine = create_engine(database_url)
    
    print(f"\n{'='*80}")
    print("Stock Positions Migration")
    print(f"{'='*80}")
    print(f"Database: {database_url[:50]}...\n")
    
    with engine.connect() as conn:
        # Start transaction
        trans = conn.begin()
        
        try:
            # Check if stock_positions table exists
            if check_table_exists(engine, 'stock_positions'):
                print("✓ stock_positions table already exists")
            else:
                print("Creating stock_positions table...")
                # Determine database type
                is_postgres = database_url.startswith('postgresql://') or database_url.startswith('postgres://')
                
                if is_postgres:
                    # PostgreSQL syntax
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
                    conn.execute(text("CREATE INDEX idx_stock_positions_symbol ON stock_positions(symbol)"))
                    conn.execute(text("CREATE INDEX idx_stock_positions_account_id ON stock_positions(account_id)"))
                else:
                    # SQLite syntax
                    conn.execute(text("""
                        CREATE TABLE stock_positions (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
                    conn.execute(text("CREATE INDEX idx_stock_positions_symbol ON stock_positions(symbol)"))
                    conn.execute(text("CREATE INDEX idx_stock_positions_account_id ON stock_positions(account_id)"))
                
                conn.commit()
                print("✓ stock_positions table created")
            
            # Check if trades table exists before trying to modify it
            if not check_table_exists(engine, 'trades'):
                print("⚠ trades table does not exist yet. It will be created when you run db.create_all()")
            else:
                # Check if trades table has stock_position_id column
                if check_column_exists(engine, 'trades', 'stock_position_id'):
                    print("✓ trades.stock_position_id column already exists")
                else:
                    print("Adding stock_position_id column to trades table...")
                    is_postgres = database_url.startswith('postgresql://') or database_url.startswith('postgres://')
                    
                    if is_postgres:
                        conn.execute(text("""
                            ALTER TABLE trades 
                            ADD COLUMN stock_position_id INTEGER,
                            ADD CONSTRAINT fk_trades_stock_position 
                            FOREIGN KEY (stock_position_id) REFERENCES stock_positions(id) ON DELETE SET NULL
                        """))
                    else:
                        # SQLite doesn't support adding foreign key constraints in ALTER TABLE
                        conn.execute(text("ALTER TABLE trades ADD COLUMN stock_position_id INTEGER"))
                        # Note: SQLite foreign key would need to be added via table recreation
                        # For now, we'll rely on application-level integrity
                    
                    conn.commit()
                    print("✓ stock_position_id column added")
                
                # Check if trades table has shares_used column
                if check_column_exists(engine, 'trades', 'shares_used'):
                    print("✓ trades.shares_used column already exists")
                else:
                    print("Adding shares_used column to trades table...")
                    conn.execute(text("ALTER TABLE trades ADD COLUMN shares_used INTEGER"))
                    conn.commit()
                    print("✓ shares_used column added")
            
            # Commit transaction
            trans.commit()
            print(f"\n{'='*80}")
            print("✅ Migration completed successfully!")
            print(f"{'='*80}\n")
            
        except Exception as e:
            trans.rollback()
            print(f"\n❌ Migration failed: {str(e)}")
            print(f"   Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrate database to add StockPosition table')
    parser.add_argument('--database-url', type=str, help='Database URL (defaults to DATABASE_URL env var)')
    
    args = parser.parse_args()
    
    # Get database URL
    database_url = args.database_url or os.getenv('DATABASE_URL')
    
    if not database_url:
        print("❌ Error: DATABASE_URL not provided and not found in environment variables")
        print("\nUsage:")
        print("  python migrate_add_stock_positions.py --database-url 'postgresql://...'")
        print("  OR")
        print("  export DATABASE_URL='postgresql://...'")
        print("  python migrate_add_stock_positions.py")
        sys.exit(1)
    
    migrate_database(database_url)
