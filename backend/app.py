from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required
from flask_mail import Mail
from models import db
from routes.auth import auth_bp
from routes.accounts import accounts_bp
from routes.trades import trades_bp
from routes.dashboard import dashboard_bp
from routes.stock_positions import stock_positions_bp
from version import get_version
import os
from datetime import timedelta, datetime
from dotenv import load_dotenv
import threading
import requests
import time

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Configuration
database_url = os.getenv('DATABASE_URL', 'sqlite:///options_tracker.db')

# Fix PostgreSQL SSL connection issues on Render
# If using PostgreSQL, ensure SSL mode is set correctly
if database_url.startswith('postgresql://') or database_url.startswith('postgres://'):
    # Parse the database URL and add SSL parameters if not present
    if 'sslmode' not in database_url:
        # Add sslmode=require for Render PostgreSQL
        separator = '&' if '?' in database_url else '?'
        database_url = f"{database_url}{separator}sslmode=require"
    print(f"Database URL configured with SSL: {database_url[:50]}...")

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Add connection pool settings - only for PostgreSQL (SQLite doesn't use connection pooling)
if database_url.startswith('postgresql://') or database_url.startswith('postgres://'):
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,  # Verify connections before using
        'pool_recycle': 300,    # Recycle connections after 5 minutes
        'pool_size': 5,         # Connection pool size
        'max_overflow': 10,     # Max overflow connections
        'connect_args': {
            'connect_timeout': 10,  # 10 second connection timeout
            'options': '-c statement_timeout=5000'  # 5 second query timeout for PostgreSQL
        }
    }
elif database_url.startswith('sqlite:///'):
    # For SQLite, ensure instance directory exists and use absolute path
    # SQLite URL format: sqlite:///path/to/db.db
    # Extract the path part (everything after sqlite:///)
    db_path = database_url.replace('sqlite:///', '')
    
    # If path contains 'instance', ensure the directory exists
    if 'instance' in db_path:
        instance_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
        if not os.path.exists(instance_dir):
            os.makedirs(instance_dir)
        
        # Convert to absolute path
        if not os.path.isabs(db_path):
            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), db_path)
        
        database_url = f'sqlite:///{db_path}'
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    
    # SQLite doesn't need connection pooling - use NullPool to disable pooling
    # For SQLite, we need check_same_thread=False for Flask's multi-threaded environment
    from sqlalchemy.pool import NullPool
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'poolclass': NullPool,  # Disable connection pooling for SQLite
        'connect_args': {
            'check_same_thread': False  # Allow SQLite to be used in multi-threaded environment
        }
    }
else:
    # For other database types, use minimal settings
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {}
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
# Remove trailing slash if present (CORS origin matching requires exact match without trailing slash)
frontend_url = frontend_url.rstrip('/')
allowed_origins = [frontend_url]

# In production, also add www/non-www variant if applicable
if os.getenv('FLASK_ENV') == 'production' and frontend_url.startswith('http'):
    # If URL contains www, also add non-www version, and vice versa
    if 'www.' in frontend_url:
        non_www_url = frontend_url.replace('www.', '')
        allowed_origins.append(non_www_url)
    elif frontend_url.startswith('https://') and '.' in frontend_url.replace('https://', ''):
        # Add www version if it's a production HTTPS URL
        parts = frontend_url.split('://', 1)
        if len(parts) == 2:
            www_url = f"{parts[0]}://www.{parts[1]}"
            allowed_origins.append(www_url)

if os.getenv('FLASK_ENV') != 'production':
    # Allow localhost for development
    allowed_origins.extend(['http://localhost:3000', 'http://127.0.0.1:3000'])

CORS(app, 
     resources={r"/api/*": {
         "origins": allowed_origins,
         "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
         "allow_headers": ["Content-Type", "Authorization", "X-Requested-With", "Accept"],
         "supports_credentials": True,
         "expose_headers": ["Content-Type", "Authorization"]
     }}
)

# Log CORS configuration for debugging
print(f"CORS Configuration:")
print(f"  Allowed origins: {allowed_origins}")
print(f"  Frontend URL from env (normalized): {frontend_url}")
print(f"  Flask ENV: {os.getenv('FLASK_ENV', 'not set')}")


# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(accounts_bp, url_prefix='/api/accounts')
app.register_blueprint(trades_bp, url_prefix='/api/trades')
app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
app.register_blueprint(stock_positions_bp, url_prefix='/api/stock-positions')

# Initialize database on app startup (works with gunicorn)
def initialize_database():
    """Initialize database tables and run migrations"""
    with app.app_context():
        try:
            # Create all tables
            db.create_all()
            print("✓ Database tables created/verified")
            
            # Run migrations for existing tables
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
                    
                    if 'close_date' not in columns:
                        print("Adding close_date column to trades table...")
                        conn.execute(text("ALTER TABLE trades ADD COLUMN close_date DATE"))
                        conn.commit()
                        print("✓ Added close_date column")
                    
                    if 'parent_trade_id' not in columns:
                        print("Adding parent_trade_id column to trades table...")
                        conn.execute(text("ALTER TABLE trades ADD COLUMN parent_trade_id INTEGER"))
                        conn.commit()
                        print("✓ Added parent_trade_id column")
                    
                    if 'assignment_price' not in columns:
                        print("Adding assignment_price column to trades table...")
                        conn.execute(text("ALTER TABLE trades ADD COLUMN assignment_price NUMERIC(10, 2)"))
                        conn.commit()
                        print("✓ Added assignment_price column")
                    
                    if 'assignment_fee' not in columns:
                        print("Adding assignment_fee column to trades table...")
                        conn.execute(text("ALTER TABLE trades ADD COLUMN assignment_fee NUMERIC(10, 2) DEFAULT 0"))
                        conn.commit()
                        print("✓ Added assignment_fee column to trades table")
            
            # Check if accounts table exists and add assignment_fee if needed
            if 'accounts' in inspector.get_table_names():
                accounts_columns = [col['name'] for col in inspector.get_columns('accounts')]
                
                with db.engine.connect() as conn:
                    if 'assignment_fee' not in accounts_columns:
                        print("Adding assignment_fee column to accounts table...")
                        conn.execute(text("ALTER TABLE accounts ADD COLUMN assignment_fee NUMERIC(10, 2) DEFAULT 0"))
                        conn.commit()
                        print("✓ Added assignment_fee column to accounts table")
            
            # Check if users table exists and add new columns if needed
            if 'users' in inspector.get_table_names():
                columns = [col['name'] for col in inspector.get_columns('users')]
                
                # Detect database type for proper column type syntax
                db_url = str(db.engine.url)
                db_url_lower = db_url.lower()
                # Check for PostgreSQL (postgresql://, postgres://, or postgresql+psycopg2://)
                is_postgres = 'postgresql' in db_url_lower or 'postgres' in db_url_lower
                datetime_type = 'TIMESTAMP' if is_postgres else 'DATETIME'
                print(f"Database URL: {db_url[:50]}...")  # Log first 50 chars for debugging
                print(f"Is PostgreSQL: {is_postgres}, datetime_type: {datetime_type}")
                print(f"Database driver: {db.engine.driver}")
                
                with db.engine.connect() as conn:
                    if 'first_name' not in columns:
                        print("Adding first_name column to users table...")
                        # For PostgreSQL, add column as nullable first, then update and set NOT NULL
                        try:
                            conn.execute(text("ALTER TABLE users ADD COLUMN first_name VARCHAR(100)"))
                            conn.execute(text("UPDATE users SET first_name = '' WHERE first_name IS NULL"))
                            conn.execute(text("ALTER TABLE users ALTER COLUMN first_name SET NOT NULL"))
                            conn.execute(text("ALTER TABLE users ALTER COLUMN first_name SET DEFAULT ''"))
                        except Exception as e:
                            # If above fails, try simpler approach (works for SQLite and some PostgreSQL versions)
                            try:
                                conn.execute(text("ALTER TABLE users ADD COLUMN first_name VARCHAR(100) NOT NULL DEFAULT ''"))
                            except:
                                # Last resort: add as nullable
                                conn.execute(text("ALTER TABLE users ADD COLUMN first_name VARCHAR(100) DEFAULT ''"))
                        conn.commit()
                        print("✓ Added first_name column")
                    
                    if 'last_name' not in columns:
                        print("Adding last_name column to users table...")
                        # For PostgreSQL, add column as nullable first, then update and set NOT NULL
                        try:
                            conn.execute(text("ALTER TABLE users ADD COLUMN last_name VARCHAR(100)"))
                            conn.execute(text("UPDATE users SET last_name = '' WHERE last_name IS NULL"))
                            conn.execute(text("ALTER TABLE users ALTER COLUMN last_name SET NOT NULL"))
                            conn.execute(text("ALTER TABLE users ALTER COLUMN last_name SET DEFAULT ''"))
                        except Exception as e:
                            # If above fails, try simpler approach (works for SQLite and some PostgreSQL versions)
                            try:
                                conn.execute(text("ALTER TABLE users ADD COLUMN last_name VARCHAR(100) NOT NULL DEFAULT ''"))
                            except:
                                # Last resort: add as nullable
                                conn.execute(text("ALTER TABLE users ADD COLUMN last_name VARCHAR(100) DEFAULT ''"))
                        conn.commit()
                        print("✓ Added last_name column")
                    
                    if 'email_verified' not in columns:
                        print("Adding email_verified column to users table...")
                        if is_postgres:
                            conn.execute(text("ALTER TABLE users ADD COLUMN email_verified BOOLEAN NOT NULL DEFAULT FALSE"))
                        else:
                            conn.execute(text("ALTER TABLE users ADD COLUMN email_verified BOOLEAN NOT NULL DEFAULT 0"))
                        conn.commit()
                        print("✓ Added email_verified column")
                    
                    if 'verification_token' not in columns:
                        print("Adding verification_token column to users table...")
                        conn.execute(text("ALTER TABLE users ADD COLUMN verification_token VARCHAR(100) UNIQUE"))
                        conn.commit()
                        print("✓ Added verification_token column")
                    
                    if 'verification_token_expires' not in columns:
                        print("Adding verification_token_expires column to users table...")
                        conn.execute(text(f"ALTER TABLE users ADD COLUMN verification_token_expires {datetime_type}"))
                        conn.commit()
                        print("✓ Added verification_token_expires column")
                    
                    if 'updated_at' not in columns:
                        print("Adding updated_at column to users table...")
                        if is_postgres:
                            conn.execute(text("ALTER TABLE users ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
                        else:
                            conn.execute(text("ALTER TABLE users ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP"))
                        conn.commit()
                        print("✓ Added updated_at column")
                    
                    if 'reset_token' not in columns:
                        print("Adding reset_token column to users table...")
                        # SQLite doesn't support adding UNIQUE constraint directly, add column first
                        conn.execute(text("ALTER TABLE users ADD COLUMN reset_token VARCHAR(100)"))
                        conn.commit()
                        # For SQLite, we can't add UNIQUE constraint via ALTER TABLE
                        # The uniqueness will be enforced at application level
                        print("✓ Added reset_token column")
                    
                    if 'reset_token_expires' not in columns:
                        print(f"Adding reset_token_expires column to users table... (using {datetime_type})")
                        sql = f"ALTER TABLE users ADD COLUMN reset_token_expires {datetime_type}"
                        print(f"Executing SQL: {sql}")
                        conn.execute(text(sql))
                        conn.commit()
                        print("✓ Added reset_token_expires column")
            
            print("✓ Database initialization complete")
        except Exception as e:
            print(f"⚠ Database initialization error (may be expected on first run): {e}")

# Initialize database when app starts
initialize_database()

@app.route('/api/health', methods=['GET'])
def health_check():
    return {'status': 'ok'}, 200

@app.route('/api/ping', methods=['GET'])
def ping():
    """Keep-alive endpoint to prevent Render free tier spin-down"""
    return {'status': 'pong', 'timestamp': datetime.utcnow().isoformat()}, 200

def keep_alive_ping():
    """
    Background thread to ping the health endpoint every 5 minutes
    This keeps the Render free tier instance awake even when no users are active
    """
    # Wait a bit for the app to fully start
    time.sleep(30)
    
    # Get the base URL from environment or use localhost for development
    base_url = os.getenv('RENDER_EXTERNAL_URL') or os.getenv('BASE_URL') or 'http://localhost:5001'
    
    # Ensure base_url doesn't end with /
    base_url = base_url.rstrip('/')
    
    ping_url = f'{base_url}/api/ping'
    
    while True:
        try:
            # Ping the health endpoint
            response = requests.get(ping_url, timeout=10)
            if response.status_code == 200:
                app.logger.debug(f'Keep-alive ping successful: {ping_url}')
            else:
                app.logger.warning(f'Keep-alive ping returned status {response.status_code}')
        except Exception as e:
            # Log but don't crash - this is just a keep-alive
            app.logger.warning(f'Keep-alive ping failed: {str(e)}')
        
        # Wait 5 minutes before next ping (Render spins down after 15 min of inactivity)
        time.sleep(5 * 60)

# Start keep-alive thread when app starts (only in production/Render)
if os.getenv('FLASK_ENV') == 'production' or os.getenv('RENDER') == 'true' or os.getenv('RENDER_EXTERNAL_URL'):
    keep_alive_thread = threading.Thread(target=keep_alive_ping, daemon=True)
    keep_alive_thread.start()
    app.logger.info('Keep-alive thread started to prevent Render spin-down')

@app.route('/api/version', methods=['GET'])
def get_app_version():
    """Get the current application version"""
    return jsonify({'version': get_version()}), 200

@app.route('/api/init-db', methods=['POST'])
@jwt_required()
def init_db_endpoint():
    """Manual database initialization endpoint (requires authentication)"""
    try:
        initialize_database()
        return {'status': 'success', 'message': 'Database initialized successfully'}, 200
    except Exception as e:
        return {'status': 'error', 'message': str(e)}, 500

if __name__ == '__main__':
    # Database initialization is already done above (line 173)
    # This block is only for local development
    print("=" * 50)
    print("Backend server starting...")
    print("Server will run on: http://127.0.0.1:5001")
    print("API endpoints available at: http://127.0.0.1:5001/api")
    print("Health check: http://127.0.0.1:5001/api/health")
    print("=" * 50)
    app.run(debug=True, port=5001, host='127.0.0.1')

