from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, current_user
from app.services.course_service import get_all_courses, create_course, batch_create_courses

course_bp = Blueprint('courses', __name__)

@course_bp.route('', methods=['GET'])
@jwt_required()
def handle_get_all_courses():
    if not current_user:
        return jsonify({"msg": "Unauthorized"}), 403

    courses = get_all_courses()
    response_data = [
        {
            "id": pc.course.id,
            "code": pc.course.code,
            "title": pc.course.title,
            "unit": pc.course.units,
            "program": {
                "id": pc.program.id,
                "name": pc.program.name
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

    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    bulletin_id = request.form.get('bulletin_id')
    program_id = request.form.get('program_id')
    semester_id = request.form.get('semester_id')
    level_id = request.form.get('level_id')
    specialization_id = request.form.get('specialization_id')

    if not all([bulletin_id, program_id, semester_id, level_id]):
        return jsonify({'error': 'Missing required form fields'}), 400

    created_count, errors = batch_create_courses(file, bulletin_id, program_id, semester_id, level_id, specialization_id)

    if errors:
        return jsonify({"message": f"Processed with {len(errors)} errors.", "errors": errors}), 400

    return jsonify({"message": f"Successfully created {created_count} courses."}), 200
