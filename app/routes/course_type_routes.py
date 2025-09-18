from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, current_user
from app import db
from app.models.models import CourseType

course_type_bp = Blueprint('course_types', __name__)

@course_type_bp.route('/create', methods=['POST'])
@jwt_required()
def create_course_type():
    if not current_user or not (current_user.is_superadmin or current_user.is_vetter):
        return jsonify({"msg": "Unauthorized – Only superadmin or vetter can create course types"}), 403

    data = request.get_json()
    name = data.get('name')

    if not name:
        return jsonify({'error': 'Name is required'}), 400

    if CourseType.query.filter_by(name=name).first():
        return jsonify({'error': 'Course type with this name already exists'}), 409

    new_course_type = CourseType(name=name)
    db.session.add(new_course_type)
    db.session.commit()

    return jsonify({
        "msg": "Course type created successfully",
        "course_type": {
            "id": new_course_type.id,
            "name": new_course_type.name
        }
    }), 201

@course_type_bp.route('/list', methods=['GET'])
@jwt_required()
def get_course_types():
    if not current_user or not (current_user.is_superadmin or current_user.is_vetter or current_user.is_hod):
        return jsonify({"msg": "Unauthorized"}), 403
        
    course_types = CourseType.query.order_by(CourseType.name).all()
    
    return jsonify(
        [
            {
                "id": course_type.id,
                "name": course_type.name,
            } for course_type in course_types
        ]
    ), 200
