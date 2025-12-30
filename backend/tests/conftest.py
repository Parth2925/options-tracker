"""
Pytest configuration and fixtures for testing
"""
import pytest
import os
import sys
from datetime import datetime, date
from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import User, Account, Trade, StockPosition

@pytest.fixture(scope='function')
def test_app():
    """Create a test Flask application"""
    # Use in-memory SQLite database for testing
    # Create a fresh app instance to avoid config conflicts
    test_app = Flask(__name__)
    test_app.config['TESTING'] = True
    # Use unique database URI for each test to avoid conflicts
    import uuid
    test_app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///:memory:{uuid.uuid4().hex[:8]}'
    test_app.config['JWT_SECRET_KEY'] = 'test-secret-key'
    test_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    test_app.config['FINNHUB_API_KEY'] = 'test-key'
    
    # Initialize extensions
    from flask_cors import CORS
    from flask_jwt_extended import JWTManager
    db.init_app(test_app)
    jwt = JWTManager(test_app)
    CORS(test_app)
    
    with test_app.app_context():
        db.create_all()
        yield test_app
        db.session.remove()
        db.drop_all()
        db.session.close()

@pytest.fixture(scope='function')
def test_client(test_app):
    """Create a test client"""
    return test_app.test_client()

@pytest.fixture(scope='function')
def test_user(test_app):
    """Create a test user"""
    with test_app.app_context():
        user = User(
            email='test@example.com',
            first_name='Test',
            last_name='User',
            password_hash='hashed_password',
            email_verified=True
        )
        db.session.add(user)
        db.session.commit()
        # Refresh to ensure user is attached to session
        db.session.refresh(user)
        return user

@pytest.fixture(scope='function')
def test_account(test_app, test_user):
    """Create a test account for the test user"""
    with test_app.app_context():
        # Use the existing test_user
        # Re-attach test_user to current session if needed
        if test_user not in db.session:
            db.session.merge(test_user)
            db.session.flush()
        
        # Create account
        account = Account(
            user_id=test_user.id,
            name='Test Account',
            initial_balance=10000.00
        )
        db.session.add(account)
        db.session.commit()
        
        # Refresh to ensure account has user relationship loaded
        db.session.refresh(account)
        return account

@pytest.fixture(scope='function')
def auth_headers(test_app, test_user):
    """Get authentication headers for test user"""
    # For testing, we'll need to create a token
    # In a real scenario, you'd login first
    from flask_jwt_extended import create_access_token
    with test_app.app_context():
        token = create_access_token(identity=test_user.id)
        return {'Authorization': f'Bearer {token}'}
