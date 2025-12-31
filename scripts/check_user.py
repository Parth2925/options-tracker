#!/usr/bin/env python3
"""Script to check if test@example.com user exists in database"""
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load environment variables
load_dotenv()

def check_user():
    database_url = os.getenv('DATABASE_URL', 'sqlite:///options_tracker.db')
    
    # Handle PostgreSQL SSL
    if database_url.startswith('postgresql://') or database_url.startswith('postgres://'):
        if 'sslmode' not in database_url:
            separator = '&' if '?' in database_url else '?'
            database_url = f"{database_url}{separator}sslmode=require"
    
    engine = create_engine(database_url)
    
    with engine.connect() as conn:
        # Check all users
        result = conn.execute(text("SELECT id, email, email_verified FROM users WHERE email LIKE '%test@example.com%' OR email LIKE '%TEST@EXAMPLE.COM%'"))
        users = result.fetchall()
        
        print(f"\nFound {len(users)} user(s) with email containing 'test@example.com':")
        for user in users:
            print(f"  ID: {user[0]}, Email: '{user[1]}', Verified: {user[2]}")
        
        # Check all users
        result = conn.execute(text("SELECT id, email, email_verified FROM users"))
        all_users = result.fetchall()
        
        print(f"\nAll users in database ({len(all_users)} total):")
        for user in all_users:
            print(f"  ID: {user[0]}, Email: '{user[1]}', Verified: {user[2]}")

if __name__ == '__main__':
    check_user()

