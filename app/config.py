import os
from dotenv import load_dotenv
load_dotenv()
from datetime import timedelta

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    JWT_TOKEN_LOCATION = ["cookies"]
    # Use secure cookies (set to True in production)
    JWT_COOKIE_SECURE = False  # True if using HTTPS
    # Enable HttpOnly for security
    # JWT_COOKIE_HTTPONLY = True
    JWT_ACCESS_COOKIE_NAME = "access_token_cookie"
    # Optional: CSRF protection (good to use in production)
    JWT_COOKIE_CSRF_PROTECT = False  # You can turn it on if needed
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=2)
