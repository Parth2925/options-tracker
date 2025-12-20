from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from models import db
from routes.auth import auth_bp
from routes.accounts import accounts_bp
from routes.trades import trades_bp
from routes.dashboard import dashboard_bp
import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///options_tracker.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7)
app.config['FINNHUB_API_KEY'] = os.getenv('FINNHUB_API_KEY', 'd525qj1r01qu5pvmiv2gd525qj1r01qu5pvmiv30')

# Initialize extensions
db.init_app(app)
jwt = JWTManager(app)

# Configure Flask-Mail for email verification
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME', '')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', '')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@optionstracker.com')
mail = Mail(app)

# Configure JWT to handle integer user IDs
@jwt.user_identity_loader
def user_identity_lookup(user_id):
    return str(user_id) if user_id is not None else None

@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_payload):
    from models import User
    identity = jwt_payload["sub"]
    return User.query.filter_by(id=int(identity)).one_or_none()
# Configure CORS
# In production, use FRONTEND_URL environment variable
# In development, allow localhost
frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
allowed_origins = [frontend_url]
if os.getenv('FLASK_ENV') != 'production':
    # Allow localhost for development
    allowed_origins.extend(['http://localhost:3000', 'http://127.0.0.1:3000'])

CORS(app, 
     resources={r"/api/*": {
         "origins": allowed_origins,
         "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
         "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
         "supports_credentials": True
     }}
)

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(accounts_bp, url_prefix='/api/accounts')
app.register_blueprint(trades_bp, url_prefix='/api/trades')
app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')

# Tables will be created on first request or when app starts

@app.route('/api/health', methods=['GET'])
def health_check():
    return {'status': 'ok'}, 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Migration: Add trade_price and trade_action columns if they don't exist
        try:
            from sqlalchemy import inspect, text
            inspector = inspect(db.engine)
            
            # Check if trades table exists
            if 'trades' in inspector.get_table_names():
                columns = [col['name'] for col in inspector.get_columns('trades')]
                
                with db.engine.connect() as conn:
                    if 'trade_price' not in columns:
                        print("Adding trade_price column to trades table...")
                        conn.execute(text("ALTER TABLE trades ADD COLUMN trade_price NUMERIC(10, 2)"))
                        conn.commit()
                        print("✓ Added trade_price column")
                    
                    if 'trade_action' not in columns:
                        print("Adding trade_action column to trades table...")
                        conn.execute(text("ALTER TABLE trades ADD COLUMN trade_action VARCHAR(30)"))
                        conn.commit()
                        print("✓ Added trade_action column")
                    
                    if 'open_date' not in columns:
                        print("Adding open_date column to trades table...")
                        conn.execute(text("ALTER TABLE trades ADD COLUMN open_date DATE"))
                        conn.commit()
                        print("✓ Added open_date column")
                
                # Migration: Add user profile fields if they don't exist
                if 'users' in inspector.get_table_names():
                    user_columns = [col['name'] for col in inspector.get_columns('users')]
                    
                    with db.engine.connect() as conn:
                        if 'first_name' not in user_columns:
                            print("Adding first_name column to users table...")
                            conn.execute(text("ALTER TABLE users ADD COLUMN first_name VARCHAR(100) DEFAULT ''"))
                            conn.commit()
                            print("✓ Added first_name column")
                        
                        if 'last_name' not in user_columns:
                            print("Adding last_name column to users table...")
                            conn.execute(text("ALTER TABLE users ADD COLUMN last_name VARCHAR(100) DEFAULT ''"))
                            conn.commit()
                            print("✓ Added last_name column")
                        
                        if 'email_verified' not in user_columns:
                            print("Adding email_verified column to users table...")
                            conn.execute(text("ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT 0"))
                            conn.commit()
                            print("✓ Added email_verified column")
                        
                        if 'verification_token' not in user_columns:
                            print("Adding verification_token column to users table...")
                            conn.execute(text("ALTER TABLE users ADD COLUMN verification_token VARCHAR(100)"))
                            conn.commit()
                            print("✓ Added verification_token column")
                        
                        if 'verification_token_expires' not in user_columns:
                            print("Adding verification_token_expires column to users table...")
                            conn.execute(text("ALTER TABLE users ADD COLUMN verification_token_expires DATETIME"))
                            conn.commit()
                            print("✓ Added verification_token_expires column")
                        
                        if 'updated_at' not in user_columns:
                            print("Adding updated_at column to users table...")
                            conn.execute(text("ALTER TABLE users ADD COLUMN updated_at DATETIME"))
                            conn.commit()
                            print("✓ Added updated_at column")
        except Exception as e:
            # If table doesn't exist yet, db.create_all() will create it with all columns
            # This error is expected for new databases
            pass
    
    print("=" * 50)
    print("Backend server starting...")
    print("Server will run on: http://127.0.0.1:5001")
    print("API endpoints available at: http://127.0.0.1:5001/api")
    print("Health check: http://127.0.0.1:5001/api/health")
    print("=" * 50)
    app.run(debug=True, port=5001, host='127.0.0.1')

