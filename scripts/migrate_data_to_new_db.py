#!/usr/bin/env python3
"""
Data migration script to copy all data from old database to new database.

This script:
1. Reads all data from the old production database
2. Writes it to the new database (with v1.4.0 schema)
3. Verifies data integrity
4. Preserves all relationships (users → accounts → trades → etc.)

Usage:
    python migrate_data_to_new_db.py --old-db-url OLD_URL --new-db-url NEW_URL

Or set environment variables:
    OLD_DATABASE_URL=postgresql://...
    NEW_DATABASE_URL=postgresql://...
    python migrate_data_to_new_db.py
"""
import os
import sys
import time
from datetime import datetime
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def log(message, level='INFO'):
    """Log with timestamp"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_msg = f"[{timestamp}] [{level}] {message}"
    print(log_msg)
    sys.stdout.flush()

def create_engine_safe(database_url, label):
    """Create engine with proper settings"""
    log(f"Connecting to {label}...")
    
    if database_url.startswith('postgresql://') or database_url.startswith('postgres://'):
        if 'sslmode' not in database_url:
            separator = '&' if '?' in database_url else '?'
            database_url = f"{database_url}{separator}sslmode=require"
        
        engine = create_engine(
            database_url,
            pool_pre_ping=True,
            pool_recycle=300,
            connect_args={
                'connect_timeout': 15,
                'options': '-c statement_timeout=30000'  # 30 second timeout
            }
        )
    else:
        from sqlalchemy.pool import NullPool
        engine = create_engine(
            database_url,
            poolclass=NullPool,
            connect_args={'check_same_thread': False}
        )
    
    # Test connection
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).scalar()
            log(f"✅ {label} connection successful")
    except Exception as e:
        log(f"❌ {label} connection failed: {e}", 'ERROR')
        raise
    
    return engine

def get_table_count(engine, table_name):
    """Get row count for a table"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
            return result
    except Exception as e:
        log(f"   Warning: Could not count {table_name}: {e}")
        return 0

def migrate_table_data(old_engine, new_engine, table_name, order_by=None, skip_columns=None):
    """Migrate data from one table to another
    
    Args:
        old_engine: Source database engine
        new_engine: Target database engine
        table_name: Table to migrate
        order_by: Column to order by (for foreign key dependencies)
        skip_columns: List of columns to skip (e.g., new v1.4.0 columns not in old DB)
    """
    log(f"Migrating {table_name}...")
    
    start_time = time.time()
    
    # Get count from old database
    old_count = get_table_count(old_engine, table_name)
    log(f"   Old DB: {old_count} rows")
    
    if old_count == 0:
        log(f"   ⏭️  Skipping {table_name} (empty)")
        return 0
    
    # Get count from new database
    new_count = get_table_count(new_engine, table_name)
    log(f"   New DB: {new_count} rows (before migration)")
    
    if new_count > 0:
        log(f"   ⚠️  Warning: {table_name} already has data in new DB")
        log(f"   This will add duplicate data. Clearing existing data first...")
        # Clear existing data to avoid duplicates
        with new_engine.connect() as conn:
            trans = conn.begin()
            try:
                conn.execute(text(f"TRUNCATE TABLE {table_name} CASCADE"))
                trans.commit()
                log(f"   ✅ Cleared existing data from {table_name}")
            except Exception as e:
                trans.rollback()
                log(f"   ⚠️  Could not clear {table_name}: {e}", 'WARNING')
                log(f"   Will attempt to migrate anyway (may cause duplicates)")
    
    # Get column lists from both databases
    old_inspector = inspect(old_engine)
    new_inspector = inspect(new_engine)
    
    old_columns = [c['name'] for c in old_inspector.get_columns(table_name)]
    new_columns = [c['name'] for c in new_inspector.get_columns(table_name)]
    
    # Determine which columns to migrate
    # Only migrate columns that exist in both databases, or skip specified columns
    columns_to_migrate = []
    for col in old_columns:
        if col in new_columns:
            if skip_columns and col in skip_columns:
                log(f"   ⏭️  Skipping column {col} (v1.4.0 new column)")
                continue
            columns_to_migrate.append(col)
        else:
            log(f"   ⏭️  Skipping column {col} (not in new schema)")
    
    if not columns_to_migrate:
        log(f"   ⚠️  No columns to migrate for {table_name}")
        return 0
    
    log(f"   Migrating columns: {', '.join(columns_to_migrate)}")
    
    # Read data from old database
    try:
        with old_engine.connect() as old_conn:
            # For trades table, we need to handle parent_trade_id foreign key constraint
            # Insert parents first, then children
            if table_name == 'trades' and 'parent_trade_id' in columns_to_migrate:
                # First, get all trades
                col_list = ', '.join(columns_to_migrate)
                query = f"SELECT {col_list} FROM {table_name}"
                result = old_conn.execute(text(query))
                all_rows = result.fetchall()
                column_names = list(result.keys())
                
                # Separate into parents (no parent_trade_id) and children (has parent_trade_id)
                parent_rows = []
                child_rows = []
                parent_trade_id_idx = column_names.index('parent_trade_id') if 'parent_trade_id' in column_names else -1
                
                for row in all_rows:
                    if hasattr(row, '_asdict'):
                        row_dict = row._asdict()
                    elif hasattr(row, '_mapping'):
                        row_dict = dict(row._mapping)
                    else:
                        row_dict = {col: row[idx] for idx, col in enumerate(column_names)}
                    
                    parent_id = row_dict.get('parent_trade_id') if parent_trade_id_idx >= 0 else None
                    if parent_id is None:
                        parent_rows.append(row)
                    else:
                        child_rows.append((parent_id, row))
                
                # Sort child rows by parent_trade_id to ensure parents are inserted before children
                # We'll need to track which parent IDs have been inserted
                rows_to_insert = parent_rows + [r[1] for r in child_rows]
                log(f"   Read {len(rows_to_insert)} rows from old database ({len(parent_rows)} parents, {len(child_rows)} children)")
            else:
                # For other tables, use normal ordering
                order_clause = f"ORDER BY {order_by}" if order_by else ""
                col_list = ', '.join(columns_to_migrate)
                query = f"SELECT {col_list} FROM {table_name} {order_clause}"
                result = old_conn.execute(text(query))
                rows_to_insert = result.fetchall()
                column_names = list(result.keys())
            
            log(f"   Read {len(rows_to_insert)} rows from old database")
            
            if len(rows_to_insert) == 0:
                log(f"   ⏭️  No data to migrate for {table_name}")
                return 0
            
            # Write to new database
            with new_engine.connect() as new_conn:
                trans = new_conn.begin()
                try:
                    inserted = 0
                    inserted_ids = set()  # Track inserted trade IDs for foreign key validation
                    skipped_rows = []  # Track rows that were skipped due to missing parents
                    
                    # First pass: Insert all rows
                    for row in rows_to_insert:
                        # Convert row (tuple or Row) to dictionary
                        # Row objects can be accessed by column name, tuples by index
                        if hasattr(row, '_asdict'):
                            # SQLAlchemy Row object
                            row_dict = row._asdict()
                        elif hasattr(row, '_mapping'):
                            # SQLAlchemy Row with mapping access
                            row_dict = dict(row._mapping)
                        else:
                            # Plain tuple - create dict from column names and values
                            row_dict = {col: row[idx] for idx, col in enumerate(column_names)}
                        
                        # Build INSERT statement with only columns that exist in both
                        col_names = ', '.join(columns_to_migrate)
                        placeholders = ', '.join([':' + col for col in columns_to_migrate])
                        values = {col: row_dict[col] for col in columns_to_migrate}
                        
                        # For trades table, validate parent_trade_id exists before inserting
                        if table_name == 'trades' and 'parent_trade_id' in values and values['parent_trade_id']:
                            parent_id = values['parent_trade_id']
                            if parent_id not in inserted_ids:
                                # Parent not inserted yet - check if parent exists in old database
                                with old_engine.connect() as check_conn:
                                    parent_check = check_conn.execute(
                                        text("SELECT id FROM trades WHERE id = :parent_id"),
                                        {'parent_id': parent_id}
                                    ).fetchone()
                                
                                if not parent_check:
                                    # Parent doesn't exist in old DB - data integrity issue, set to NULL
                                    log(f"   ⚠️  Warning: Parent trade {parent_id} does not exist in old database, setting parent_trade_id to NULL for trade {values.get('id', 'unknown')}", 'WARNING')
                                    values['parent_trade_id'] = None
                                else:
                                    # Parent exists but not inserted yet - skip for now, retry in second pass
                                    skipped_rows.append((row, values))
                                    continue
                        
                        # Handle None values and special types
                        for key, value in values.items():
                            if value is None:
                                values[key] = None
                            elif isinstance(value, (datetime,)):
                                values[key] = value
                        
                        insert_sql = f"INSERT INTO {table_name} ({col_names}) VALUES ({placeholders})"
                        new_conn.execute(text(insert_sql), values)
                        inserted += 1
                        
                        # Track inserted trade ID for foreign key validation
                        if table_name == 'trades' and 'id' in values:
                            inserted_ids.add(values['id'])
                    
                    # Second pass: Retry skipped rows (their parents should now be inserted)
                    if skipped_rows:
                        log(f"   Retrying {len(skipped_rows)} skipped rows...")
                        for row, values in skipped_rows:
                            parent_id = values.get('parent_trade_id')
                            if parent_id and parent_id in inserted_ids:
                                # Parent is now inserted, try again
                                # Handle None values and special types
                                for key, value in values.items():
                                    if value is None:
                                        values[key] = None
                                    elif isinstance(value, (datetime,)):
                                        values[key] = value
                                
                                insert_sql = f"INSERT INTO {table_name} ({col_names}) VALUES ({placeholders})"
                                new_conn.execute(text(insert_sql), values)
                                inserted += 1
                                
                                # Track inserted trade ID
                                if table_name == 'trades' and 'id' in values:
                                    inserted_ids.add(values['id'])
                            else:
                                # Parent still not found - set to NULL
                                log(f"   ⚠️  Warning: Parent trade {parent_id} still not found, setting parent_trade_id to NULL for trade {values.get('id', 'unknown')}", 'WARNING')
                                values['parent_trade_id'] = None
                                
                                # Handle None values and special types
                                for key, value in values.items():
                                    if value is None:
                                        values[key] = None
                                    elif isinstance(value, (datetime,)):
                                        values[key] = value
                                
                                insert_sql = f"INSERT INTO {table_name} ({col_names}) VALUES ({placeholders})"
                                new_conn.execute(text(insert_sql), values)
                                inserted += 1
                                
                                # Track inserted trade ID
                                if table_name == 'trades' and 'id' in values:
                                    inserted_ids.add(values['id'])
                    
                    trans.commit()
                    elapsed = time.time() - start_time
                    log(f"   ✅ Migrated {inserted} rows in {elapsed:.2f} seconds")
                    
                    # Verify
                    final_count = get_table_count(new_engine, table_name)
                    if final_count == old_count:
                        log(f"   ✅ Verification passed: {final_count} rows")
                    else:
                        log(f"   ⚠️  Verification warning: Expected {old_count}, got {final_count}", 'WARNING')
                    
                    return inserted
                    
                except Exception as e:
                    trans.rollback()
                    log(f"   ❌ Error migrating {table_name}: {e}", 'ERROR')
                    raise
                    
    except Exception as e:
        log(f"   ❌ Error reading from old database: {e}", 'ERROR')
        raise

def migrate_all_data(old_db_url, new_db_url):
    """Migrate all data from old to new database"""
    log("=" * 80)
    log("Data Migration: Old Database → New Database")
    log("=" * 80)
    
    # Create engines
    old_engine = create_engine_safe(old_db_url, "Old Database")
    new_engine = create_engine_safe(new_db_url, "New Database")
    
    # Verify schemas exist
    log("\nVerifying database schemas...")
    old_inspector = inspect(old_engine)
    new_inspector = inspect(new_engine)
    
    old_tables = old_inspector.get_table_names()
    new_tables = new_inspector.get_table_names()
    
    log(f"Old DB tables: {', '.join(old_tables)}")
    log(f"New DB tables: {', '.join(new_tables)}")
    
    # Check required tables exist
    required_tables = ['users', 'accounts', 'trades']
    for table in required_tables:
        if table not in old_tables:
            log(f"❌ Required table '{table}' not found in old database", 'ERROR')
            return False
        if table not in new_tables:
            log(f"❌ Required table '{table}' not found in new database", 'ERROR')
            log(f"   Please run schema migrations first!", 'ERROR')
            return False
    
    log("✅ All required tables exist")
    
    # Migration order (respecting foreign key constraints)
    # 1. Users (no dependencies)
    # 2. Accounts (depends on users)
    # 3. Trades (depends on accounts) - Note: old format trades will work with v1.4.0
    # 4. Deposits/Withdrawals (depends on accounts)
    # 5. Stock Positions (depends on accounts, trades) - if exists
    
    migration_order = [
        ('users', 'id', None),  # (table, order_by, skip_columns)
        ('accounts', 'id', ['default_fee']),  # Skip default_fee (will be NULL/0, which is fine)
        ('trades', 'id', ['close_price', 'close_fees', 'close_premium', 'close_method', 'stock_position_id', 'shares_used']),  # Skip v1.4.0 columns
        ('deposits', 'id', None),
        ('withdrawals', 'id', None),
    ]
    
    # Check if stock_positions exists in new DB (v1.4.0 feature)
    # Note: Old DB won't have this, so we skip it
    # Stock positions will be created later when needed
    
    log("\n" + "=" * 80)
    log("Starting Data Migration")
    log("=" * 80)
    
    total_migrated = 0
    for migration_item in migration_order:
        # Handle both 2-tuple and 3-tuple formats
        if isinstance(migration_item, tuple) and len(migration_item) == 3:
            table_name, order_by, skip_columns = migration_item
        elif isinstance(migration_item, tuple) and len(migration_item) == 2:
            table_name, order_by = migration_item
            skip_columns = None
        else:
            log(f"❌ Invalid migration item format: {migration_item}", 'ERROR')
            continue
        
        if table_name not in old_tables:
            log(f"⏭️  Skipping {table_name} (not in old database)")
            continue
        
        try:
            count = migrate_table_data(old_engine, new_engine, table_name, order_by, skip_columns)
            total_migrated += count
            log("")  # Blank line for readability
        except Exception as e:
            log(f"❌ Migration failed for {table_name}: {e}", 'ERROR')
            log("Migration aborted. Please check errors above.", 'ERROR')
            return False
    
    # Final verification
    log("\n" + "=" * 80)
    log("Final Verification")
    log("=" * 80)
    
    all_match = True
    for migration_item in migration_order:
        # Handle both 2-tuple and 3-tuple formats
        if isinstance(migration_item, tuple) and len(migration_item) >= 2:
            table_name = migration_item[0]
        else:
            continue
        
        if table_name not in old_tables:
            continue
        
        old_count = get_table_count(old_engine, table_name)
        new_count = get_table_count(new_engine, table_name)
        
        if old_count == new_count:
            log(f"✅ {table_name}: {old_count} rows (match)")
        else:
            log(f"❌ {table_name}: Old={old_count}, New={new_count} (MISMATCH)", 'ERROR')
            all_match = False
    
    if all_match:
        log("\n✅ All data migrated successfully!")
        log(f"Total rows migrated: {total_migrated}")
        return True
    else:
        log("\n❌ Data verification failed. Please review mismatches above.", 'ERROR')
        return False

def main():
    """Main entry point"""
    # Get database URLs
    old_db_url = os.getenv('OLD_DATABASE_URL')
    new_db_url = os.getenv('NEW_DATABASE_URL')
    
    # Check command line arguments
    if '--old-db-url' in sys.argv:
        idx = sys.argv.index('--old-db-url')
        if idx + 1 < len(sys.argv):
            old_db_url = sys.argv[idx + 1]
    
    if '--new-db-url' in sys.argv:
        idx = sys.argv.index('--new-db-url')
        if idx + 1 < len(sys.argv):
            new_db_url = sys.argv[idx + 1]
    
    if not old_db_url:
        log("❌ OLD_DATABASE_URL not set", 'ERROR')
        log("Usage: python migrate_data_to_new_db.py --old-db-url OLD_URL --new-db-url NEW_URL")
        log("Or set OLD_DATABASE_URL and NEW_DATABASE_URL environment variables")
        sys.exit(1)
    
    if not new_db_url:
        log("❌ NEW_DATABASE_URL not set", 'ERROR')
        log("Usage: python migrate_data_to_new_db.py --old-db-url OLD_URL --new-db-url NEW_URL")
        log("Or set OLD_DATABASE_URL and NEW_DATABASE_URL environment variables")
        sys.exit(1)
    
    # Confirm before proceeding
    log("\n⚠️  WARNING: This will copy all data from old database to new database.")
    log(f"   Old DB: {old_db_url[:50]}...")
    log(f"   New DB: {new_db_url[:50]}...")
    response = input("\nContinue? (yes/no): ")
    
    if response.lower() != 'yes':
        log("Migration cancelled.")
        sys.exit(0)
    
    # Run migration
    try:
        success = migrate_all_data(old_db_url, new_db_url)
        if success:
            log("\n✅ Migration completed successfully!")
            sys.exit(0)
        else:
            log("\n❌ Migration completed with errors. Please review above.")
            sys.exit(1)
    except Exception as e:
        log(f"\n❌ Migration failed: {e}", 'ERROR')
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()

