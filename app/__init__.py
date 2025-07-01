from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from .config import Config
# from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from .jwt_config import jwt

db = SQLAlchemy()
migrate = Migrate()
# jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    bcrypt = Bcrypt(app)
    app.config.from_object(Config)

    db.init_app(app)
    from app.models import models  # Import models to register them with SQLAlchemy

    migrate.init_app(app, db)
    CORS(app)

    # Initialize JWT
    jwt.init_app(app)

    # Import and register blueprints here
    from app.auth.routes import auth_bp
    from app.routes.session_routes import session_bp
    from app.routes.allocation_routes import allocation_bp

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    app.register_blueprint(session_bp, url_prefix='/api/v1/sessions')
    app.register_blueprint(allocation_bp, url_prefix='/api/v1/allocation')

    return app
