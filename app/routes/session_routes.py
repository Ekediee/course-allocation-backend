# import os
# from dotenv import load_dotenv
# load_dotenv()
from flask import Blueprint, request, jsonify
from app import db
from app.models.models import AcademicSession, ProgramCourse, CourseAllocation, User
from icecream import ic

session_bp = Blueprint('sessions', __name__, url_prefix='/api/v1/sessions')

def get_current_user():
    # Mocked login — replace with real auth in production
    return User.query.filter_by(email='alloc_admin@babcock.edu.ng').first()

@session_bp.route('/init', methods=['POST'])
def initialize_session():
    user = get_current_user()

    if not user or user.role != 'superadmin':
        return jsonify({'error': 'Only superadmin can initialize sessions.'}), 403

    data = request.get_json()
    session_name = data.get('name')

    

    if not session_name:
        return jsonify({'error': 'Session name is required'}), 400

    if AcademicSession.query.filter_by(name=session_name).first():
        return jsonify({'error': 'Session already exists'}), 400
    
    # Deactivate all previous sessions
    session_name_first = int(session_name.split('/')[0]) - 1
    session_name_second = int(session_name.split('/')[1]) - 1

    previous_session = AcademicSession.query.filter_by(name=f"{session_name_first}/{session_name_second}").first()
    if previous_session:
        previous_session.is_active = False
        db.session.commit()
    
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
    return jsonify({'message': f"Session '{session_name}' initialized by superadmin."}), 201
