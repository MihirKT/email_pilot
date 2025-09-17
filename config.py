import os
from dotenv import load_dotenv

load_dotenv()
# Get the absolute path of the directory where this file is located
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "a-very-secret-key-that-you-should-change")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    SESSION_TYPE = 'filesystem'
    SESSION_FILE_DIR = os.path.join(basedir, 'flask_session')
    SESSION_PERMANENT = True
    SESSION_USE_SIGNER = True
    SESSION_KEY_PREFIX = 'email_outreach:'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 3600

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    # Use the 'basedir' to create an absolute path to the database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'instance', 'templates-dev.db')
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    SESSION_COOKIE_SECURE = False

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    # For production, DATABASE_URL should be a full URL to a production DB (e.g., Postgres)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SESSION_COOKIE_SECURE = True

# Create session directory if it doesn't exist
os.makedirs(Config.SESSION_FILE_DIR, exist_ok=True)
