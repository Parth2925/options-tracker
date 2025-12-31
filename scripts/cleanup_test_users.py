#!/usr/bin/env python3
"""
Script to clean up test users from the database.
This will delete users and all their related data (accounts, trades, deposits).

Usage:
    python cleanup_test_users.py
"""

import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User

def list_users():
    """List all users in the database"""
    with app.app_context():
        users = User.query.order_by(User.created_at.desc()).all()
        print(f"\n{'='*80}")
        print(f"Found {len(users)} users in database:")
        print(f"{'='*80}")
        print(f"{'ID':<5} {'Email':<40} {'Name':<30} {'Verified':<10} {'Created At'}")
        print("-" * 80)
        for user in users:
            verified = "Yes" if user.email_verified else "No"
            created = user.created_at.strftime("%Y-%m-%d %H:%M") if user.created_at else "N/A"
            print(f"{user.id:<5} {user.email:<40} {user.first_name} {user.last_name:<20} {verified:<10} {created}")
        print(f"{'='*80}\n")
        return users

def delete_users_by_email_pattern(pattern, dry_run=True):
    """Delete users whose email contains the pattern"""
    with app.app_context():
        users = User.query.filter(User.email.contains(pattern)).all()
        if not users:
            print(f"No users found with email containing '{pattern}'")
            return []
        
        print(f"\nFound {len(users)} users matching pattern '{pattern}':")
        for user in users:
            print(f"  - ID {user.id}: {user.email} ({user.first_name} {user.last_name})")
        
        if dry_run:
            print("\n[DRY RUN] Would delete these users. Run with --execute to actually delete.")
        else:
            confirm = input(f"\nAre you sure you want to delete {len(users)} users? (yes/no): ")
            if confirm.lower() != 'yes':
                print("Cancelled.")
                return []
            
            deleted_count = 0
            for user in users:
                try:
                    # Cascade delete will handle accounts, trades, deposits
                    db.session.delete(user)
                    deleted_count += 1
                    print(f"  Deleted: {user.email}")
                except Exception as e:
                    print(f"  Error deleting {user.email}: {str(e)}")
            
            db.session.commit()
            print(f"\nSuccessfully deleted {deleted_count} users.")
        
        return users

def delete_users_by_date_range(days_ago=None, before_date=None, dry_run=True):
    """Delete users created before a certain date or within a date range"""
    with app.app_context():
        query = User.query
        
        if days_ago:
            cutoff_date = datetime.utcnow() - timedelta(days=days_ago)
            query = query.filter(User.created_at >= cutoff_date)
            print(f"Finding users created in the last {days_ago} days...")
        elif before_date:
            query = query.filter(User.created_at < before_date)
            print(f"Finding users created before {before_date}...")
        else:
            print("No date filter specified")
            return []
        
        users = query.all()
        if not users:
            print(f"No users found matching date criteria")
            return []
        
        print(f"\nFound {len(users)} users:")
        for user in users:
            created = user.created_at.strftime("%Y-%m-%d %H:%M") if user.created_at else "N/A"
            print(f"  - ID {user.id}: {user.email} (created: {created})")
        
        if dry_run:
            print("\n[DRY RUN] Would delete these users. Run with --execute to actually delete.")
        else:
            confirm = input(f"\nAre you sure you want to delete {len(users)} users? (yes/no): ")
            if confirm.lower() != 'yes':
                print("Cancelled.")
                return []
            
            deleted_count = 0
            for user in users:
                try:
                    db.session.delete(user)
                    deleted_count += 1
                    print(f"  Deleted: {user.email}")
                except Exception as e:
                    print(f"  Error deleting {user.email}: {str(e)}")
            
            db.session.commit()
            print(f"\nSuccessfully deleted {deleted_count} users.")
        
        return users

def delete_unverified_users(dry_run=True):
    """Delete users with unverified email addresses"""
    with app.app_context():
        users = User.query.filter_by(email_verified=False).all()
        if not users:
            print("No unverified users found")
            return []
        
        print(f"\nFound {len(users)} unverified users:")
        for user in users:
            created = user.created_at.strftime("%Y-%m-%d %H:%M") if user.created_at else "N/A"
            print(f"  - ID {user.id}: {user.email} (created: {created})")
        
        if dry_run:
            print("\n[DRY RUN] Would delete these users. Run with --execute to actually delete.")
        else:
            confirm = input(f"\nAre you sure you want to delete {len(users)} unverified users? (yes/no): ")
            if confirm.lower() != 'yes':
                print("Cancelled.")
                return []
            
            deleted_count = 0
            for user in users:
                try:
                    db.session.delete(user)
                    deleted_count += 1
                    print(f"  Deleted: {user.email}")
                except Exception as e:
                    print(f"  Error deleting {user.email}: {str(e)}")
            
            db.session.commit()
            print(f"\nSuccessfully deleted {deleted_count} users.")
        
        return users

def delete_user_by_id(user_id, dry_run=True):
    """Delete a specific user by ID"""
    with app.app_context():
        user = User.query.get(user_id)
        if not user:
            print(f"User with ID {user_id} not found")
            return None
        
        print(f"\nUser found:")
        print(f"  ID: {user.id}")
        print(f"  Email: {user.email}")
        print(f"  Name: {user.first_name} {user.last_name}")
        print(f"  Verified: {user.email_verified}")
        print(f"  Created: {user.created_at}")
        
        if dry_run:
            print("\n[DRY RUN] Would delete this user. Run with --execute to actually delete.")
        else:
            confirm = input(f"\nAre you sure you want to delete this user? (yes/no): ")
            if confirm.lower() != 'yes':
                print("Cancelled.")
                return None
            
            try:
                db.session.delete(user)
                db.session.commit()
                print(f"\nSuccessfully deleted user {user.email}")
            except Exception as e:
                print(f"\nError deleting user: {str(e)}")
                db.session.rollback()
        
        return user

def delete_users_by_ids(user_ids, dry_run=True):
    """Delete multiple users by their IDs"""
    with app.app_context():
        users = User.query.filter(User.id.in_(user_ids)).all()
        
        if not users:
            print(f"No users found with IDs: {user_ids}")
            return []
        
        # Check if any requested IDs were not found
        found_ids = {user.id for user in users}
        missing_ids = set(user_ids) - found_ids
        if missing_ids:
            print(f"Warning: User IDs not found: {missing_ids}")
        
        print(f"\nFound {len(users)} users to delete:")
        for user in users:
            created = user.created_at.strftime("%Y-%m-%d %H:%M") if user.created_at else "N/A"
            verified = "Yes" if user.email_verified else "No"
            print(f"  - ID {user.id}: {user.email} ({user.first_name} {user.last_name}) - Verified: {verified} - Created: {created}")
        
        if dry_run:
            print(f"\n[DRY RUN] Would delete {len(users)} users. Run with --execute to actually delete.")
        else:
            confirm = input(f"\nAre you sure you want to delete {len(users)} users? (yes/no): ")
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
            
            db.session.commit()
            print(f"\nSuccessfully deleted {deleted_count} out of {len(users)} users.")
        
        return users

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Clean up test users from the database')
    parser.add_argument('--list', action='store_true', help='List all users')
    parser.add_argument('--email-pattern', type=str, help='Delete users with email containing this pattern (e.g., "test", "fake")')
    parser.add_argument('--unverified', action='store_true', help='Delete all unverified users')
    parser.add_argument('--days-ago', type=int, help='Delete users created in the last N days')
    parser.add_argument('--before-date', type=str, help='Delete users created before this date (YYYY-MM-DD)')
    parser.add_argument('--user-id', type=int, help='Delete a specific user by ID')
    parser.add_argument('--user-ids', type=str, help='Delete multiple users by IDs (comma-separated, e.g., "1,3,4,5")')
    parser.add_argument('--execute', action='store_true', help='Actually delete (without this flag, it\'s a dry run)')
    parser.add_argument('--database-url', type=str, help='Override DATABASE_URL (for production: paste from Render)')
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Override DATABASE_URL if provided via command line
    if args.database_url:
        os.environ['DATABASE_URL'] = args.database_url
        print(f"Using provided DATABASE_URL: {args.database_url[:50]}...")
    
    # Show which database we're connecting to
    database_url = os.getenv('DATABASE_URL', 'sqlite:///options_tracker.db')
    if database_url.startswith('postgresql://') or database_url.startswith('postgres://'):
        print(f"\n⚠️  Connecting to PRODUCTION PostgreSQL database!")
        print(f"   {database_url[:50]}...")
    else:
        print(f"\n📁 Connecting to local database: {database_url}")
    
    # If no arguments, show menu
    if len(sys.argv) == 1:
        print("\n" + "="*80)
        print("Database User Cleanup Tool")
        print("="*80)
        print("\nAvailable options:")
        print("  1. List all users: --list")
        print("  2. Delete by email pattern: --email-pattern 'test' --execute")
        print("  3. Delete unverified users: --unverified --execute")
        print("  4. Delete users created in last N days: --days-ago 7 --execute")
        print("  5. Delete users created before date: --before-date '2025-01-01' --execute")
        print("  6. Delete specific user: --user-id 5 --execute")
        print("  7. Delete multiple users: --user-ids '1,3,4,5' --execute")
        print("\nNote: Add --execute to actually delete. Without it, it's a dry run.")
        print("\nExamples:")
        print("  python cleanup_test_users.py --list")
        print("  python cleanup_test_users.py --email-pattern 'dev.nondon.store' --execute")
        print("  python cleanup_test_users.py --unverified --execute")
        print("  python cleanup_test_users.py --user-ids '1,3,4,5' --execute")
        print("="*80 + "\n")
        return
    
    if args.list:
        list_users()
    
    if args.email_pattern:
        delete_users_by_email_pattern(args.email_pattern, dry_run=not args.execute)
    
    if args.unverified:
        delete_unverified_users(dry_run=not args.execute)
    
    if args.days_ago:
        delete_users_by_date_range(days_ago=args.days_ago, dry_run=not args.execute)
    
    if args.before_date:
        try:
            before_date = datetime.strptime(args.before_date, '%Y-%m-%d')
            delete_users_by_date_range(before_date=before_date, dry_run=not args.execute)
        except ValueError:
            print(f"Invalid date format. Use YYYY-MM-DD")
    
    if args.user_id:
        delete_user_by_id(args.user_id, dry_run=not args.execute)
    
    if args.user_ids:
        try:
            # Parse comma-separated IDs
            user_ids = [int(id.strip()) for id in args.user_ids.split(',')]
            delete_users_by_ids(user_ids, dry_run=not args.execute)
        except ValueError:
            print("Error: --user-ids must be comma-separated numbers (e.g., '1,3,4,5')")

if __name__ == '__main__':
    main()

