#!/usr/bin/env python3
"""Script to create test@example.com user if it doesn't exist"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import app
from models import db, User

def create_test_user():
    with app.app_context():
        email = 'test@example.com'
        password = 'password123'
        
        # Check if user exists
        user = User.query.filter_by(email=email).first()
        if user:
            print(f"User {email} already exists with ID: {user.id}")
            print(f"Email verified: {user.email_verified}")
            # Update password to be sure
            user.set_password(password)
            user.email_verified = True
            db.session.commit()
            print(f"Password updated and email verified set to True")
        else:
            # Create user
            user = User(
                email=email,
                first_name='Test',
                last_name='User',
                email_verified=True
            )
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            print(f"Created user {email} with ID: {user.id}")

if __name__ == '__main__':
    create_test_user()

