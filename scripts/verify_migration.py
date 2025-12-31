#!/usr/bin/env python3
"""Verify that migration was successful"""
from app import app, db
from sqlalchemy import inspect

with app.app_context():
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print('Tables:', tables)
    
    if 'trades' in tables:
        cols = [c['name'] for c in inspector.get_columns('trades')]
        print('\nTrades columns:', cols)
        print('Has stock_position_id:', 'stock_position_id' in cols)
        print('Has shares_used:', 'shares_used' in cols)
    
    if 'stock_positions' in tables:
        cols = [c['name'] for c in inspector.get_columns('stock_positions')]
        print('\nStock positions columns:', cols)
