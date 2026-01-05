#!/usr/bin/env python3
"""
Script to check database schema and verify all required columns exist.
"""

import os
import sys
from sqlalchemy import create_engine, inspect

# New production database URL
NEW_DB_URL = "postgresql://options_tracker_new_db_user:J7qsnDUWd1Y7yKgOLjFX2qnnimMU60vp@dpg-d5aleduuk2gs73er5c40-a.ohio-postgres.render.com/options_tracker_new_db?sslmode=require"

def get_expected_columns():
    """Return expected columns for each table based on models"""
    return {
        'accounts': [
            'id', 'user_id', 'name', 'account_type', 'initial_balance', 
            'default_fee', 'assignment_fee', 'created_at'
        ],
        'trades': [
            'id', 'account_id', 'symbol', 'trade_type', 'position_type',
            'strike_price', 'expiration_date', 'contract_quantity',
            'trade_price', 'trade_action', 'premium', 'fees',
            'assignment_price', 'trade_date', 'open_date', 'close_date',
            'close_price', 'close_fees', 'close_premium', 'close_method',
            'assignment_fee', 'status', 'parent_trade_id',
            'stock_position_id', 'shares_used', 'notes', 'created_at', 'updated_at'
        ],
        'users': [
            'id', 'email', 'first_name', 'last_name', 'password_hash',
            'email_verified', 'verification_token', 'verification_token_expires',
            'reset_token', 'reset_token_expires', 'created_at', 'updated_at'
        ],
        'stock_positions': [
            'id', 'account_id', 'symbol', 'shares', 'cost_basis_per_share',
            'acquired_date', 'status', 'source_trade_id', 'notes',
            'created_at', 'updated_at'
        ]
    }

def check_database_schema(database_url):
    """Check database schema and report missing columns"""
    print(f"\n{'='*80}")
    print("Database Schema Check")
    print(f"{'='*80}")
    print(f"Database: {database_url[:60]}...\n")
    
    engine = create_engine(database_url, pool_pre_ping=True, connect_args={'connect_timeout': 10})
    inspector = inspect(engine)
    
    expected = get_expected_columns()
    all_good = True
    
    for table_name, expected_cols in expected.items():
        print(f"\n📊 Checking {table_name} table...")
        
        if table_name not in inspector.get_table_names():
            print(f"  ❌ Table '{table_name}' does NOT exist!")
            all_good = False
            continue
        
        existing_cols = [col['name'] for col in inspector.get_columns(table_name)]
        missing_cols = [col for col in expected_cols if col not in existing_cols]
        extra_cols = [col for col in existing_cols if col not in expected_cols]
        
        if missing_cols:
            print(f"  ❌ Missing columns ({len(missing_cols)}): {missing_cols}")
            all_good = False
        else:
            print(f"  ✅ All required columns present ({len(expected_cols)} columns)")
        
        if extra_cols:
            print(f"  ℹ️  Extra columns (not in model): {extra_cols}")
        
        print(f"  Total columns: {len(existing_cols)} (expected: {len(expected_cols)})")
    
    print(f"\n{'='*80}")
    if all_good:
        print("✅ All tables and columns are present - database schema is complete!")
    else:
        print("❌ Some columns are missing - migration needed")
    print(f"{'='*80}\n")
    
    return all_good

if __name__ == '__main__':
    check_database_schema(NEW_DB_URL)

