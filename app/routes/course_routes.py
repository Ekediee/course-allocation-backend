from flask import Blueprint, current_app, request, jsonify
from flask_jwt_extended import jwt_required, current_user
from app.services import course_service
from app.services.course_service import get_all_courses, create_course, batch_create_courses, update_course, delete_course
from .user_routes import _simplify_db_error

course_bp = Blueprint('courses', __name__)

@course_bp.route('', methods=['GET'])
@jwt_required()
def handle_get_all_courses():
    if not current_user:
        return jsonify({"msg": "Unauthorized"}), 403

    courses = get_all_courses()
    response_data = [
        {
            "program_course_id": pc.id,
            "id": pc.course.id,
            "code": pc.course.code,
            "title": pc.course.title,
            "unit": pc.course.units,
            "course_type": {
                "id": pc.course.course_type.id if pc.course.course_type else None,
                "name": pc.course.course_type.name if pc.course.course_type else None
            },
            "program": {
                "id": pc.program.id,
                "name": pc.program.name,
                "department": {
                    "id": pc.program.department.id,
                    "name": pc.program.department.name,
                    "school": {
                        "id": pc.program.department.school.id,
                        "name": pc.program.department.school.name
                    }
                }
            },
            "specialization": {
                "id": pc.specializations[0].id if pc.specializations else None,
                "name": pc.specializations[0].name if pc.specializations else 'General'
            },
            "bulletin": {
                "id": pc.bulletin.id,
                "name": pc.bulletin.name
            },
            "level": {
                "id": pc.level.id,
                "name": pc.level.name
            },
            "semester": {
                "id": pc.semester.id,
                "name": pc.semester.name
            }
        } for pc in courses
    ]

    return jsonify({"courses": response_data}), 200

@course_bp.route('', methods=['POST'])
@jwt_required()
def handle_create_course():
    if not current_user or not (current_user.is_superadmin or current_user.is_vetter):
        return jsonify({"msg": "Unauthorized"}), 403

    data = request.get_json()
    if not data or not all(k in data for k in ['code', 'title', 'unit', 'program_id', 'level_id', 'semester_id', 'bulletin_id']):
        return jsonify({'error': 'Missing required fields'}), 400

    course, error = create_course(data)

    if error:
        return jsonify({'error': error}), 409

    return jsonify({
        "msg": "Course created successfully.",
        "course": {
            "id": course.id,
            "code": course.code,
            "title": course.title,
            "unit": course.units
        }
    }), 201

@course_bp.route('/batch', methods=['POST'])
@jwt_required()
def handle_batch_create_courses():
    if not current_user or not (current_user.is_superadmin or current_user.is_vetter):
        return jsonify({"msg": "Unauthorized"}), 403
    
    data = request.get_json()
    courses_data = data.get('courses', [])
    
    bulletin_id = courses_data[0].get('bulletin_id')
    program_id = courses_data[0].get('program_id')
    semester_id = courses_data[0].get('semester_id')
    level_id = courses_data[0].get('level_id')

    if not courses_data:
        return jsonify({'error': 'No courses data provided'}), 400
    
    if not all([bulletin_id, program_id, semester_id, level_id]):
        return jsonify({'error': 'Missing required fields: bulletin_id, program_id, semester_id, level_id'}), 400
   
    created_count, errors = batch_create_courses(courses_data)

    if errors and any(errors):
        cleaned = [_simplify_db_error(e) for e in errors]
        errors_str = "\n".join(cleaned)

        return jsonify({
        "message": f"Successfully created {created_count} courses.",
        "errors": f"The following conflicts were detected:\n\n{errors_str}"
    }), 400

    return jsonify({
        "message": f"Successfully created {created_count} courses."
    }), 201

@course_bp.route('/<int:program_course_id>', methods=['PUT'])
@jwt_required()
def handle_update_course(program_course_id):
    if not current_user or not (current_user.is_superadmin or current_user.is_vetter):
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid data provided'}), 400

    updated_course, error = update_course(program_course_id, data)

    if error:
        # Resource not found
        if "not found" in error:
            return jsonify({"msg": error}), 404
    
    # Manually construct the response to match the format in the prompt
    response_data = {
        "id": updated_course.course.id,
        "code": updated_course.course.code,
        "title": updated_course.course.title,
        "unit": updated_course.course.units,
        "program": {
            "id": updated_course.program.id,
            "name": updated_course.program.name,
            "department": {
                "id": updated_course.program.department.id,
                "name": updated_course.program.department.name,
                "school": {
                    "id": updated_course.program.department.school.id,
                    "name": updated_course.program.department.school.name
                }
            }
        },
        "level": {
            "id": updated_course.level.id,
            "name": updated_course.level.name
        },
        "semester": {
            "id": updated_course.semester.id,
            "name": updated_course.semester.name
        },
        "specialization": {
            "id": updated_course.specializations[0].id if updated_course.specializations else None,
            "name": updated_course.specializations[0].name if updated_course.specializations else 'General'
        },
        "bulletin": {
            "id": updated_course.bulletin.id,
            "name": updated_course.bulletin.name
        },
        "course_type": {
            "id": updated_course.course.course_type.id if updated_course.course.course_type else None,
            "name": updated_course.course.course_type.name if updated_course.course.course_type else None
        }
    }

    return jsonify(response_data), 200

@course_bp.route('/<int:program_course_id>', methods=['DELETE'])
@jwt_required()
def handle_delete_course(program_course_id):
    if not current_user or not (current_user.is_superadmin or current_user.is_vetter):
        return jsonify({"error": "Unauthorized"}), 403

    success, error = delete_course(program_course_id)

    if error:
        if error == "Program course not found":
            return jsonify({'error': 'Course not found'}), 404
        return jsonify({'error': error}), 500
        
    return '', 204

@course_bp.route('/department-courses', methods=['POST'])
@jwt_required()
def get_courses_by_department_route():
    """
     Gets all course courses for a given department and semester,
     organized by program and level.
    """
    if not (current_user.is_superadmin or current_user.is_vetter):
        return jsonify({"error": "Unauthorized: Only superadmins and vetters can view this."}), 403
    
    data = request.get_json()
    department_id = data.get('department')
    semester_id = data.get('semester')

    if not department_id or not semester_id:
        return jsonify({"error": "department_id and semester_id are required."}), 400

    courses, error = course_service.get_courses_by_department(department_id, semester_id)

    if error:
        return jsonify({"error": error}), 400

    return jsonify(courses)
