import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    # ── Core ──────────────────────────────────────────────────────────────────
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'change-me-in-production-use-a-long-random-string'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///voting.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ── Session / Cookie security ─────────────────────────────────────────────
    SESSION_COOKIE_HTTPONLY  = True   # JS cannot read the cookie
    SESSION_COOKIE_SAMESITE  = 'Lax' # CSRF mitigation
    SESSION_COOKIE_SECURE    = False  # Set True when behind HTTPS in production
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)  # auto-logout

    # ── CSRF ──────────────────────────────────────────────────────────────────
    WTF_CSRF_ENABLED     = True
    WTF_CSRF_TIME_LIMIT  = 3600  # 1 hour

    # ── Rate limiting ─────────────────────────────────────────────────────────
    RATELIMIT_DEFAULT          = "200 per day;50 per hour"
    RATELIMIT_STORAGE_URL      = "memory://"
    RATELIMIT_STRATEGY         = "fixed-window"

    # ── Mail (optional – for OTP / notifications) ─────────────────────────────
    MAIL_SERVER   = os.environ.get('MAIL_SERVER',   'smtp.gmail.com')
    MAIL_PORT     = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS  = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@votingsystem.com')

    # ── Upload ────────────────────────────────────────────────────────────────
    UPLOAD_FOLDER    = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024   # 2 MB max upload
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


class ProductionConfig(Config):
    SESSION_COOKIE_SECURE = True   # enforce HTTPS cookies
    DEBUG = False


class DevelopmentConfig(Config):
    DEBUG = True


config = {
    'development': DevelopmentConfig,
    'production':  ProductionConfig,
    'default':     DevelopmentConfig,
}
