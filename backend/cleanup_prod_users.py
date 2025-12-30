#!/usr/bin/env python3
"""
Clean up test users from production database
Usage:
    python cleanup_prod_users.py --database-url DATABASE_URL --user-ids "1,2,3" --execute
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

def delete_users_by_ids(database_url, user_ids, execute=False, skip_confirm=False):
    """Delete multiple users by their IDs"""
    app = setup_app_and_db(database_url)
    
    with app.app_context():
        try:
            users = User.query.filter(User.id.in_(user_ids)).all()
            
            if not users:
                print(f"No users found with IDs: {user_ids}")
                return []
            
            # Check if any requested IDs were not found
            found_ids = {user.id for user in users}
            missing_ids = set(user_ids) - found_ids
            if missing_ids:
                print(f"Warning: User IDs not found: {missing_ids}")
            
            print(f"\n{'='*80}")
            print(f"Found {len(users)} users to delete:")
            print(f"{'='*80}")
            for user in users:
                created = user.created_at.strftime("%Y-%m-%d %H:%M:%S") if user.created_at else "N/A"
                verified = "Yes" if user.email_verified else "No"
                account_count = len(user.accounts)
                print(f"  - ID {user.id}: {user.email}")
                print(f"    Name: {user.first_name} {user.last_name}")
                print(f"    Verified: {verified} | Accounts: {account_count} | Created: {created}")
                print()
            
            if not execute:
                print(f"{'='*80}")
                print("[DRY RUN] Would delete these users. Add --execute to actually delete.")
                print(f"{'='*80}\n")
                return users
            
            # Actually delete
            if not skip_confirm:
                confirm = input(f"\n⚠️  Are you sure you want to delete {len(users)} users? This cannot be undone! (yes/no): ")
                if confirm.lower() != 'yes':
                    print("Cancelled.")
                    return []
            
            deleted_count = 0
            for user in users:
                try:
                    db.session.delete(user)
                    deleted_count += 1
                    print(f"  ✓ Deleted: ID {user.id} - {user.email}")
                except Exception as e:
                    print(f"  ✗ Error deleting ID {user.id} ({user.email}): {str(e)}")
                    db.session.rollback()
            
            db.session.commit()
            print(f"\n{'='*80}")
            print(f"✅ Successfully deleted {deleted_count} out of {len(users)} users.")
            print(f"{'='*80}\n")
            
            return users
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            print(f"   Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Clean up test users from production database')
    parser.add_argument('--database-url', type=str, required=True, help='Database URL (required)')
    parser.add_argument('--user-ids', type=str, required=True, help='Comma-separated user IDs (e.g., "1,2,3,4")')
    parser.add_argument('--execute', action='store_true', help='Actually delete (without this, it\'s a dry run)')
    parser.add_argument('--yes', action='store_true', help='Skip confirmation prompt (use with caution)')
    
    args = parser.parse_args()
    
    # Parse user IDs
    try:
        user_ids = [int(id.strip()) for id in args.user_ids.split(',')]
    except ValueError:
        print("❌ Error: --user-ids must be comma-separated numbers (e.g., '1,2,3,4')")
        sys.exit(1)
    
    # Mask URL for display
    print(f"\n📊 Connecting to database: {args.database_url[:50]}...")
    
    delete_users_by_ids(args.database_url, user_ids, execute=args.execute, skip_confirm=args.yes)
