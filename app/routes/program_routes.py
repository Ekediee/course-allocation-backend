from flask_jwt_extended import jwt_required, current_user
from flask import Blueprint, request, jsonify
from app import db
from app.models.models import Program, Department


program_bp = Blueprint('programs', __name__)

@program_bp.route('/create', methods=['POST'])
@jwt_required()
def create_program():

    if not current_user or not (current_user.is_superadmin or current_user.is_vetter):
        return jsonify({"msg": "Unauthorized – Only superadmin can create programs"}), 403

    data = request.get_json()
    name = data.get('name')
    department_id = data.get('department_id')
    acronym = data.get('acronym')

    

    if not name:
        return jsonify({'error': 'Program name is required'}), 400

    if Program.query.filter_by(name=name).first():
        return jsonify({'error': f"Program - '{name}' already exists"}), 400

    # Create new program
    new_program = Program(name=name, department_id=department_id, acronym=acronym)
    db.session.add(new_program)
    db.session.flush()

    db.session.commit()
    
    return jsonify({
        "msg": f"School '{name}' created and activated successfully",
        "bulletin": {
            "id": new_program.id,
            "name": new_program.name,
            "department_id": new_program.department_id,
            "acronym": new_program.acronym
        }
    }), 201


@program_bp.route('/list', methods=['GET'])
@jwt_required()
def get_programs():

    if not current_user or not (current_user.is_superadmin or current_user.is_vetter or current_user.is_hod):
        return jsonify({"msg": "Unauthorized – Only superadmin can fetch programs"}), 403

    programs = Program.query.order_by(Program.id).all()
    
    return jsonify({
        "programs": [
            {
                "id": program.id,
                "name": program.name,
                "department": program.department.name,
                "acronym": program.acronym
            } for program in programs
        ]
    }), 200

@program_bp.route('/department-list', methods=['POST'])
@jwt_required()
def get_programs_by_department():

    if not current_user or not (current_user.is_superadmin or current_user.is_vetter or current_user.is_hod):
        return jsonify({"msg": "Unauthorized – Only superadmin can fetch programs"}), 403
    
    data = request.get_json()
    department_name = data.get('department')

    department = Department.query.filter_by(name=department_name).first()

    programs = Program.query.filter_by(department_id=department.id).all()
    
    return jsonify({
        "programs": [
            {
                "id": program.id,
                "name": program.name,
                "department": program.department.name,
                "acronym": program.acronym
            } for program in programs
        ]
    }), 200

# @program_bp.route('/lists', methods=['GET'])
# @jwt_required()
# def get_departments_names():

#     if not current_user or not (current_user.is_superadmin or current_user.is_vetter):
#         return jsonify({"msg": "Unauthorized – Only superadmin can fetch departments"}), 403

#     departments = Department.query.order_by(Department.id).all()
    
#     return jsonify({
#         "departments": [
#             {
#                 "id": department.id,
#                 "name": department.name,
#             } for department in departments
#         ]
#     }), 200

@program_bp.route('/names/list', methods=['POST'])
@jwt_required()
def get_program_by_department():

    if not current_user or not (current_user.is_superadmin or current_user.is_vetter):
        return jsonify({"msg": "Unauthorized – Only superadmin can fetch departments"}), 403

    data = request.get_json()
    department_id = data.get('department_id')
    
    programs = Program.query.filter_by(department_id=department_id).all()
    
    return jsonify({
        "programs": [
            {
                "id": program.id,
                "name": program.name,
            } for program in programs
        ]
    }), 200

@program_bp.route('/batch', methods=['POST'])
@jwt_required()
def batch_upload():

    if not current_user or not (current_user.is_superadmin or current_user.is_vetter):
        return jsonify({"error": "Unauthorized – Only superadmin can create programs"}), 403
    
    data = request.get_json()

    
    programs = data.get('programs', [])

    created = []
    for prog in programs:
        name = prog.get('name')
        department_id = prog.get('department_id')
        acronym = prog.get('acronym')
        if name and acronym:
            program = Program(name=name, department_id=department_id, acronym=acronym)
            db.session.add(program)
            created.append(name)

    db.session.commit()

    return jsonify({
        "message": f"Successfully uploaded {len(created)} programs.",
        "programs_created ": created
    })
