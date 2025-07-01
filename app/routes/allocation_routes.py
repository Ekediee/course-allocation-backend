from flask_jwt_extended import jwt_required, current_user
from flask import Blueprint, request, jsonify
from app import db
from app.models import Program, ProgramCourse, CourseAllocation, Semester
from icecream import ic

allocation_bp = Blueprint('allocations', __name__)

@allocation_bp.route('/list', methods=['GET'])
@jwt_required()
def get_hod_course_allocations():
    hod = current_user
    department = hod.lecturer.department

    programs = Program.query.filter_by(department_id=department.id).all()
    semesters = Semester.query.all()  # Or filtered by active session

    output = []
    for semester in semesters:
        semester_data = {"id": semester.id, "name": semester.name, "programs": []}
        
        for program in programs:
            program_data = {"id": program.id, "name": program.name, "levels": []}
            
            levels = db.session.query(ProgramCourse.level).filter_by(program_id=program.id).distinct()
            for level_row in levels:
                level = level_row.level
                level_data = {"id": str(level), "name": f"{level} Level", "courses": []}
                
                program_courses = ProgramCourse.query.filter_by(
                    program_id=program.id, level=level
                ).all()

                for pc in program_courses:
                    course = pc.course
                    allocation = CourseAllocation.query.filter_by(
                        program_course_id=pc.id,
                        semester_id=semester.id
                    ).first()

                    level_data["courses"].append({
                        "id": str(pc.id),
                        "code": course.code,
                        "title": course.title,
                        "unit": course.unit,
                        "isAllocated": bool(allocation),
                        "allocatedTo": allocation.lecturer.full_name if allocation else None
                    })
                program_data["levels"].append(level_data)
            semester_data["programs"].append(program_data)
        output.append(semester_data)
    return output

