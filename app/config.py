import os
from dotenv import load_dotenv
load_dotenv()
from datetime import timedelta

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    LOG_FILE = "app.log"

    # Email configuration
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.googlemail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER')
    JWT_TOKEN_LOCATION = ["cookies"]
    # Use secure cookies (set to True in production)
    JWT_COOKIE_SECURE = False  # True if using HTTPS
    # Enable HttpOnly for security
    # JWT_COOKIE_HTTPONLY = True
    JWT_ACCESS_COOKIE_NAME = "access_token_cookie"
    # Optional: CSRF protection (good to use in production)
    JWT_COOKIE_CSRF_PROTECT = False  # You can turn it on if needed
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=3)

class ProductionConfig(Config):
    JWT_COOKIE_SECURE = True
    JWT_COOKIE_CSRF_PROTECT = True

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    JWT_SECRET_KEY = 'super-secret-testing-key'
    JWT_COOKIE_CSRF_PROTECT = False
    JWT_TOKEN_LOCATION = ["headers"]

config = {
    'development': Config,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': Config
}