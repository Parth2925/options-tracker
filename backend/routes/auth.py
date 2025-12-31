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

def generate_reset_token():
    """Generate a secure random token for password reset"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(32))

def send_password_reset_email(user, token):
    """Send password reset email to user (asynchronous, non-blocking)"""
    try:
        from flask_mail import Message
        frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
        reset_url = f"{frontend_url}/reset-password?token={token}"
        
        msg = Message(
            subject='Reset Your Password - Options Tracker',
            recipients=[user.email],
            html=f"""
            <html>
            <body>
                <h2>Password Reset Request</h2>
                <p>Hi {user.first_name},</p>
                <p>We received a request to reset your password. Click the link below to reset it:</p>
                <p><a href="{reset_url}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">Reset Password</a></p>
                <p>Or copy and paste this link into your browser:</p>
                <p>{reset_url}</p>
                <p>This link will expire in 1 hour.</p>
                <p>If you didn't request a password reset, please ignore this email. Your password will remain unchanged.</p>
            </body>
            </html>
            """,
            body=f"""
            Password Reset Request
            
            Hi {user.first_name},
            
            We received a request to reset your password. Visit the link below to reset it:
            {reset_url}
            
            This link will expire in 1 hour.
            
            If you didn't request a password reset, please ignore this email. Your password will remain unchanged.
            """
        )
        
        # Send email asynchronously - don't wait for it (fire and forget)
        import threading
        from flask import copy_current_request_context
        
        @copy_current_request_context
        def send_email_async():
            try:
                mail = current_app.extensions.get('mail')
                if mail:
                    mail.send(msg)
            except Exception as e:
                # Silently fail - email sending is not critical
                pass
        
        email_thread = threading.Thread(target=send_email_async)
        email_thread.daemon = True
        email_thread.start()
        return True
    except Exception as e:
        # Return True anyway - email failure shouldn't block password reset request
        return True

def send_verification_email(user, token):
    """Send verification email to user (asynchronous, non-blocking)"""
    try:
        from flask_mail import Message
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
        
        # Send email asynchronously - don't wait for it (fire and forget)
        # This prevents registration from timing out and allows site to work even if email fails
        import threading
        from flask import copy_current_request_context
        
        @copy_current_request_context
        def send_email_async():
            try:
                mail = current_app.extensions.get('mail')
                if mail:
                    mail.send(msg)
            except Exception as e:
                # Silently fail - email sending is not critical for registration
                pass
        
        email_thread = threading.Thread(target=send_email_async)
        email_thread.daemon = True
        email_thread.start()
        
        # Return True immediately - email will be sent in background
        # Even if it fails, user can still use the site and resend verification email from profile
        return True
    except Exception as e:
        # Return True anyway - email failure shouldn't block registration
        return True

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Parse data
    data = {
        'email': data.get('email', '').strip().lower(),
        'password': data.get('password', ''),
        'first_name': data.get('first_name', '').strip(),
        'last_name': data.get('last_name', '').strip()
    }
    
    # Validate required fields
    if not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password are required'}), 400
    
    if not data.get('first_name') or not data.get('last_name'):
        return jsonify({'error': 'First name and last name are required'}), 400
    
    # Check if user already exists
    try:
        existing_user = User.query.filter_by(email=data['email']).first()
    except Exception as e:
        import traceback
        return jsonify({'error': 'Database error. Please try again.'}), 500
    
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
        
        # Send verification email (non-blocking - don't wait for it)
        # Registration succeeds even if email fails
        send_verification_email(user, verification_token)
        
        access_token = create_access_token(identity=str(user.id))
        
        return jsonify({
            'message': 'User created successfully. Please check your email to verify your account.',
            'access_token': access_token,
            'user': user.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        import traceback
        return jsonify({'error': 'Failed to create user. Please try again.'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password are required'}), 400
    
    email = data['email'].strip().lower() if data.get('email') else None
    user = User.query.filter_by(email=email).first()
    
    if not user:
        return jsonify({'error': 'Invalid email or password'}), 401
    
    password_check_result = user.check_password(data['password'])
    
    if not password_check_result:
        return jsonify({'error': 'Invalid email or password'}), 401
    
    try:
        # Convert user.id to string for JWT (consistent with register endpoint)
        access_token = create_access_token(identity=str(user.id))
        
        return jsonify({
            'access_token': access_token,
            'user': user.to_dict()
        }), 200
    except Exception as e:
        return jsonify({'error': f'Failed to create access token: {str(e)}'}), 500

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
    
    if not token:
        return jsonify({'error': 'Verification token is required'}), 400
    
    user = User.query.filter_by(verification_token=token).first()
    
    if not user:
        # Token not found - could mean:
        # 1. Token was already used (user verified)
        # 2. Token is invalid/expired
        # Since we can't distinguish, provide helpful error message
        return jsonify({'error': 'Invalid or expired verification token. If you already verified your email, you can log in. Otherwise, please request a new verification email from your profile page.'}), 400
    
    # Check if already verified (idempotent - allow re-verification attempts)
    if user.email_verified:
        return jsonify({'message': 'Email is already verified'}), 200
    
    # Check if token has expired
    if user.verification_token_expires and user.verification_token_expires < datetime.utcnow():
        return jsonify({'error': 'Verification token has expired. Please request a new verification email.'}), 400
    
    # Verify email (idempotent - safe to call multiple times)
    if not user.email_verified:
        user.email_verified = True
        # Keep the token in database for idempotency (don't clear it)
        # This allows the same link to be clicked multiple times without error
        # The token will naturally expire after 24 hours anyway
    
    try:
        db.session.commit()
        return jsonify({'message': 'Email verified successfully'}), 200
    except Exception as e:
        db.session.rollback()
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

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """Request password reset - sends email with reset link"""
    data = request.get_json()
    
    if not data or not data.get('email'):
        return jsonify({'error': 'Email is required'}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    
    # For security, don't reveal if email exists or not
    # Always return success message to prevent email enumeration
    if user:
        # Generate reset token
        reset_token = generate_reset_token()
        token_expires = datetime.utcnow() + timedelta(hours=1)  # 1 hour expiration
        
        user.reset_token = reset_token
        user.reset_token_expires = token_expires
        user.updated_at = datetime.utcnow()
        
        try:
            db.session.commit()
            send_password_reset_email(user, reset_token)
        except Exception as e:
            db.session.rollback()
            print(f"Error generating reset token: {str(e)}")
    
    # Always return success message (security best practice)
    return jsonify({
        'message': 'If an account with that email exists, a password reset link has been sent.'
    }), 200

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """Reset password using token from email"""
    data = request.get_json()
    
    if not data or not data.get('token'):
        return jsonify({'error': 'Reset token is required'}), 400
    
    if not data.get('password'):
        return jsonify({'error': 'New password is required'}), 400
    
    if not data.get('confirm_password'):
        return jsonify({'error': 'Password confirmation is required'}), 400
    
    if data.get('password') != data.get('confirm_password'):
        return jsonify({'error': 'Passwords do not match'}), 400
    
    # Validate password length
    if len(data['password']) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400
    
    # Find user by reset token
    user = User.query.filter_by(reset_token=data['token']).first()
    
    if not user:
        return jsonify({'error': 'Invalid or expired reset token'}), 400
    
    # Check if token has expired
    if user.reset_token_expires and user.reset_token_expires < datetime.utcnow():
        # Clear expired token
        user.reset_token = None
        user.reset_token_expires = None
        db.session.commit()
        return jsonify({'error': 'Reset token has expired. Please request a new password reset.'}), 400
    
    # Reset password
    user.set_password(data['password'])
    # Clear reset token (one-time use)
    user.reset_token = None
    user.reset_token_expires = None
    user.updated_at = datetime.utcnow()
    
    try:
        db.session.commit()
        return jsonify({'message': 'Password reset successfully. You can now login with your new password.'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change user password (requires current password)"""
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

