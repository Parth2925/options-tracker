from flask import Blueprint, request, jsonify, current_app, url_for
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import db, User
from datetime import datetime, timedelta
import secrets
import string
import os

auth_bp = Blueprint('auth', __name__)

def generate_verification_token():
    """Generate a secure random token for email verification"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(32))

def send_verification_email(user, token):
    """Send verification email to user"""
    try:
        from flask_mail import Message
        # Get frontend URL from environment or use default
        frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
        verification_url = f"{frontend_url}/verify-email?token={token}"
        
        msg = Message(
            subject='Verify Your Email - Options Tracker',
            recipients=[user.email],
            html=f"""
            <html>
            <body>
                <h2>Welcome to Options Tracker!</h2>
                <p>Hi {user.first_name},</p>
                <p>Thank you for registering. Please verify your email address by clicking the link below:</p>
                <p><a href="{verification_url}" style="background-color: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">Verify Email</a></p>
                <p>Or copy and paste this link into your browser:</p>
                <p>{verification_url}</p>
                <p>This link will expire in 24 hours.</p>
                <p>If you didn't create this account, please ignore this email.</p>
            </body>
            </html>
            """,
            body=f"""
            Welcome to Options Tracker!
            
            Hi {user.first_name},
            
            Thank you for registering. Please verify your email address by visiting:
            {verification_url}
            
            This link will expire in 24 hours.
            
            If you didn't create this account, please ignore this email.
            """
        )
        
        mail = current_app.extensions.get('mail')
        if mail:
            mail.send(msg)
            return True
    except Exception as e:
        print(f"Error sending verification email: {str(e)}")
    return False

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Validate required fields
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password are required'}), 400
    
    if not data.get('first_name') or not data.get('last_name'):
        return jsonify({'error': 'First name and last name are required'}), 400
    
    # Check if user already exists
    existing_user = User.query.filter_by(email=data['email']).first()
    if existing_user:
        return jsonify({'error': 'User already exists'}), 400
    
    # Generate verification token
    verification_token = generate_verification_token()
    token_expires = datetime.utcnow() + timedelta(hours=24)
    
    # Create new user
    user = User(
        email=data['email'],
        first_name=data['first_name'],
        last_name=data['last_name'],
        email_verified=False,
        verification_token=verification_token,
        verification_token_expires=token_expires
    )
    user.set_password(data['password'])
    
    try:
        db.session.add(user)
        db.session.commit()
        
        # Send verification email
        send_verification_email(user, verification_token)
        
        access_token = create_access_token(identity=str(user.id))
        return jsonify({
            'message': 'User created successfully. Please check your email to verify your account.',
            'access_token': access_token,
            'user': user.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password are required'}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    
    if not user or not user.check_password(data['password']):
        return jsonify({'error': 'Invalid email or password'}), 401
    
    access_token = create_access_token(identity=user.id)
    return jsonify({
        'access_token': access_token,
        'user': user.to_dict()
    }), 200

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify(user.to_dict()), 200

@auth_bp.route('/verify-email', methods=['GET'])
def verify_email():
    """Verify user email with token"""
    token = request.args.get('token')
    
    # #region agent log
    import json
    import time
    try:
        with open('/Users/parthsoni/Documents/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({
                'timestamp': time.time(),
                'location': 'auth.py:verify_email',
                'message': 'Verification attempt started',
                'data': {'token': token[:10] + '...' if token else None},
                'sessionId': 'debug-session',
                'runId': 'run1',
                'hypothesisId': 'A'
            }) + '\n')
    except:
        pass
    # #endregion
    
    if not token:
        return jsonify({'error': 'Verification token is required'}), 400
    
    user = User.query.filter_by(verification_token=token).first()
    
    # #region agent log
    try:
        with open('/Users/parthsoni/Documents/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({
                'timestamp': time.time(),
                'location': 'auth.py:verify_email',
                'message': 'User lookup by token',
                'data': {'token_found': user is not None, 'user_id': user.id if user else None, 'email_verified': user.email_verified if user else None, 'has_token': user.verification_token is not None if user else None},
                'sessionId': 'debug-session',
                'runId': 'run1',
                'hypothesisId': 'A'
            }) + '\n')
    except:
        pass
    # #endregion
    
    if not user:
        # Token not found - could mean:
        # 1. Token was already used (user verified)
        # 2. Token is invalid/expired
        # Since we can't distinguish, provide helpful error message
        # #region agent log
        try:
            with open('/Users/parthsoni/Documents/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({
                    'timestamp': time.time(),
                    'location': 'auth.py:verify_email',
                    'message': 'Token not found in database',
                    'data': {},
                    'sessionId': 'debug-session',
                    'runId': 'run1',
                    'hypothesisId': 'A'
                }) + '\n')
        except:
            pass
        # #endregion
        return jsonify({'error': 'Invalid or expired verification token. If you already verified your email, you can log in. Otherwise, please request a new verification email from your profile page.'}), 400
    
    # Check if already verified (idempotent - allow re-verification attempts)
    if user.email_verified:
        # #region agent log
        try:
            with open('/Users/parthsoni/Documents/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({
                    'timestamp': time.time(),
                    'location': 'auth.py:verify_email',
                    'message': 'User already verified - returning success',
                    'data': {'user_id': user.id},
                    'sessionId': 'debug-session',
                    'runId': 'run1',
                    'hypothesisId': 'A'
                }) + '\n')
        except:
            pass
        # #endregion
        return jsonify({'message': 'Email is already verified'}), 200
    
    # Check if token has expired
    if user.verification_token_expires and user.verification_token_expires < datetime.utcnow():
        # #region agent log
        try:
            with open('/Users/parthsoni/Documents/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({
                    'timestamp': time.time(),
                    'location': 'auth.py:verify_email',
                    'message': 'Token expired',
                    'data': {'user_id': user.id, 'expires': str(user.verification_token_expires), 'now': str(datetime.utcnow())},
                    'sessionId': 'debug-session',
                    'runId': 'run1',
                    'hypothesisId': 'A'
                }) + '\n')
        except:
            pass
        # #endregion
        return jsonify({'error': 'Verification token has expired. Please request a new verification email.'}), 400
    
    # Verify email (idempotent - safe to call multiple times)
    was_already_verified = user.email_verified
    if not user.email_verified:
        user.email_verified = True
        # Keep the token in database for idempotency (don't clear it)
        # This allows the same link to be clicked multiple times without error
        # The token will naturally expire after 24 hours anyway
    
    try:
        db.session.commit()
        # #region agent log
        try:
            with open('/Users/parthsoni/Documents/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({
                    'timestamp': time.time(),
                    'location': 'auth.py:verify_email',
                    'message': 'Email verified successfully',
                    'data': {'user_id': user.id, 'was_already_verified': was_already_verified},
                    'sessionId': 'debug-session',
                    'runId': 'run1',
                    'hypothesisId': 'A'
                }) + '\n')
        except:
            pass
        # #endregion
        return jsonify({'message': 'Email verified successfully'}), 200
    except Exception as e:
        db.session.rollback()
        # #region agent log
        try:
            with open('/Users/parthsoni/Documents/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({
                    'timestamp': time.time(),
                    'location': 'auth.py:verify_email',
                    'message': 'Database error during verification',
                    'data': {'user_id': user.id, 'error': str(e)},
                    'sessionId': 'debug-session',
                    'runId': 'run1',
                    'hypothesisId': 'A'
                }) + '\n')
        except:
            pass
        # #endregion
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/resend-verification', methods=['POST'])
@jwt_required()
def resend_verification():
    """Resend verification email"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    if user.email_verified:
        return jsonify({'message': 'Email is already verified'}), 200
    
    # Generate new verification token
    verification_token = generate_verification_token()
    token_expires = datetime.utcnow() + timedelta(hours=24)
    
    user.verification_token = verification_token
    user.verification_token_expires = token_expires
    
    try:
        db.session.commit()
        send_verification_email(user, verification_token)
        return jsonify({'message': 'Verification email sent successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/update-profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update user profile (first name, last name, email)"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    
    # Update fields if provided
    if 'first_name' in data:
        user.first_name = data['first_name']
    
    if 'last_name' in data:
        user.last_name = data['last_name']
    
    if 'email' in data:
        new_email = data['email']
        # Check if email is already taken by another user
        existing_user = User.query.filter_by(email=new_email).first()
        if existing_user and existing_user.id != user.id:
            return jsonify({'error': 'Email already in use'}), 400
        
        # If email changed, require re-verification
        if new_email != user.email:
            user.email = new_email
            user.email_verified = False
            # Generate new verification token
            verification_token = generate_verification_token()
            token_expires = datetime.utcnow() + timedelta(hours=24)
            user.verification_token = verification_token
            user.verification_token_expires = token_expires
            send_verification_email(user, verification_token)
    
    user.updated_at = datetime.utcnow()
    
    try:
        db.session.commit()
        return jsonify({
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change user password"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    
    if not data.get('current_password') or not data.get('new_password'):
        return jsonify({'error': 'Current password and new password are required'}), 400
    
    # Verify current password
    if not user.check_password(data['current_password']):
        return jsonify({'error': 'Current password is incorrect'}), 401
    
    # Validate new password
    if len(data['new_password']) < 6:
        return jsonify({'error': 'New password must be at least 6 characters'}), 400
    
    # Set new password
    user.set_password(data['new_password'])
    user.updated_at = datetime.utcnow()
    
    try:
        db.session.commit()
        return jsonify({'message': 'Password changed successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

