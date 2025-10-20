from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, current_user
from app.services.user_service import get_all_users, create_user, create_users_batch, update_user, delete_user
import re

user_bp = Blueprint('users', __name__)

def _simplify_db_error(err):
    s = str(err)
    # match MySQL duplicate entry message
    m = re.search(r"Duplicate entry '([^']+)' for key '([^']+)'", s)
    if m:
        return f"Duplicate entry '{m.group(1)}' for key '{m.group(2)}'"
    # fallback: return first non-empty line
    for line in s.splitlines():
        line = line.strip()
        if line:
            return line
    return s

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
    
    if errors and any(errors):
        cleaned = [_simplify_db_error(e) for e in errors]
        errors_str = "\n".join(cleaned)
        return jsonify({
            "message": f"Successfully created {count} users with some errors.",
            "errors": f"The following conflicts were detected:\n\n{errors_str}"
        }), 400


    return jsonify({
        "message": f"Successfully created {count} users."
    }), 201

@user_bp.route('/<int:user_id>', methods=['PUT'])
@jwt_required()
def handle_update_user(user_id):
    if not current_user or not (current_user.is_superadmin or current_user.is_vetter):
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Missing required fields'}), 400

    updated_user, error = update_user(user_id, data)
    if error:
        if error == "User not found":
            return jsonify({'error': error}), 404
        return jsonify({'error': error}), 500
        
    return jsonify({
        "msg": "User updated successfully",
        "user": updated_user
    }), 200

@user_bp.route('/<int:user_id>', methods=['DELETE'])
@jwt_required()
def handle_delete_user(user_id):
    if not current_user or not (current_user.is_superadmin or current_user.is_vetter):
        return jsonify({"error": "Unauthorized"}), 403

    success, error = delete_user(user_id)
    if error:
        if error == "User not found":
            return jsonify({'error': error}), 404
        return jsonify({'error': error}), 500
        
    return jsonify({"msg": "User deleted successfully"}), 200
