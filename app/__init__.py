from flask import Flask
from flask_migrate import Migrate
from flask_cors import CORS
from .config import config
# from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from app.models import models
from .jwt_config import jwt
from .extensions import db

migrate = Migrate()
# jwt = JWTManager()

def create_app(config_name='default'):
    app = Flask(__name__)
    app.json.sort_keys = False
    
    bcrypt = Bcrypt(app)
    app.config.from_object(config[config_name])

    db.init_app(app)

    migrate.init_app(app, db)
    CORS(app, supports_credentials=True)  # Enable CORS with credentials support

    # Initialize JWT
    jwt.init_app(app)

    # Explicitly set JWT config after init_app for testing
    if config_name == 'testing': # Apply only for testing config
        app.config['JWT_TOKEN_LOCATION'] = ["headers"]
        app.config['JWT_COOKIE_CSRF_PROTECT'] = False
        app.config['JWT_COOKIE_SECURE'] = False

    # Import and register blueprints here
    from app.auth.routes import auth_bp
    from app.routes.session_routes import session_bp
    from app.routes.semester_routes import semester_bp
    from app.routes.level_route import level_bp
    from app.routes.school_routes import school_bp
    from app.routes.department_routes import department_bp
    from app.routes.program_routes import program_bp
    from app.routes.bulletin_route import bulletin_bp
    from app.routes.allocation_routes import allocation_bp

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    app.register_blueprint(session_bp, url_prefix='/api/v1/sessions')
    app.register_blueprint(semester_bp, url_prefix='/api/v1/semesters')
    app.register_blueprint(level_bp, url_prefix='/api/v1/levels')
    app.register_blueprint(school_bp, url_prefix='/api/v1/schools')
    app.register_blueprint(department_bp, url_prefix='/api/v1/departments')
    app.register_blueprint(program_bp, url_prefix='/api/v1/programs')
    app.register_blueprint(bulletin_bp, url_prefix='/api/v1/bulletins')
    app.register_blueprint(allocation_bp, url_prefix='/api/v1/allocation')

    return app