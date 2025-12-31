#!/usr/bin/env python3
"""Script to list all users in the database"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import app
from models import db, User, Account, Trade

def list_users():
    with app.app_context():
        users = User.query.all()
        
        print(f"\nTotal users in database: {len(users)}\n")
        print("=" * 80)
        
        for user in users:
            print(f"\nUser ID: {user.id}")
            print(f"  Email: {user.email}")
            print(f"  Name: {user.first_name} {user.last_name}")
            print(f"  Email Verified: {user.email_verified}")
            print(f"  Created: {user.created_at}")
            
            # Count related data
            accounts = Account.query.filter_by(user_id=user.id).all()
            total_trades = 0
            total_accounts = len(accounts)
            
            for account in accounts:
                trades = Trade.query.filter_by(account_id=account.id).all()
                total_trades += len(trades)
            
            print(f"  Accounts: {total_accounts}")
            print(f"  Trades: {total_trades}")
            print("-" * 80)

if __name__ == '__main__':
    list_users()

