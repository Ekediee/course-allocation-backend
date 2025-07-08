from flask_jwt_extended import jwt_required, current_user
from flask import Blueprint, request, jsonify
from app import db
from app.models import (
    Program, ProgramCourse, 
    CourseAllocation, Semester, Level, 
    Lecturer, AcademicSession, User
)
from icecream import ic

allocation_bp = Blueprint('allocations', __name__)

@allocation_bp.route('/list', methods=['GET'])
@jwt_required()
def get_hod_course_allocations():
    # hod = current_user
    department = current_user.lecturer.department
    
    programs = Program.query.filter_by(department_id=department.id).all()
    semesters = Semester.query.all()  # Or filtered by active session

    output = []
    for semester in semesters:
        semester_data = {"id": semester.id, "name": semester.name, "programs": []}
        
        for program in programs:
            program_data = {"id": program.id, "name": program.name, "levels": []}
            
            # levels = db.session.query(ProgramCourse.level).filter_by(program_id=program.id).distinct().all()
            
            # Get distinct level IDs used in this program
            level_ids = (
                db.session.query(ProgramCourse.level_id)
                .filter_by(program_id=program.id)
                .distinct()
                .all()
            )
            # ic(level_ids, semester.id, program.id)
            for level_row in level_ids:
                # level = level_row.level
                level_id = level_row.level_id
                level = Level.query.get(level_id)

                level_data = {"id": str(level.id), "name": f"{level.name} Level", "courses": []}
                
                program_courses = ProgramCourse.query.filter_by(
                    program_id=program.id, level_id=level.id
                ).distinct()

                for pc in program_courses:
                    course = pc.course
                    allocation = CourseAllocation.query.filter_by(
                        program_course_id=pc.id,
                        semester_id=semester.id
                    ).first()

                    level_data["courses"].append({
                        "id": str(course.id),
                        "code": course.code,
                        "title": course.title,
                        "unit": course.units,
                        "isAllocated": bool(allocation),
                        "allocatedTo": allocation.lecturer_profile.user_account[0].name if allocation else None
                    })
                program_data["levels"].append(level_data)
            semester_data["programs"].append(program_data)
        output.append(semester_data)
    return output

@allocation_bp.route('/allocate/lecturers', methods=['GET'])
@jwt_required()
def get_lecturers_by_department():
    department = current_user.lecturer.department
    

    if not current_user or not current_user.is_hod:
        return jsonify({'error': 'Access denied. Only HODs can view this data.'}), 403

    # Get department from linked lecturer
    if not current_user.lecturer:
        return jsonify({'error': 'User is not linked to a lecturer profile.'}), 400

    # department = user.lecturer.department
    lecturers = Lecturer.query.filter_by(department_id=department.id).all()

    data = [{
        "id": lec.id,
        "staff_id": lec.staff_id,
        "name": lec.user_account[0].name if lec.user_account else "Unlinked",
        "rank": lec.rank,
        "qualification": lec.qualification,
        "phone": lec.phone
    } for lec in lecturers]

    return jsonify(data), 200

@allocation_bp.route("/allocate", methods=["POST"])
@jwt_required()
def allocate_course():
    # Validate HOD access
    if not current_user or not current_user.is_hod:
        return jsonify({"error": "Unauthorized: Only HODs can allocate courses."}), 403

    data_list = request.get_json()
    ic(data_list)
    # 1. Find active session
    session = AcademicSession.query.filter_by(is_active=True).first()
    if not session:
        return jsonify({"error": "No active academic session found."}), 400
    
    results = []

    for index, data in enumerate(data_list):
        try:    
            semester_id = int(data.get("semesterId"))
            program_id = int(data.get("programId"))
            level_id = int(data.get("levelId"))
            course_id = int(data.get("courseId"))
            class_size = int(data.get("classSize", 0))
            is_allocated = data.get("isAllocated", False)
            group_name = data.get("groupName")
            lecturer_name = data.get("allocatedTo")

            # 2. Find program_course
            pc = ProgramCourse.query.filter_by(
                program_id=program_id,
                course_id=course_id,
                level_id=level_id,
                semester_id=semester_id
            ).first()

            if not pc:
                return jsonify({
                    "status": "error",
                    "message": "ProgramCourse not found for given input."
                }), 404

            # 3. Resolve lecturer by full name
            lecturer = (
                Lecturer.query.join(User)
                .filter(User.name == lecturer_name, Lecturer.department_id == current_user.department_id)
                .first()
            )
            if not lecturer:
                return jsonify({
                    "status": "error",
                    "message": f"Lecturer '{lecturer_name}' not found."
                }), 404

            # 4. Check if this allocation already exists (same session, program_course, group_name)
            existing = CourseAllocation.query.filter_by(
                program_course_id=pc.id,
                session_id=session.id,
                group_name=group_name
            ).first()

            if existing:
                return jsonify({"error": f"Allocation already exists for group '{group_name}'"}), 409

            # 5. Create new CourseAllocation
            allocation = CourseAllocation(
                program_course_id=pc.id,
                session_id=session.id,
                semester_id=semester_id,
                lecturer_id=lecturer.id,
                source_bulletin_id=pc.bulletin_id,  # Assuming bulletin_id is available in ProgramCourse
                is_special_allocation=False,  # Assuming this is a normal allocation
                group_name=group_name,
                is_lead=(group_name.lower() == "group a"),
                is_allocated=is_allocated,
                class_size=class_size
            )

            db.session.add(allocation)
            results.append({
                "index": index,
                "message": f"Course allocated successfully to {lecturer_name} for group '{group_name}'"
            })

        except Exception as e:
            results.append({"index": index, "error": str(e)})

    db.session.commit()

    return jsonify({
        "status": "success",
        "message": "Course allocated successfully",
    }), 201
