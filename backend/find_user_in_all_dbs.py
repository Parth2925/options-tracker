#!/usr/bin/env python3
"""Script to find test@example.com user in all possible database locations"""
import os
import sys
from sqlalchemy import create_engine, text, inspect
from pathlib import Path

def check_database(db_path, db_name):
    """Check if user exists in a database"""
    try:
        engine = create_engine(db_path)
        with engine.connect() as conn:
            # Check if users table exists
            inspector = inspect(engine)
            if 'users' not in inspector.get_table_names():
                return None
            
            result = conn.execute(text("SELECT id, email, email_verified FROM users WHERE LOWER(email) = LOWER(:email)"), {'email': 'test@example.com'})
            users = result.fetchall()
            if users:
                return users
    except Exception as e:
        print(f"  Error checking {db_name}: {e}")
    return None

def find_user():
    base_dir = Path('/Users/parthsoni/Documents/options-tracker')
    
    # Possible database locations
    db_paths = [
        ('sqlite:///options_tracker.db', 'Default location (options_tracker.db)'),
        ('sqlite:///instance/options_tracker.db', 'Instance directory'),
        (f'sqlite:///{base_dir}/backend/options_tracker.db', 'Backend directory'),
        (f'sqlite:///{base_dir}/backend/instance/options_tracker.db', 'Backend instance'),
        (f'sqlite:///{base_dir}/instance/options_tracker.db', 'Root instance'),
    ]
    
    # Also check environment variable
    from dotenv import load_dotenv
    load_dotenv()
    env_db = os.getenv('DATABASE_URL')
    if env_db and env_db.startswith('sqlite'):
        db_paths.append((env_db, 'Environment variable DATABASE_URL'))
    
    print("Searching for test@example.com in all database locations...\n")
    
    found_any = False
    for db_path, db_name in db_paths:
        print(f"Checking: {db_name}")
        print(f"  Path: {db_path}")
        users = check_database(db_path, db_name)
        if users:
            found_any = True
            print(f"  ✓ FOUND {len(users)} user(s):")
            for user in users:
                print(f"    ID: {user[0]}, Email: '{user[1]}', Verified: {user[2]}")
        else:
            print(f"  ✗ Not found or table doesn't exist")
        print()
    
    if not found_any:
        print("User not found in any database location!")
    else:
        print("\nTo use the correct database, set DATABASE_URL in .env file to the path where the user exists.")

if __name__ == '__main__':
    find_user()

