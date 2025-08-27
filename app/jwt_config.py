# app/jwt_config.py
from flask_jwt_extended import JWTManager


jwt = JWTManager()

@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    from app.models import User
    from app.extensions import db
    identity = jwt_data["sub"]
    return db.session.get(User, int(identity))
