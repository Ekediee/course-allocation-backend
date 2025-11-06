from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, current_user
from app.services.admin_user_service import get_all_admin_users, create_admin_user, create_admin_users_batch
from app.models.models import AppSetting
from app.extensions import db

admin_user_bp = Blueprint('admin_users', __name__, url_prefix='/api/v1/admin')

@admin_user_bp.route('/users', methods=['GET'])
@jwt_required()
def handle_get_admin_users():
    if not current_user or not (current_user.is_vetter or current_user.is_superadmin):
        return jsonify({"msg": "Unauthorized"}), 403
        
    users, error = get_all_admin_users()
    if error:
        return jsonify({'error': error}), 500
    return jsonify({"users": users}), 200

@admin_user_bp.route('/users', methods=['POST'])
@jwt_required()
def handle_create_admin_user():
    if not current_user or not (current_user.is_vetter or current_user.is_superadmin):
        return jsonify({"msg": "Unauthorized"}), 403

    data = request.get_json()
    if not data or not all(k in data for k in ['name', 'email', 'role', 'department_id', 'gender', 'phone']):
        return jsonify({'error': 'Missing required fields'}), 400
    
    if data['role'] not in ['admin', 'vetter', 'superadmin']:
        return jsonify({'error': 'Invalid role specified'}), 400
    
    new_user, password, error = create_admin_user(data)
    if error:
        return jsonify({'error': error}), 400
        
    return jsonify({
        "msg": f"User created successfully - temporary password is {password}",
        "user": new_user
    }), 201

@admin_user_bp.route('/users/batch', methods=['POST'])
@jwt_required()
def handle_create_admin_users_batch():
    if not current_user or not current_user.is_superadmin:
        return jsonify({"msg": "Unauthorized"}), 403

    data = request.get_json()
    if not data or 'users' not in data:
        return jsonify({"error": "Invalid data"}), 400
    
    count, errors = create_admin_users_batch(data['users'])
    if errors:
        return jsonify({
            "msg": f"Batch user creation successful with {count} created.",
            "errors": errors
        }), 207 # 207 Multi-Status

    return jsonify({
        "msg": "Batch user creation successful",
        "count": count
    }), 201

@admin_user_bp.route('/maintenance-mode', methods=['POST'])
@jwt_required()
def set_maintenance_mode():
    """
    Sets the application's maintenance mode. Expects JSON: {"enable": true/false}.
    """

    if not current_user.is_superadmin:
        return jsonify({"msg": "Unauthorized"}), 403
    
    data = request.get_json()
    enable = data.get('enable')

    if enable is None or not isinstance(enable, bool):
        return jsonify({"error": "Missing or invalid 'enable' field. Must be true or false."}), 400

    # Find the setting, or create it if it doesn't exist
    setting = AppSetting.query.filter_by(setting_name='maintenance_mode').first()
    if not setting:
        setting = AppSetting(setting_name='maintenance_mode')
        db.session.add(setting)

    setting.is_enabled = enable
    db.session.commit()

    return jsonify({"message": f"Maintenance mode has been {'enabled' if enable else 'disabled'}."}), 200

@admin_user_bp.route('/maintenance-status', methods=['GET'])
def get_maintenance_status():
    """
    Returns the current maintenance status of the application. Publicly accessible.
    """
    setting = AppSetting.query.filter_by(setting_name='maintenance_mode').first()
    
    # If the setting doesn't exist in the DB, default to false (not in maintenance)
    is_maintenance = setting.is_enabled if setting else False
    
    return jsonify({"isMaintenanceMode": is_maintenance})
