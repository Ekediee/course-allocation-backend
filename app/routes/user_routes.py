from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, current_user
from app.services.user_service import get_all_users, create_user, create_users_batch

user_bp = Blueprint('users', __name__)


@user_bp.route('', methods=['GET'])
@jwt_required()
def handle_get_users():
    if not current_user:
        return jsonify({"msg": "Unauthorized"}), 403
        
    users, error = get_all_users()
    if error:
        return jsonify({'error': error}), 500
    return jsonify({"users": users}), 200

@user_bp.route('', methods=['POST'])
@jwt_required()
def handle_create_user():
    if not current_user or not (current_user.is_superadmin or current_user.is_vetter):
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json()
    if not data or not all(k in data for k in ['name', 'email', 'role', 'department_id']):
        return jsonify({'error': 'Missing required fields'}), 400

    new_user, error = create_user(data)
    if error:
        return jsonify({'error': error}), 500
        
    return jsonify({
        "msg": "User created successfully",
        "user": new_user
    }), 201

@user_bp.route('/batch', methods=['POST'])
@jwt_required()
def handle_create_users_batch():
    if not current_user or not (current_user.is_superadmin or current_user.is_vetter):
        return jsonify({"msg": "Unauthorized"}), 403

    data = request.get_json()
    if not data or 'users' not in data:
        return jsonify({"error": "Invalid data"}), 400
    
    count, errors = create_users_batch(data['users'])
    if errors:
        return jsonify({
            "message": f"Successfully created {count} users with some errors.",
            "errors": errors
        }), 400

    return jsonify({
        "message": f"Successfully created {count} users."
    }), 201