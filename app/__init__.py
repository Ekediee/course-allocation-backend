from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from .config import Config

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    from app.models import models  # Import models to register them with SQLAlchemy

    migrate.init_app(app, db)
    CORS(app)

    # Import and register blueprints here
    from app.routes.session_routes import session_bp

    # Register blueprints
    app.register_blueprint(session_bp)

    return app
