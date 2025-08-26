from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, current_user
from app.services.specialization_service import (
    create_specialization,
    get_specializations,
    get_specialization_names_by_program,
    batch_create_specializations,
)

specialization_bp = Blueprint('specializations', __name__)

@specialization_bp.route('/create', methods=['POST'])
@jwt_required()
def handle_create_specialization():
    if not current_user or not (current_user.is_superadmin or current_user.is_vetter):
        return jsonify({"msg": "Unauthorized"}), 403

    data = request.get_json()
    name = data.get('name')
    program_id = data.get('program_id')

    if not name or not program_id:
        return jsonify({'error': 'Specialization name and program_id are required'}), 400

    specialization, error = create_specialization(name, program_id)

    if error:
        return jsonify({'error': error}), 400

    return jsonify({
        "msg": f"Specialization '{name}' created successfully",
        "specialization": {
            "id": specialization.id,
            "name": specialization.name,
            "program_id": specialization.program_id
        }
    }), 201

@specialization_bp.route('/list', methods=['GET'])
@jwt_required()
def handle_get_specializations():
    if not current_user or not (current_user.is_superadmin or current_user.is_vetter):
        return jsonify({"msg": "Unauthorized"}), 403

    specializations = get_specializations()
    
    return jsonify({
        "specializations": [
            {
                "id": spec.id,
                "name": spec.name,
                "program": spec.program.name,
                "department": spec.program.department.name,
            } for spec in specializations
        ]
    }), 200

@specialization_bp.route('/names/list', methods=['POST'])
@jwt_required()
def handle_get_specialization_names():
    if not current_user or not (current_user.is_superadmin or current_user.is_vetter or current_user.is_hod):
        return jsonify({"msg": "Unauthorized"}), 403

    data = request.get_json()
    program_id = data.get('program_id')
    
    if not program_id:
        return jsonify({'error': 'program_id is required'}), 400

    specializations = get_specialization_names_by_program(program_id)
    
    return jsonify({
        "specializations": [
            {
                "id": spec.id,
                "name": spec.name,
            } for spec in specializations
        ]
    }), 200

@specialization_bp.route('/batch-upload', methods=['POST'])
@jwt_required()
def handle_batch_upload():
    if not current_user or not (current_user.is_superadmin or current_user.is_vetter):
        return jsonify({"error": "Unauthorized"}), 403
    
    data = request.get_json()
    specializations = data.get('specializations', [])

    if not specializations:
        return jsonify({'error': 'No specializations data provided'}), 400

    created_count, errors = batch_create_specializations(specializations)

    response = {
        "message": f"Successfully created {created_count} specializations."
    }
    if errors:
        response["errors"] = errors

    return jsonify(response), 201
