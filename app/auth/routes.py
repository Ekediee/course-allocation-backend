from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, jwt_required, get_jwt_identity, current_user, set_access_cookies
)
from app.models import User
from app import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()
    print(f"User found: {user.email}")
    if not user or not user.check_password(password):
        return jsonify({"msg": "Invalid credentials"}), 401

    token = create_access_token(identity=str(user.id))
    resp = jsonify({
        "access_token": token,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "department": user.lecturer.department.name,
            "rank": user.lecturer.rank,
            "qualification": user.lecturer.qualification
        }
    })
    set_access_cookies(resp, token)
    return resp

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_me():
    # user_id = get_jwt_identity()
    # user = User.query.get(user_id)

    return jsonify({
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role,
        "department": current_user.lecturer.department.name,
        "rank": current_user.lecturer.rank,
        "qualification": current_user.lecturer.qualification
    }), 200
