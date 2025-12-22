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
    """Send password reset email to user"""
    try:
        from flask_mail import Message
        # Get frontend URL from environment or use default
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
        
        mail = current_app.extensions.get('mail')
        if mail:
            mail.send(msg)
            return True
    except Exception as e:
        print(f"Error sending password reset email: {str(e)}")
    return False

def send_verification_email(user, token):
    """Send verification email to user (non-blocking with timeout)"""
    import signal
    
    def timeout_handler(signum, frame):
        raise TimeoutError("Email sending timed out")
    
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
            # Send email asynchronously - don't wait for it (fire and forget)
            # This prevents registration from timing out due to slow SMTP
            import threading
            from flask import copy_current_request_context
            
            @copy_current_request_context
            def send_email_async():
                # Retry logic for email sending (up to 2 retries)
                max_retries = 2
                retry_delay = 2  # seconds
                
                for attempt in range(max_retries + 1):
                    try:
                        # Access mail from current_app in the thread context
                        from flask import current_app
                        import time
                        mail_instance = current_app.extensions.get('mail')
                        if mail_instance:
                            if attempt > 0:
                                print(f"Retry {attempt}: Starting email send to {user.email}...")
                                time.sleep(retry_delay)
                            else:
                                print(f"Starting email send to {user.email}...")
                            
                            mail_instance.send(msg)
                            print(f"Email sent successfully to {user.email}")
                            return  # Success - exit function
                        else:
                            print(f"WARNING: Mail extension not available for {user.email}")
                            return
                    except OSError as e:
                        # Network errors - retry
                        error_msg = str(e)
                        print(f"Network error sending email to {user.email} (attempt {attempt + 1}/{max_retries + 1}): {error_msg}")
                        if attempt < max_retries:
                            print(f"Will retry in {retry_delay} seconds...")
                            continue
                        else:
                            print(f"Failed to send email to {user.email} after {max_retries + 1} attempts. User can resend from profile.")
                            import traceback
                            print(f"Final email error traceback: {traceback.format_exc()}")
                    except Exception as e:
                        # Other errors - log and don't retry
                        print(f"Error sending email to {user.email}: {str(e)}")
                        import traceback
                        print(f"Email error traceback: {traceback.format_exc()}")
                        return
            
            # Start email sending in background thread - don't wait for it
            email_thread = threading.Thread(target=send_email_async)
            email_thread.daemon = True
            email_thread.start()
            print(f"Email sending started in background for {user.email}")
            
            # Return True immediately - email will be sent in background
            # Even if it fails, user can resend verification email from profile
            return True
    except Exception as e:
        print(f"Error sending verification email: {str(e)}")
        import traceback
        print(f"Email error traceback: {traceback.format_exc()}")
    return False

@auth_bp.route('/register', methods=['POST'])
def register():
    print("=" * 50)
    print("REGISTER ENDPOINT CALLED")
    print(f"Request method: {request.method}")
    print(f"Request headers: {dict(request.headers)}")
    print("=" * 50)
    
    # #region agent log
    import json
    import time
    import traceback
    data = request.get_json()
    print(f"REGISTER: Received data: {data}")
    try:
        with open('/tmp/debug.log', 'a') as f:
            f.write(json.dumps({
                'timestamp': time.time(),
                'location': 'auth.py:register',
                'message': 'Registration attempt started',
                'data': {
                    'has_data': data is not None,
                    'has_email': bool(data.get('email') if data else False),
                    'has_password': bool(data.get('password') if data else False),
                    'has_first_name': bool(data.get('first_name') if data else False),
                    'has_last_name': bool(data.get('last_name') if data else False),
                    'email': data.get('email') if data else None
                },
                'sessionId': 'debug-session',
                'runId': 'run1',
                'hypothesisId': 'A'
            }) + '\n')
    except Exception as log_err:
        print(f"Debug log error: {log_err}")
    # #endregion
    
    data = request.get_json()
    print(f"REGISTER: Parsed data: {data}")
    
    # Validate required fields
    print(f"REGISTER: Validating fields - email: {bool(data and data.get('email'))}, password: {bool(data and data.get('password'))}, first_name: {bool(data and data.get('first_name'))}, last_name: {bool(data and data.get('last_name'))}")
    if not data or not data.get('email') or not data.get('password'):
        print("REGISTER ERROR: Email and password are required")
        return jsonify({'error': 'Email and password are required'}), 400
    
    if not data.get('first_name') or not data.get('last_name'):
        print("REGISTER ERROR: First name and last name are required")
        return jsonify({'error': 'First name and last name are required'}), 400
    
    # #region agent log
    try:
        with open('/tmp/debug.log', 'a') as f:
            f.write(json.dumps({
                'timestamp': time.time(),
                'location': 'auth.py:register',
                'message': 'Before checking existing user',
                'data': {'email': data.get('email')},
                'sessionId': 'debug-session',
                'runId': 'run1',
                'hypothesisId': 'B'
            }) + '\n')
    except:
        pass
    # #endregion
    
    # Check if user already exists
    print(f"REGISTER: Checking if user exists for email: {data['email']}")
    try:
        existing_user = User.query.filter_by(email=data['email']).first()
        print(f"REGISTER: User exists check complete. Found: {existing_user is not None}")
    except Exception as e:
        print(f"REGISTER ERROR: Database query failed: {type(e).__name__}: {str(e)}")
        import traceback
        print(f"REGISTER ERROR TRACEBACK: {traceback.format_exc()}")
        return jsonify({'error': 'Database error. Please try again.'}), 500
    
    if existing_user:
        print(f"REGISTER: User already exists, returning 400")
        return jsonify({'error': 'User already exists'}), 400
    
    # #region agent log
    try:
        with open('/tmp/debug.log', 'a') as f:
            f.write(json.dumps({
                'timestamp': time.time(),
                'location': 'auth.py:register',
                'message': 'Before creating user object',
                'data': {
                    'email': data.get('email'),
                    'first_name': data.get('first_name'),
                    'last_name': data.get('last_name')
                },
                'sessionId': 'debug-session',
                'runId': 'run1',
                'hypothesisId': 'C'
            }) + '\n')
    except:
        pass
    # #endregion
    
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
    
    # #region agent log
    try:
        with open('/tmp/debug.log', 'a') as f:
            f.write(json.dumps({
                'timestamp': time.time(),
                'location': 'auth.py:register',
                'message': 'Before database operations',
                'data': {
                    'user_email': user.email,
                    'has_password_hash': bool(user.password_hash),
                    'verification_token': verification_token[:10] + '...'
                },
                'sessionId': 'debug-session',
                'runId': 'run1',
                'hypothesisId': 'D'
            }) + '\n')
    except:
        pass
    # #endregion
    
    try:
        # #region agent log
        try:
            with open('/tmp/debug.log', 'a') as f:
                f.write(json.dumps({
                    'timestamp': time.time(),
                    'location': 'auth.py:register',
                    'message': 'Before db.session.add',
                    'data': {},
                    'sessionId': 'debug-session',
                    'runId': 'run1',
                    'hypothesisId': 'E'
                }) + '\n')
        except:
            pass
        # #endregion
        
        db.session.add(user)
        
        # #region agent log
        try:
            with open('/tmp/debug.log', 'a') as f:
                f.write(json.dumps({
                    'timestamp': time.time(),
                    'location': 'auth.py:register',
                    'message': 'Before db.session.commit',
                    'data': {},
                    'sessionId': 'debug-session',
                    'runId': 'run1',
                    'hypothesisId': 'E'
                }) + '\n')
        except:
            pass
        # #endregion
        
        print(f"REGISTER: Committing user to database...")
        db.session.commit()
        print(f"REGISTER: User committed successfully. User ID: {user.id}")
        
        # #region agent log
        try:
            with open('/tmp/debug.log', 'a') as f:
                f.write(json.dumps({
                    'timestamp': time.time(),
                    'location': 'auth.py:register',
                    'message': 'After db.session.commit - user created',
                    'data': {
                        'user_id': user.id,
                        'user_email': user.email
                    },
                    'sessionId': 'debug-session',
                    'runId': 'run1',
                    'hypothesisId': 'F'
                }) + '\n')
        except:
            pass
        # #endregion
        
        # Send verification email (non-blocking - don't wait for it)
        # #region agent log
        try:
            with open('/tmp/debug.log', 'a') as f:
                f.write(json.dumps({
                    'timestamp': time.time(),
                    'location': 'auth.py:register',
                    'message': 'Before sending verification email',
                    'data': {
                        'user_id': user.id,
                        'user_email': user.email
                    },
                    'sessionId': 'debug-session',
                    'runId': 'run1',
                    'hypothesisId': 'G'
                }) + '\n')
        except:
            pass
        # #endregion
        
        print(f"REGISTER: Attempting to send verification email...")
        # Send email in background - don't block on it
        try:
            email_sent = send_verification_email(user, verification_token)
            print(f"REGISTER: Email send result: {email_sent}")
        except Exception as email_error:
            # Don't fail registration if email fails
            print(f"REGISTER WARNING: Email sending failed (non-critical): {str(email_error)}")
            email_sent = False
        
        # #region agent log
        try:
            with open('/tmp/debug.log', 'a') as f:
                f.write(json.dumps({
                    'timestamp': time.time(),
                    'location': 'auth.py:register',
                    'message': 'After sending verification email',
                    'data': {
                        'email_sent': email_sent,
                        'user_id': user.id
                    },
                    'sessionId': 'debug-session',
                    'runId': 'run1',
                    'hypothesisId': 'G'
                }) + '\n')
        except:
            pass
        # #endregion
        
        # #region agent log
        try:
            with open('/tmp/debug.log', 'a') as f:
                f.write(json.dumps({
                    'timestamp': time.time(),
                    'location': 'auth.py:register',
                    'message': 'Before creating JWT token',
                    'data': {
                        'user_id': user.id,
                        'user_id_type': type(user.id).__name__
                    },
                    'sessionId': 'debug-session',
                    'runId': 'run1',
                    'hypothesisId': 'H'
                }) + '\n')
        except:
            pass
        # #endregion
        
        access_token = create_access_token(identity=str(user.id))
        
        # #region agent log
        try:
            with open('/tmp/debug.log', 'a') as f:
                f.write(json.dumps({
                    'timestamp': time.time(),
                    'location': 'auth.py:register',
                    'message': 'Registration successful',
                    'data': {
                        'user_id': user.id,
                        'token_created': bool(access_token)
                    },
                    'sessionId': 'debug-session',
                    'runId': 'run1',
                    'hypothesisId': 'I'
                }) + '\n')
        except:
            pass
        # #endregion
        
        return jsonify({
            'message': 'User created successfully. Please check your email to verify your account.',
            'access_token': access_token,
            'user': user.to_dict()
        }), 201
    except Exception as e:
        # #region agent log
        error_traceback = traceback.format_exc()
        print(f"REGISTRATION ERROR: {type(e).__name__}: {str(e)}")
        print(f"REGISTRATION TRACEBACK: {error_traceback}")
        try:
            with open('/tmp/debug.log', 'a') as f:
                f.write(json.dumps({
                    'timestamp': time.time(),
                    'location': 'auth.py:register',
                    'message': 'Registration error caught',
                    'data': {
                        'error_type': type(e).__name__,
                        'error_message': str(e),
                        'error_traceback': error_traceback
                    },
                    'sessionId': 'debug-session',
                    'runId': 'run1',
                    'hypothesisId': 'ERROR'
                }) + '\n')
        except:
            pass
        # #endregion
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password are required'}), 400
    
    email = data['email'].strip() if data.get('email') else None
    user = User.query.filter_by(email=email).first()
    
    if not user:
        return jsonify({'error': 'Invalid email or password'}), 401
    
    if not user.check_password(data['password']):
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

