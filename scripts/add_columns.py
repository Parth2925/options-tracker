#!/usr/bin/env python3
"""Add stock_position_id and shares_used columns to existing trades table"""
from app import app, db
from sqlalchemy import text, inspect

with app.app_context():
    inspector = inspect(db.engine)
    
    # Check if columns already exist
    if 'trades' in inspector.get_table_names():
        cols = [c['name'] for c in inspector.get_columns('trades')]
        
        if 'stock_position_id' not in cols:
            print("Adding stock_position_id column...")
            db.session.execute(text("ALTER TABLE trades ADD COLUMN stock_position_id INTEGER"))
            db.session.commit()
            print("✓ stock_position_id added")
        else:
            print("✓ stock_position_id already exists")
        
        if 'shares_used' not in cols:
            print("Adding shares_used column...")
            db.session.execute(text("ALTER TABLE trades ADD COLUMN shares_used INTEGER"))
            db.session.commit()
            print("✓ shares_used added")
        else:
            print("✓ shares_used already exists")
    else:
        print("⚠ trades table does not exist")
