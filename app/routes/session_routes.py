from flask_jwt_extended import jwt_required, current_user
from flask import Blueprint, request, jsonify
from app import db
from app.models.models import AcademicSession, ProgramCourse, CourseAllocation, User
from icecream import ic

session_bp = Blueprint('sessions', __name__)

@session_bp.route('/init', methods=['POST'])
@jwt_required()
def initialize_session():

    ic(current_user.is_vetter)

    if not current_user or not (current_user.is_superadmin or current_user.is_vetter):
        return jsonify({"msg": "Unauthorized – Only superadmin can create sessions"}), 403

    data = request.get_json()
    session_name = data.get('name')

    

    if not session_name:
        return jsonify({'error': 'Session name is required'}), 400

    if AcademicSession.query.filter_by(name=session_name).first():
        return jsonify({'error': f"Session - '{session_name}' already exists"}), 400
    
     # Deactivate current active sessions
    AcademicSession.query.update({AcademicSession.is_active: False})
    
    # Create new session
    new_session = AcademicSession(name=session_name, is_active=True)
    db.session.add(new_session)
    db.session.flush()

    # all_program_courses = ProgramCourse.query.all()

    # for pc in all_program_courses:
    #     last_alloc = (
    #         CourseAllocation.query
    #         .filter_by(program_course_id=pc.id)
    #         .order_by(CourseAllocation.session_id.desc())
    #         .first()
    #     )

    #     new_alloc = CourseAllocation(
    #         program_course_id=pc.id,
    #         session_id=new_session.id,
    #         lecturer_id=last_alloc.lecturer_id if last_alloc else None,
    #         is_allocated=bool(last_alloc and last_alloc.lecturer_id)
    #     )

    #     db.session.add(new_alloc)

    db.session.commit()
    # return jsonify({'message': f"Session '{session_name}' initialized by superadmin."}), 201
    return jsonify({
        "msg": f"Session '{session_name}' created and activated successfully",
        "session": {
            "id": new_session.id,
            "name": new_session.name,
            "is_active": new_session.is_active
        }
    }), 201


@session_bp.route('/active', methods=['GET'])
@jwt_required()
def get_session():

    if not current_user or not (current_user.is_superadmin or current_user.is_vetter):
        return jsonify({"msg": "Unauthorized – Only superadmin can fetch sessions"}), 403

    current_session = AcademicSession.query.filter_by(is_active=True).first()
    
    return jsonify({
        "session": [{
            "id": current_session.id,
            "name": current_session.name,
            "is_active": current_session.is_active
        }]
    }), 200
