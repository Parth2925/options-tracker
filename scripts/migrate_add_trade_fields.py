#!/usr/bin/env python3
"""
Migration script to add trade_price and trade_action columns to trades table
Run this once to update your existing database schema.
"""
import sqlite3
import os

# Path to the database
db_path = 'options_tracker.db'

if not os.path.exists(db_path):
    print(f"Database file {db_path} not found. Make sure you're running this from the backend directory.")
    exit(1)

print(f"Connecting to database: {db_path}")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Check if columns already exist
    cursor.execute("PRAGMA table_info(trades)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'trade_price' in columns and 'trade_action' in columns:
        print("Columns trade_price and trade_action already exist. Migration not needed.")
        conn.close()
        exit(0)
    
    print("Adding trade_price column...")
    cursor.execute("ALTER TABLE trades ADD COLUMN trade_price NUMERIC(10, 2)")
    
    print("Adding trade_action column...")
    cursor.execute("ALTER TABLE trades ADD COLUMN trade_action VARCHAR(30)")
    
    conn.commit()
    print("✓ Migration completed successfully!")
    print("  - Added trade_price column")
    print("  - Added trade_action column")
    
except sqlite3.Error as e:
    print(f"✗ Error during migration: {e}")
    conn.rollback()
    exit(1)
finally:
    conn.close()

