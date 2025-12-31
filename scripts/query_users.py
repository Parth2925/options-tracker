#!/usr/bin/env python3
"""
Query production database to get user information
Usage:
    python query_users.py [--database-url DATABASE_URL]
    
    Or set DATABASE_URL environment variable
"""
import os
import sys
from dotenv import load_dotenv
from models import User, db
from flask import Flask

# Load environment variables
load_dotenv()

def setup_app_and_db(database_url):
    """Setup Flask app and database connection"""
    app = Flask(__name__)
    
    # Configure database URL
    if database_url.startswith('postgresql://') or database_url.startswith('postgres://'):
        if 'sslmode' not in database_url:
            separator = '&' if '?' in database_url else '?'
            database_url = f"{database_url}{separator}sslmode=require"
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_size': 5,
        'max_overflow': 10,
    } if database_url.startswith('postgresql://') or database_url.startswith('postgres://') else {}
    
    db.init_app(app)
    return app

def query_users(database_url):
    """Query and display user information"""
    app = setup_app_and_db(database_url)
    
    with app.app_context():
        try:
            # Query all users
            users = User.query.order_by(User.created_at).all()
            
            print(f"\n{'='*80}")
            print(f"USER QUERY RESULTS")
            print(f"{'='*80}")
            print(f"\nTotal Users: {len(users)}\n")
            
            if users:
                print(f"{'ID':<5} {'Email':<35} {'Name':<25} {'Verified':<10} {'Created At':<20}")
                print("-" * 95)
                
                for user in users:
                    full_name = f"{user.first_name} {user.last_name}"
                    verified = "Yes" if user.email_verified else "No"
                    created = user.created_at.strftime("%Y-%m-%d %H:%M:%S") if user.created_at else "N/A"
                    
                    print(f"{user.id:<5} {user.email:<35} {full_name:<25} {verified:<10} {created:<20}")
                
                print("\n" + "-" * 95)
                print("\nDetailed User Information:\n")
                
                for user in users:
                    print(f"User ID: {user.id}")
                    print(f"  Email: {user.email}")
                    print(f"  First Name: {user.first_name}")
                    print(f"  Last Name: {user.last_name}")
                    print(f"  Email Verified: {user.email_verified}")
                    print(f"  Created At: {user.created_at}")
                    print(f"  Updated At: {user.updated_at}")
                    
                    # Count accounts for this user
                    account_count = len(user.accounts)
                    print(f"  Accounts: {account_count}")
                    
                    print()
            else:
                print("No users found in the database.")
            
            print(f"{'='*80}\n")
            
        except Exception as e:
            print(f"\n❌ Error querying users: {str(e)}")
            print(f"   Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Query production database for user information')
    parser.add_argument('--database-url', type=str, help='Database URL (defaults to DATABASE_URL env var)')
    
    args = parser.parse_args()
    
    # Get database URL
    database_url = args.database_url or os.getenv('DATABASE_URL')
    
    if not database_url:
        print("❌ Error: DATABASE_URL not provided and not found in environment variables")
        print("\nUsage:")
        print("  python query_users.py --database-url 'postgresql://...'")
        print("  OR")
        print("  export DATABASE_URL='postgresql://...'")
        print("  python query_users.py")
        sys.exit(1)
    
    # Mask URL for display (show only first 50 chars)
    print(f"\n📊 Connecting to database: {database_url[:50]}...")
    
    query_users(database_url)
