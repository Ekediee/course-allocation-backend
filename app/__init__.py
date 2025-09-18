from flask import Flask
from flask_migrate import Migrate
from flask_cors import CORS
from .config import config
# from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from app.models import models
from .jwt_config import jwt
from .extensions import db, mail

migrate = Migrate()
# jwt = JWTManager()

def create_app(config_name='default'):
    app = Flask(__name__)
    app.json.sort_keys = False
    
    bcrypt = Bcrypt(app)
    app.config.from_object(config[config_name])

    db.init_app(app)
    mail.init_app(app)

    migrate.init_app(app, db)
    CORS(app, supports_credentials=True)  # Enable CORS with credentials support

    # Initialize JWT
    jwt.init_app(app)

    @jwt.user_lookup_loader
    def user_lookup_loader(_jwt_header, jwt_data):
        identity = jwt_data["sub"]
        return db.session.get(models.User, int(identity))

    # Explicitly set JWT config after init_app for testing
    if config_name == 'testing': # Apply only for testing config
        app.config['JWT_TOKEN_LOCATION'] = ["headers"]
        app.config['JWT_COOKIE_CSRF_PROTECT'] = False
        app.config['JWT_COOKIE_SECURE'] = False

    # Import and register blueprints here
    from app.auth.routes import auth_bp
    from app.auth.umis_login import umis_auth_bp
    from app.routes.session_routes import session_bp
    from app.routes.semester_routes import semester_bp
    from app.routes.level_route import level_bp
    from app.routes.school_routes import school_bp
    from app.routes.department_routes import department_bp
    from app.routes.program_routes import program_bp
    from app.routes.bulletin_route import bulletin_bp
    from app.routes.allocation_routes import allocation_bp
    from app.routes.specialization_routes import specialization_bp
    from app.routes.course_routes import course_bp
    from app.routes.user_routes import user_bp
    from app.routes.admin_user_routes import admin_user_bp
    from app.routes.course_type_routes import course_type_bp

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    app.register_blueprint(umis_auth_bp, url_prefix='/api/v1/auth/umis')
    app.register_blueprint(session_bp, url_prefix='/api/v1/sessions')
    app.register_blueprint(specialization_bp, url_prefix='/api/v1/specializations')
    app.register_blueprint(course_bp, url_prefix='/api/v1/courses')
    app.register_blueprint(semester_bp, url_prefix='/api/v1/semesters')
    app.register_blueprint(level_bp, url_prefix='/api/v1/levels')
    app.register_blueprint(school_bp, url_prefix='/api/v1/schools')
    app.register_blueprint(department_bp, url_prefix='/api/v1/departments')
    app.register_blueprint(program_bp, url_prefix='/api/v1/programs')
    app.register_blueprint(bulletin_bp, url_prefix='/api/v1/bulletins')
    app.register_blueprint(allocation_bp, url_prefix='/api/v1/allocation')
    app.register_blueprint(user_bp, url_prefix='/api/v1/users')
    app.register_blueprint(admin_user_bp)
    app.register_blueprint(course_type_bp, url_prefix='/api/v1/course-types')

    return app
