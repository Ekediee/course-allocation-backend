from flask_jwt_extended import jwt_required, current_user
from flask import Blueprint, request, jsonify
from app import db
from app.models.models import Department


department_bp = Blueprint('departments', __name__)

@department_bp.route('/create', methods=['POST'])
@jwt_required()
def create_department():

    if not current_user or not (current_user.is_superadmin or current_user.is_vetter):
        return jsonify({"msg": "Unauthorized – Only superadmin can create departments"}), 403

    data = request.get_json()
    name = data.get('name')
    school_id = data.get('school_id')
    acronym = data.get('acronym')

    

    if not name:
        return jsonify({'error': 'Department name is required'}), 400

    if Department.query.filter_by(name=name).first():
        return jsonify({'error': f"Department - '{name}' already exists"}), 400

    # Create new school
    new_department = Department(name=name, school_id=school_id, acronym=acronym)
    db.session.add(new_department)
    db.session.flush()

    db.session.commit()
    
    return jsonify({
        "msg": f"School '{name}' created and activated successfully",
        "bulletin": {
            "id": new_department.id,
            "name": new_department.name,
            "school_id": new_department.school_id,
            "acronym": new_department.acronym
        }
    }), 201


@department_bp.route('/list', methods=['GET'])
@jwt_required()
def get_departments():

    if not current_user or not (current_user.is_superadmin or current_user.is_vetter):
        return jsonify({"msg": "Unauthorized – Only superadmin can fetch departments"}), 403

    departments = Department.query.order_by(Department.id).filter(Department.name.notin_(['Registry', 'Academic Planning'])).all()
    
    return jsonify({
        "departments": [
            {
                "id": department.id,
                "name": department.name,
                "school": department.school.name,
                "acronym": department.acronym
            } for department in departments
        ]
    }), 200

@department_bp.route('/list/admin', methods=['GET'])
@jwt_required()
def get_admin_departments():

    if not current_user or not (current_user.is_superadmin or current_user.is_vetter):
        return jsonify({"msg": "Unauthorized – Only superadmin can fetch departments"}), 403

    departments = Department.query.order_by(Department.id).filter(Department.name.in_(['Registry', 'Academic Planning'])).all()
    
    return jsonify({
        "departments": [
            {
                "id": department.id,
                "name": department.name,
                "school": department.school.name,
                "acronym": department.acronym
            } for department in departments
        ]
    }), 200

@department_bp.route('/lists', methods=['GET'])
@jwt_required()
def get_departments_names():

    if not current_user or not (current_user.is_superadmin or current_user.is_vetter):
        return jsonify({"msg": "Unauthorized – Only superadmin can fetch departments"}), 403
    
    departments = Department.query.order_by(Department.id).all()
    
    return jsonify({
        "departments": [
            {
                "id": department.id,
                "name": department.name,
            } for department in departments
        ]
    }), 200

@department_bp.route('/names/list', methods=['POST'])
@jwt_required()
def get_departments_names_by_school():

    if not current_user or not (current_user.is_superadmin or current_user.is_vetter):
        return jsonify({"msg": "Unauthorized – Only superadmin can fetch departments"}), 403

    data = request.get_json()
    school_id = data.get('school_id')
    
    departments = Department.query.filter_by(school_id=school_id).all()
    
    return jsonify({
        "departments": [
            {
                "id": department.id,
                "name": department.name,
            } for department in departments
        ]
    }), 200

@department_bp.route('/batch', methods=['POST'])
@jwt_required()
def batch_upload():

    if not current_user or not (current_user.is_superadmin or current_user.is_vetter):
        return jsonify({"error": "Unauthorized – Only superadmin can create departments"}), 403
    
    data = request.get_json()

    
    departments = data.get('departments', [])

    created = []
    for dept in departments:
        name = dept.get('name')
        school_id = dept.get('school_id')
        acronym = dept.get('acronym')
        if name and acronym:
            department = Department(name=name, school_id=school_id, acronym=acronym)
            db.session.add(department)
            created.append(name)

    db.session.commit()

    return jsonify({
        "message": f"Successfully uploaded {len(created)} schools.",
        "departments_created": created
    })

@department_bp.route('/update/<int:id>', methods=['PUT'])
@jwt_required()
def update_department(id):
    if not current_user or not (current_user.is_superadmin or current_user.is_vetter):
        return jsonify({"msg": "Unauthorized – Only superadmin can update departments"}), 403

    department = Department.query.get(id)
    if not department:
        return jsonify({'error': 'Department not found'}), 404

    data = request.get_json()
    name = data.get('name')
    school_id = data.get('school_id')
    acronym = data.get('acronym')

    if not name:
        return jsonify({'error': 'Department name is required'}), 400

    department.name = name
    department.school_id = school_id
    department.acronym = acronym

    db.session.commit()

    return jsonify({'message': 'Department updated successfully'}), 200

@department_bp.route('/delete/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_department(id):
    if not current_user or not (current_user.is_superadmin or current_user.is_vetter):
        return jsonify({"msg": "Unauthorized – Only superadmin can delete departments"}), 403

    department = Department.query.get(id)
    if not department:
        return jsonify({'error': 'Department not found'}), 404

    db.session.delete(department)
    db.session.commit()

    return jsonify({'message': 'Department deleted successfully'}), 200