from flask_jwt_extended import jwt_required, current_user
from flask import Blueprint, request, jsonify
from sqlalchemy import or_
from app import db
from app.models import (
    Program, ProgramCourse, 
    CourseAllocation, Semester, Level, 
    Lecturer, AcademicSession, User, Specialization, Bulletin
)
from icecream import ic

allocation_bp = Blueprint('allocations', __name__)

@allocation_bp.route('/list', methods=['GET'])
@jwt_required()
def get_hod_course_allocations():
    
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
            
            for level_row in level_ids:
                # level = level_row.level
                level_id = level_row.level_id
                level = db.session.get(Level, level_id)

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


@allocation_bp.route('/detailed-list', methods=['GET'])
@jwt_required()
def get_detailed_course_list_for_allocation():
    department = current_user.lecturer.department
    programs = Program.query.filter_by(department_id=department.id).all()
    semesters = Semester.query.all()

    # Pre-fetch semester objects for logic handling
    first_semester = Semester.query.filter_by(name='First Semester').first()
    second_semester = Semester.query.filter_by(name='Second Semester').first()
    third_semester = Semester.query.filter_by(name='Summer Semester').first()

    # Create a list of IDs for easier querying
    first_and_second_sem_ids = []
    if first_semester:
        first_and_second_sem_ids.append(first_semester.id)
    if second_semester:
        first_and_second_sem_ids.append(second_semester.id)

    output = []
    for semester in semesters:
        semester_data = {"id": semester.id, "name": semester.name, "programs": []}
        
        for program in programs:
            program_data = {"id": program.id, "name": program.name, "levels": []}
            
            level_ids = (
                db.session.query(ProgramCourse.level_id)
                .filter_by(program_id=program.id)
                .distinct()
                .all()
            )
            
            for level_row in level_ids:
                level_id = level_row.level_id
                level = db.session.get(Level, level_id)

                level_data = {"id": str(level.id), "name": f"{level.name} Level", "courses": []}
                
                # Conditional logic for fetching courses
                if third_semester and semester.id == third_semester.id:
                    # For Summer semester, get courses from 1st and 2nd semesters
                    if not first_and_second_sem_ids:
                        program_courses = [] # Skip if 1st/2nd sem not found
                    else:
                        program_courses = ProgramCourse.query.filter(
                            ProgramCourse.program_id == program.id,
                            ProgramCourse.level_id == level.id,
                            ProgramCourse.semester_id.in_(first_and_second_sem_ids)
                        ).distinct()
                else:
                    # For regular semesters, get courses for that specific semester
                    program_courses = ProgramCourse.query.filter_by(
                        program_id=program.id, 
                        level_id=level.id,
                        semester_id=semester.id
                    ).distinct()

                for pc in program_courses:
                    course = pc.course
                    # Allocation is always checked against the current semester in the loop
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
                
                if level_data["courses"]:
                    program_data["levels"].append(level_data)

            if program_data["levels"]:
                semester_data["programs"].append(program_data)
        
        output.append(semester_data)
        
    return jsonify(output)


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

def is_number(value):
    try:
        float(value)
        return True
    except ValueError:
        return False

@allocation_bp.route("/allocate", methods=["POST"])
@jwt_required()
def allocate_course():
    # Validate HOD access
    if not current_user or not current_user.is_hod:
        return jsonify({"error": "Unauthorized: Only HODs can allocate courses."}), 403

    data_list = request.get_json()
    
    # 1. Find active session
    session = AcademicSession.query.filter_by(is_active=True).first()
    if not session:
        return jsonify({"error": "No active academic session found."}),
    
    results = []

    for index, data in enumerate(data_list):
        try:    
            if is_number(data.get("semesterId")) is False:
                semester = Semester.query.filter_by(name=data.get("semesterId")).first()
                semester_id = semester.id
            else:
                semester_id = int(data.get("semesterId"))

            if is_number(data.get("programId")) is False:
                program = Program.query.filter_by(name=data.get("programId")).first()
                program_id = program.id
            else:
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
                is_de_allocation=False,       # Assuming this is a normal allocation
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

@allocation_bp.route('/list-by-specialization', methods=['GET'])
@jwt_required()
def get_hod_allocations_by_specialization():
    """
    Gets all course allocations for the HOD's department, organized by
    semester, program, level, and specialization.
    """
    if not current_user or not current_user.is_hod:
        return jsonify({'msg': 'Access denied. Only HODs can view this data.'}), 403

    department = current_user.lecturer.department
    programs = Program.query.filter_by(department_id=department.id).all()
    semesters = Semester.query.all()

    output = []
    for semester in semesters:
        semester_data = {"id": semester.id, "name": semester.name, "programs": []}

        for program in programs:
            program_data = {"id": program.id, "name": program.name, "levels": []}

            level_ids = db.session.query(ProgramCourse.level_id)\
                .filter_by(program_id=program.id)\
                .distinct().all()

            for level_id_tuple in level_ids:
                level_id = level_id_tuple[0]
                level = db.session.get(Level, level_id)
                level_data = {"id": str(level.id), "name": f"{level.name} Level", "specializations": []}

                # Get all program courses for this level
                program_courses = ProgramCourse.query.filter_by(
                    program_id=program.id, level_id=level.id
                ).all()

                general_courses = []
                specialization_courses = {} # Key: specialization_id, Value: list of courses

                for pc in program_courses:
                    allocation = CourseAllocation.query.filter_by(
                        program_course_id=pc.id, semester_id=semester.id
                    ).first()
                    
                    lecturer_name = None
                    if allocation and allocation.lecturer_profile and allocation.lecturer_profile.user_account[0].name:
                        lecturer_name = allocation.lecturer_profile.user_account[0].name

                    course_details = {
                        "id": str(pc.course.id),
                        "code": pc.course.code,
                        "title": pc.course.title,
                        "unit": pc.course.units,
                        "isAllocated": bool(allocation),
                        "allocatedTo": lecturer_name
                    }

                    if not pc.specializations:
                        general_courses.append(course_details)
                    else:
                        for spec in pc.specializations:
                            if spec.id not in specialization_courses:
                                specialization_courses[spec.id] = {
                                    "id": spec.id,
                                    "name": spec.name,
                                    "courses": []
                                }
                            specialization_courses[spec.id]["courses"].append(course_details)
                
                # Add the "General" category if it has courses
                if general_courses:
                    level_data["specializations"].append({
                        "id": "general",
                        "name": "General",
                        "courses": general_courses
                    })
                
                # Add the specialization categories
                level_data["specializations"].extend(specialization_courses.values())
                
                if level_data["specializations"]:
                    program_data["levels"].append(level_data)

            if program_data["levels"]:
                semester_data["programs"].append(program_data)
        
        if semester_data["programs"]:
            output.append(semester_data)

    return jsonify(output)

@allocation_bp.route('/courses-by-bulletin', methods=['POST'])
@jwt_required()
def get_courses_for_allocation_by_bulletin():
    """
    Fetches courses for a specific program, semester, and bulletin,
    organized by level, for the purpose of allocation.
    """
    # 1. Authorization: Ensure user is HOD
    if not current_user or not current_user.is_hod:
        return jsonify({'msg': 'Access denied. Only HODs can view this data.'}), 403

    # 2. Get query parameters
    data = request.get_json()
    bulletin_name = data.get('bulletin')
    program_name = data.get('program')
    semester_name = data.get('semester')

    # # 3. Validate parameters
    # if not all([bulletin_name, program_name, semester_name]):
    #     return jsonify({"error": "Missing required query parameters: bulletin_name, program, semester"}), 400
    
    
    # 4. Fetch bulletin from DB
    bulletin = Bulletin.query.filter_by(name=bulletin_name).first()
    program = Program.query.filter_by(name=program_name).first()
    semester = Semester.query.filter_by(name=semester_name).first()

    if not bulletin:
        return jsonify({"error": f"Bulletin '{bulletin_name}' not found."}), 404

    # 5. Fetch program courses based on criteria
    program_courses = ProgramCourse.query.filter_by(
        program_id=program.id,
        semester_id=semester.id,
        bulletin_id=bulletin.id
    ).all()

    # 6. Structure the data by level
    levels_data = {}
    for pc in program_courses:
        level = pc.level
        course = pc.course

        # get all allocated courses for the semester
        allocation = CourseAllocation.query.filter_by(
            program_course_id=pc.id,
            semester_id=semester.id
        ).first()

        if level.id not in levels_data:
            levels_data[level.id] = {
                "id": str(level.id),
                "name": f"{level.name.strip("L")} Level",
                "courses": []
            }

        levels_data[level.id]["courses"].append({
            "id": str(course.id),
            "code": course.code,
            "title": course.title,
            "unit": course.units,
            "isAllocated": bool(allocation),
            "allocatedTo": allocation.lecturer_profile.user_account[0].name if allocation else None
        })

    # 7. Convert the dictionary to a list for the final output
    output = list(levels_data.values())

    return jsonify(output)
