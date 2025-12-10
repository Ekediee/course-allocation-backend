from flask_jwt_extended import jwt_required, current_user
from flask import Blueprint, request, jsonify
from sqlalchemy import or_
from app import db
from app.models import (
    Program, ProgramCourse, 
    CourseAllocation, Semester, Level, 
    Lecturer, AcademicSession, User, Specialization, Bulletin,
    DepartmentAllocationState, Department
)
from app.services.umis_auth_service import auth_dev_user
import app.services.allocation_service as allocation_service
from app.services.allocation_service import get_allocation_status_overview
from collections import defaultdict
from flask import session
from datetime import datetime, timezone


allocation_bp = Blueprint('allocations', __name__)

@allocation_bp.route('/status/<int:semester_id>', methods=['GET'])
@jwt_required()
def get_allocation_submission_status(semester_id):
    """
    Checks if the allocations for the HOD's department for a given semester are submitted.
    """
    if not current_user.is_hod:
        return jsonify({"error": "Unauthorized: Only HODs can check submission status."}), 403

    department_id = current_user.department_id
    is_submitted, error = allocation_service.get_allocation_status(department_id, semester_id)

    if error:
        return jsonify({"error": error}), 404

    return jsonify({"is_submitted": is_submitted}), 200


@allocation_bp.route('/submit', methods=['POST'])
@jwt_required()
def submit_allocations():
    """
    Submits (locks) the course allocations for the HOD's department for a specific semester.
    """
    if not current_user.is_hod:
        return jsonify({"error": "Unauthorized: Only HODs can submit allocations."}), 403

    data = request.get_json()
    semester_id = data.get('semester_id')

    if not semester_id:
        return jsonify({"error": "semester_id is required."}), 400

    department_id = current_user.department_id
    user_id = current_user.id

    state, error = allocation_service.submit_allocation(department_id, user_id, semester_id)

    if error:
        return jsonify({"error": error}), 400
    
    return jsonify({
        "message": "Allocations submitted successfully.",
        "submission_details": {
            "department_id": state.department_id,
            "semester_id": state.semester_id,
            "session_id": state.session_id,
            "submitted_at": state.submitted_at.isoformat()
        }
    }), 200

@allocation_bp.route('/vet', methods=['POST'])
@jwt_required()
def vet_allocations():
    """
    Vets (approves) a submitted course allocation. Action performed by an admin.
    """
    
    # Authorization: Ensure the user has the correct role (e.g., is_admin)
    if not (current_user.is_vetter or current_user.is_superadmin): # Assuming you have an 'is_admin' property
        return jsonify({"error": "Unauthorized: Only administrators can vet allocations."}), 403

    data = request.get_json()
    department_id = data.get('department_id')
    semester_id = data.get('semester_id')

    # Validation: The admin must specify which department's allocation to vet
    if not department_id or not semester_id:
        return jsonify({"error": "department_id and semester_id are required."}), 400

    admin_user_id = current_user.id

    # Call the service layer to perform the action
    state, error = allocation_service.vet_allocation(department_id, admin_user_id, semester_id)

    if error:
        # A "not found" error
        if "not found" in error:
            return jsonify({"error": error}), 404
        return jsonify({"error": error}), 400
    
    # Return a success response
    return jsonify({
        "message": "Allocation vetted successfully.",
        "vetting_details": {
            "department_id": state.department_id,
            "semester_id": state.semester_id,
            "session_id": state.session_id,
            "vetted_at": state.vetted_at.isoformat(),
            "vetted_by": state.vetted_by.name
        }
    }), 200


@allocation_bp.route('/unblock', methods=['POST'])
@jwt_required()
def unblock_allocations():
    """
    Unblocks (unlocks) course allocations for a department and semester.
    Accessible only by superadmins.
    """
    if not current_user.is_superadmin:
        return jsonify({"error": "Unauthorized: Only administrators can unblock allocations."}), 403

    data = request.get_json()
    department_id = data.get('department_id')
    semester_id = data.get('semester_id')

    if not department_id or not semester_id:
        return jsonify({"error": "department_id and semester_id are required."}), 400

    state, error = allocation_service.unblock_allocation(department_id, semester_id)

    if error:
        return jsonify({"error": error}), 400

    return jsonify(state), 200


@allocation_bp.route('/update', methods=['PUT'])
@jwt_required()
def update_allocation():
    """
    Updates the allocation for a course using a delete-then-insert strategy.
    """
    if not current_user.is_hod:
        return jsonify({"error": "Unauthorized: Only HODs can update allocations."}), 403

    data = request.get_json()

    if not data:
        return jsonify({"status": "error", "message": "Invalid data"}), 400
    
    department_id = current_user.department_id

    success, error = allocation_service.update_course_allocation(data, department_id)

    if error:
        return jsonify({"status": "error", "message": error}), 400
    
    return jsonify({"status": "success", "message": "Course allocation updated successfully."}), 200


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

@allocation_bp.route('/allocation-by-department', methods=['POST'])
@jwt_required()
def get_allocations_by_department_route():
    """
     Gets all course allocations for a given department and semester,
     organized by program and level.
    """
    if not (current_user.is_superadmin or current_user.is_vetter):
        return jsonify({"error": "Unauthorized: Only superadmins and vetters can view this."}), 403
    
    data = request.get_json()
    department_id = data.get('department')
    semester_id = data.get('semester')

    if not department_id or not semester_id:
        return jsonify({"error": "department_id and semester_id are required."}), 400

    allocations, error = allocation_service.get_allocations_by_department(department_id, semester_id)

    if error:
        return jsonify({"error": error}), 400

    return jsonify(allocations)

# @allocation_bp.route('/detailed-list', methods=['GET'])
# @jwt_required()
# def get_detailed_course_list_for_allocation():
#     department = current_user.lecturer.department
#     programs = Program.query.filter_by(department_id=department.id).all()
#     semesters = Semester.query.all()
#     session = AcademicSession.query.filter_by(is_active=True).first()

#     # Get the active bulletin
#     active_bulletin = Bulletin.query.filter_by(is_active=True).first()

#     if not session:
#         return jsonify({"error": "No active session found"}), 404
    
#     # Check if active bulletin exists
#     if not active_bulletin:
#         return jsonify({"error": "No active bulletin found"}), 404

#     # Pre-fetch semester objects for logic handling
#     first_semester = Semester.query.filter_by(name='First Semester').first()
#     second_semester = Semester.query.filter_by(name='Second Semester').first()
#     third_semester = Semester.query.filter_by(name='Summer Semester').first()

#     first_and_second_sem_ids = [s.id for s in [first_semester, second_semester] if s]

#     # Get all ProgramCourse IDs relevant to the programs in this department.
#     program_ids = [p.id for p in programs]
#     relevant_pc_ids_query = db.session.query(ProgramCourse.id).filter(
#         ProgramCourse.program_id.in_(program_ids),
#         ProgramCourse.bulletin_id == active_bulletin.id # review this line - it may prevent allocation from prev bulletins
#     )

#     # Fetch all allocations for these courses in the current session in ONE query.
#     all_allocations_for_session = CourseAllocation.query.filter(
#         CourseAllocation.session_id == session.id,
#         CourseAllocation.program_course_id.in_(relevant_pc_ids_query)
#     ).all()

#     # Create a fast lookup dictionary (map).
#     allocations_map = defaultdict(list)
#     for alloc in all_allocations_for_session:
#         key = (alloc.program_course_id, alloc.semester_id)
        
#         allocations_map[key].append(alloc)


#     output = []
#     for semester in semesters:
#         semester_data = {"sessionId": session.id, "sessionName": session.name, "id": semester.id, "name": semester.name, "programs": []}
        
#         for program in programs:
#             program_data = {"id": program.id, "name": program.name, "levels": []}
            
#             level_ids = db.session.query(ProgramCourse.level_id).filter_by(
#                 program_id=program.id,
#                 bulletin_id=active_bulletin.id # review - it may prevent levels from other bulletins
#             ).distinct().all()
            
#             for level_row in level_ids:
#                 level_id = level_row.level_id
#                 level = db.session.get(Level, level_id)
#                 level_data = {"id": str(level.id), "name": f"{level.name} Level", "courses": []}
                
#                 # Conditional logic for fetching courses
#                 if third_semester and semester.id == third_semester.id:
#                     if not first_and_second_sem_ids:
#                         continue
#                     program_courses_query = ProgramCourse.query.filter(
#                         ProgramCourse.program_id == program.id,
#                         ProgramCourse.level_id == level.id,
#                         ProgramCourse.semester_id.in_(first_and_second_sem_ids),
#                         ProgramCourse.bulletin_id == active_bulletin.id
#                     )
#                 else:
#                     program_courses_query = ProgramCourse.query.filter_by(
#                         program_id=program.id, 
#                         level_id=level.id,
#                         semester_id=semester.id,
#                         bulletin_id=active_bulletin.id
#                     )

#                 program_courses = program_courses_query.distinct()

#                 for pc in program_courses:
#                     course = pc.course

#                     # Access the specializations for the program_course
#                     specializations = [spec.name for spec in pc.specializations]
                    
#                     # Check if the allocation exists for the semester and course.
#                     allocations = allocations_map.get((pc.id, semester.id))

#                     # Process the list to get all lecturer names.
#                     allocated_to_names = []
#                     if allocations:
#                         # Create a list of names, safely checking for profiles
#                         allocated_to_names = [
#                             alloc.lecturer_profile.user_account[0].name
#                             for alloc in allocations 
#                             if alloc.lecturer_profile and alloc.lecturer_profile.user_account
#                         ]

#                     if len(specializations) > 0:
#                         for spec in specializations:

#                             level_data["courses"].append({
#                                 "id": str(course.id),
#                                 "programCourseId": pc.id,
#                                 "code": course.code,
#                                 "title": course.title,
#                                 "unit": course.units,
#                                 "specialization": spec,
#                                 "isAllocated": bool(allocations),
#                                 "allocatedTo": ", ".join(allocated_to_names) if allocated_to_names else None
#                             })
#                     else:
#                         level_data["courses"].append({
#                             "id": str(course.id),
#                             "programCourseId": pc.id,
#                             "code": course.code,
#                             "title": course.title,
#                             "unit": course.units,
#                             "specialization": 'General',
#                             "isAllocated": bool(allocations),
#                             "allocatedTo": ", ".join(allocated_to_names) if allocated_to_names else None
#                         })
                
#                 # It sorts by specialization name first, then by the course code.
#                 level_data["courses"].sort(key=lambda c: (c['specialization'], c['code']))

#                 if level_data["courses"]:
#                     program_data["levels"].append(level_data)

#             program_data["levels"].sort(key=lambda level: int(level['name'].split()[0]))    

#             if program_data["levels"]:
#                 semester_data["programs"].append(program_data)
        
#         output.append(semester_data)
        
#     return jsonify(output)

@allocation_bp.route('/detailed-list', methods=['GET'])
@jwt_required()
def get_detailed_course_list_for_allocation():
    department = current_user.lecturer.department
    programs = Program.query.filter_by(department_id=department.id).all()
    semesters = Semester.query.filter_by(is_active=True).all() # Or filtered by active session (semesters = Semester.query.all())
    session = AcademicSession.query.filter_by(is_active=True).first()
    active_bulletin = Bulletin.query.filter_by(is_active=True).first()

    if not session:
        return jsonify({"error": "No active session found"}), 404
    if not active_bulletin:
        return jsonify({"error": "No active bulletin found"}), 404

    # Get all ProgramCourse IDs for the programs in this department, regardless of bulletin
    program_ids = [p.id for p in programs]
    all_department_pc_ids_query = db.session.query(ProgramCourse.id).filter(
        ProgramCourse.program_id.in_(program_ids)
    )

    # Fetch ALL allocations for this department in the current session.
    # This will now include allocations from previous bulletins.
    all_allocations_for_session = CourseAllocation.query.filter(
        CourseAllocation.session_id == session.id,
        CourseAllocation.program_course_id.in_(all_department_pc_ids_query)
    ).all()

    # Create a set of ProgramCourse IDs that have been allocated in this session.
    allocated_pc_ids = {alloc.program_course_id for alloc in all_allocations_for_session}

    # Create the fast lookup map as before.
    allocations_map = defaultdict(list)
    for alloc in all_allocations_for_session:
        key = (alloc.program_course_id, alloc.semester_id)
        allocations_map[key].append(alloc)
    
    # Pre-fetch semester objects for logic handling
    first_semester = Semester.query.filter_by(name='First Semester').first()
    second_semester = Semester.query.filter_by(name='Second Semester').first()
    third_semester = Semester.query.filter_by(name='Summer Semester').first()
    first_and_second_sem_ids = [s.id for s in [first_semester, second_semester] if s]

    output = []
    for semester in semesters:
        semester_data = {"sessionId": session.id, "sessionName": session.name, "id": semester.id, "name": semester.name, "programs": []}
        
        for program in programs:
            program_data = {"id": program.id, "name": program.name, "levels": []}
            
            # Get levels that EITHER have courses in the active bulletin OR have courses allocated in this session.
            level_ids_query = db.session.query(ProgramCourse.level_id).filter(
                ProgramCourse.program_id == program.id,
                or_(
                    ProgramCourse.bulletin_id == active_bulletin.id,
                    ProgramCourse.id.in_(allocated_pc_ids)
                )
            ).distinct()
            level_ids = level_ids_query.all()
            
            for level_row in level_ids:
                level_id = level_row.level_id
                level = db.session.get(Level, level_id)
                level_data = {"id": str(level.id), "name": f"{level.name} Level", "courses": []}
                
        
                # Base query that will be modified
                base_query = ProgramCourse.query.filter(
                    ProgramCourse.program_id == program.id,
                    ProgramCourse.level_id == level.id,
                    # A course must be in the active bulletin OR have an allocation this session
                    or_(
                        ProgramCourse.bulletin_id == active_bulletin.id,
                        ProgramCourse.id.in_(allocated_pc_ids)
                    )
                )
                
                # Conditional logic for fetching courses by semester
                if third_semester and semester.id == third_semester.id:
                    if not first_and_second_sem_ids:
                        continue
                    program_courses_query = base_query.filter(
                        ProgramCourse.semester_id.in_(first_and_second_sem_ids)
                    )
                else:
                    program_courses_query = base_query.filter(
                        ProgramCourse.semester_id == semester.id
                    )

                program_courses = program_courses_query.distinct()

                for pc in program_courses:
                    course = pc.course
                    specializations = [spec.name for spec in pc.specializations]
                    allocations = allocations_map.get((pc.id, semester.id))

                    allocated_to_names = []
                    if allocations:
                        allocated_to_names = [
                            alloc.lecturer_profile.user_account[0].name
                            for alloc in allocations 
                            if alloc.lecturer_profile and alloc.lecturer_profile.user_account
                        ]

                    # Logic for creating course dictionaries remains the same
                    if specializations:
                        for spec in specializations:
                            level_data["courses"].append({
                                "id": str(course.id), "programCourseId": pc.id, "code": course.code,
                                "title": course.title, "unit": course.units, "specialization": spec,
                                "isAllocated": bool(allocations),
                                "allocatedTo": ", ".join(allocated_to_names) if allocated_to_names else None
                            })
                    else:
                        level_data["courses"].append({
                            "id": str(course.id), "programCourseId": pc.id, "code": course.code,
                            "title": course.title, "unit": course.units, "specialization": 'General',
                            "isAllocated": bool(allocations),
                            "allocatedTo": ", ".join(allocated_to_names) if allocated_to_names else None
                        })
                
                if level_data["courses"]:
                    level_data["courses"].sort(key=lambda c: (c['specialization'], c['code']))
                    program_data["levels"].append(level_data)

            if program_data["levels"]:
                program_data["levels"].sort(key=lambda level: int(level['name'].split()[0]))
                semester_data["programs"].append(program_data)
        
        if semester_data["programs"]:
            output.append(semester_data)
            
    return jsonify(output)

# @allocation_bp.route('/print', methods=['POST'])
# @jwt_required()
# def get__allocation():

#     data = request.get_json()
#     department_id = data.get('department_id')

#     programs = Program.query.filter_by(department_id=department_id).all()
#     semesters = Semester.query.all()
#     session = AcademicSession.query.filter_by(is_active=True).first()

#     if not session:
#         return jsonify({"error": "No active session found"}), 404

#     # Pre-fetch semester objects for logic handling
#     first_semester = Semester.query.filter_by(name='First Semester').first()
#     second_semester = Semester.query.filter_by(name='Second Semester').first()
#     third_semester = Semester.query.filter_by(name='Summer Semester').first()

#     first_and_second_sem_ids = [s.id for s in [first_semester, second_semester] if s]

#     # Get all ProgramCourse IDs relevant to the programs in this department.
#     program_ids = [p.id for p in programs]
#     relevant_pc_ids_query = db.session.query(ProgramCourse.id).filter(ProgramCourse.program_id.in_(program_ids))

#     # Fetch all allocations for these courses in the current session in ONE query.
#     all_allocations_for_session = CourseAllocation.query.filter(
#         CourseAllocation.session_id == session.id,
#         CourseAllocation.program_course_id.in_(relevant_pc_ids_query)
#     ).all()

#     # Create a fast lookup dictionary (map).
#     allocations_map = defaultdict(list)
#     for alloc in all_allocations_for_session:
#         key = (alloc.program_course_id, alloc.semester_id)
        
#         allocations_map[key].append(alloc)

#     output = []
#     for semester in semesters:
#         semester_data = {"sessionId": session.id, "sessionName": session.name, "id": semester.id, "name": semester.name, "programs": []}
        
#         for program in programs:
#             program_data = {"id": program.id, "name": program.name, "levels": []}
            
#             level_ids = db.session.query(ProgramCourse.level_id).filter_by(program_id=program.id).distinct().all()
            
#             for level_row in level_ids:
#                 level_id = level_row.level_id
#                 level = db.session.get(Level, level_id)
#                 level_data = {"id": str(level.id), "name": f"{level.name} Level", "courses": []}
                
#                 # Conditional logic for fetching courses
#                 if third_semester and semester.id == third_semester.id:
#                     if not first_and_second_sem_ids:
#                         continue
#                     program_courses_query = ProgramCourse.query.filter(
#                         ProgramCourse.program_id == program.id,
#                         ProgramCourse.level_id == level.id,
#                         ProgramCourse.semester_id.in_(first_and_second_sem_ids)
#                     )
#                 else:
#                     program_courses_query = ProgramCourse.query.filter_by(
#                         program_id=program.id, 
#                         level_id=level.id,
#                         semester_id=semester.id
#                     )

#                 program_courses = program_courses_query.distinct()

#                 for pc in program_courses:
#                     course = pc.course
                    
#                     # Check if the allocation exists for the semester and course.
#                     allocations = allocations_map.get((pc.id, semester.id))

#                     # Process the list to get all lecturer names.
#                     allocated_to_names = []
#                     if allocations:
#                         # Create a list of names, safely checking for profiles
#                         allocated_to_names = [
#                             alloc.lecturer_profile.user_account[0].name
#                             for alloc in allocations 
#                             if alloc.lecturer_profile and alloc.lecturer_profile.user_account
#                         ]

#                         level_data["courses"].append({
#                             "id": str(course.id),
#                             "programCourseId": pc.id,
#                             "code": course.code,
#                             "title": course.title,
#                             "unit": course.units,
#                             "isAllocated": bool(allocations),
#                             "allocatedTo": ", ".join(allocated_to_names) if allocated_to_names else None
#                         })

#                 if level_data["courses"]:
#                     program_data["levels"].append(level_data)

#             program_data["levels"].sort(key=lambda level: int(level['name'].split()[0]))    

#             if program_data["levels"]:
#                 semester_data["programs"].append(program_data)
        
#         output.append(semester_data)
        
#     return jsonify(output)

@allocation_bp.route('/print', methods=['POST'])
@jwt_required()
def get_allocation_report(): # Renamed for clarity

    data = request.get_json()
    department_id = data.get('department_id')

    # Get Department object for easier access to programs
    department = db.session.get(Department, department_id)
    if not department:
        return jsonify({"error": "Department not found"}), 404
        
    programs = department.programs
    semesters = Semester.query.all()
    session = AcademicSession.query.filter_by(is_active=True).first()

    if not session:
        return jsonify({"error": "No active session found"}), 404

    # Pre-fetch ONLY allocated ProgramCourse IDs ---
    # Get all ProgramCourse IDs relevant to the programs in this department.
    program_ids = [p.id for p in programs]
    relevant_pc_ids_query = db.session.query(ProgramCourse.id).filter(ProgramCourse.program_id.in_(program_ids))

    # Fetch all allocations for these courses in the current session in ONE query.
    all_allocations_for_session = CourseAllocation.query.filter(
        CourseAllocation.session_id == session.id,
        CourseAllocation.program_course_id.in_(relevant_pc_ids_query)
    ).all()

    # Create a set of ONLY the ProgramCourse IDs that are allocated.
    # This is the key to our filtering.
    allocated_pc_ids = {alloc.program_course_id for alloc in all_allocations_for_session}

    # Create a fast lookup dictionary (map).
    allocations_map = defaultdict(list)
    for alloc in all_allocations_for_session:
        key = (alloc.program_course_id, alloc.semester_id)
        allocations_map[key].append(alloc)
    
    first_semester = Semester.query.filter_by(name='First Semester').first()
    second_semester = Semester.query.filter_by(name='Second Semester').first()
    third_semester = Semester.query.filter_by(name='Summer Semester').first()
    first_and_second_sem_ids = [s.id for s in [first_semester, second_semester] if s]

    output = []
    for semester in semesters:
        semester_data = {"sessionId": session.id, "sessionName": session.name, "id": semester.id, "name": semester.name, "programs": []}
        
        for program in programs:
            program_data = {"id": program.id, "name": program.name, "levels": []}
            
            # Query levels based on ONLY allocated courses
            level_ids = db.session.query(ProgramCourse.level_id).filter(
                ProgramCourse.program_id == program.id,
                ProgramCourse.id.in_(allocated_pc_ids) # Filter by allocated IDs
            ).distinct().all()
            
            for level_row in level_ids:
                level_id = level_row.level_id
                level = db.session.get(Level, level_id)
                level_data = {"id": str(level.id), "name": f"{level.name} Level", "courses": []}
                
                # Base query for program and level
                base_query = ProgramCourse.query.filter(
                    ProgramCourse.program_id == program.id, 
                    ProgramCourse.level_id == level.id,
                    ProgramCourse.id.in_(allocated_pc_ids) # CRITICAL: Only get allocated courses
                )

                # Conditional logic for semester
                if third_semester and semester.id == third_semester.id:
                    if not first_and_second_sem_ids: continue
                    program_courses_query = base_query.filter(ProgramCourse.semester_id.in_(first_and_second_sem_ids))
                else:
                    program_courses_query = base_query.filter(ProgramCourse.semester_id == semester.id)

                # Now `program_courses` contains ONLY allocated courses
                program_courses = program_courses_query.distinct()

                for pc in program_courses:
                    course = pc.course
                    allocations = allocations_map.get((pc.id, semester.id), [])

                    # No 'if' check needed here, because we know allocations exist
                    allocated_to_names = [
                        alloc.lecturer_profile.user_account[0].name
                        for alloc in allocations 
                        if alloc.lecturer_profile and alloc.lecturer_profile.user_account
                    ]

                    level_data["courses"].append({
                        "id": str(course.id),
                        "programCourseId": pc.id,
                        "code": course.code,
                        "title": course.title,
                        "unit": course.units,
                        "isAllocated": True,
                        "allocatedTo": ", ".join(allocated_to_names) if allocated_to_names else None
                    })

                if level_data["courses"]:
                    program_data["levels"].append(level_data)

            if program_data["levels"]:
                program_data["levels"].sort(key=lambda level: int(level['name'].split()[0]))    
                semester_data["programs"].append(program_data)
        
        # Only add the semester if it has programs with allocated courses
        if semester_data["programs"]:
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

@allocation_bp.route('/allocate/lecturers/all', methods=['GET'])
@jwt_required()
def get_lecturers():
    department = current_user.lecturer.department
    

    if not current_user or not current_user.is_hod:
        return jsonify({'error': 'Access denied. Only HODs can view this data.'}), 403

    # Get department from linked lecturer
    if not current_user.lecturer:
        return jsonify({'error': 'User is not linked to a lecturer profile.'}), 400

    # department = user.lecturer.department
    lecturers = Lecturer.query.all()

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

# @allocation_bp.route("/allocate", methods=["POST"])
# @jwt_required()
# def allocate_course():
#     # Validate HOD access
#     if not current_user or not current_user.is_hod:
#         return jsonify({"error": "Unauthorized: Only HODs can allocate courses."}), 403

#     data_list = request.get_json()
    
#     # 1. Find active session
#     session = AcademicSession.query.filter_by(is_active=True).first()
#     if not session:
#         return jsonify({"error": "No active academic session found."}),
    
#     results = []

#     for index, data in enumerate(data_list):
#         try:    
#             if is_number(data.get("semesterId")) is False:
#                 semester = Semester.query.filter_by(name=data.get("semesterId")).first()
#                 semester_id = semester.id
#             else:
#                 semester_id = int(data.get("semesterId"))

#             if is_number(data.get("programId")) is False:
#                 program = Program.query.filter_by(name=data.get("programId")).first()
#                 program_id = program.id
#             else:
#                 program_id = int(data.get("programId"))
#             level_id = int(data.get("levelId"))
#             course_id = int(data.get("courseId"))
#             class_size = int(data.get("classSize", 0))
#             is_allocated = data.get("isAllocated", False)
#             group_name = data.get("groupName")
#             lecturer_name = data.get("allocatedTo")

#             # 2. Find program_course
#             pc = ProgramCourse.query.filter_by(
#                 program_id=program_id,
#                 course_id=course_id,
#                 level_id=level_id,
#                 semester_id=semester_id
#             ).first()
            
#             if not pc:
#                 return jsonify({
#                     "status": "error",
#                     "message": "ProgramCourse not found for given input."
#                 }), 404

#             # 3. Resolve lecturer by full name
#             lecturer = (
#                 Lecturer.query.join(User)
#                 .filter(User.name == lecturer_name, Lecturer.department_id == current_user.department_id)
#                 .first()
#             )
#             if not lecturer:
#                 return jsonify({
#                     "status": "error",
#                     "message": f"Lecturer '{lecturer_name}' not found."
#                 }), 404

#             # 4. Check if this allocation already exists (same session, program_course, group_name)
#             existing = CourseAllocation.query.filter_by(
#                 program_course_id=pc.id,
#                 session_id=session.id,
#                 group_name=group_name
#             ).first()

#             if existing:
#                 return jsonify({"error": f"Allocation already exists for group '{group_name}'"}), 409
            
#             # 5. Create new CourseAllocation
#             allocation = CourseAllocation(
#                 program_course_id=pc.id,
#                 session_id=session.id,
#                 semester_id=semester_id,
#                 lecturer_id=lecturer.id,
#                 source_bulletin_id=pc.bulletin_id,  # Assuming bulletin_id is available in ProgramCourse
#                 is_de_allocation=False,       # Assuming this is a normal allocation
#                 group_name=group_name,
#                 is_lead=(group_name.lower() == "group a"),
#                 is_allocated=is_allocated,
#                 class_size=class_size
#             )
            
#             db.session.add(allocation)
#             results.append({
#                 "index": index,
#                 "message": f"Course allocated successfully to {lecturer_name} for group '{group_name}'"
#             })

#         except Exception as e:
#             results.append({"index": index, "error": str(e)})

#     db.session.commit()

#     return jsonify({
#         "status": "success",
#         "message": "Course allocated successfully",
#     }), 201

@allocation_bp.route("/allocate", methods=["POST"])
@jwt_required()
def allocate_course():
    # Validate HOD access
    if not current_user or not current_user.is_hod:
        return jsonify({"error": "Unauthorized: Only HODs can allocate courses."}), 403

    data_list = request.get_json()
    if not isinstance(data_list, list) or not data_list:
        return jsonify({"error": "Request body must be a non-empty list of allocations."}), 400
    
    # Find active session
    session = AcademicSession.query.filter_by(is_active=True).first()
    if not session:
        return jsonify({"error": "No active academic session found."}), 400

    try:
        allocations_to_create = []

        # VALIDATE ALL INCOMING DATA FIRST
        for index, data in enumerate(data_list):
            
            # check if semesterId is a number - it could semester name if coming from specialization allocation
            semesterid = data.get("semesterId")
            if is_number(semesterid) is False:
                semester = Semester.query.filter_by(name=semesterid).first()
                if not semester:
                    raise ValueError(f"Error for '{data.get('groupName')}': Semester '{semesterid}' not found.")
                semester_id = semester.id
            else:
                semester_id = int(semesterid)

            programid = data.get("programId")
            if is_number(programid) is False:
                program = Program.query.filter_by(name=programid).first()
                if not program:
                    raise ValueError(f"Error for '{data.get('groupName')}': Program '{programid}' not found.")
                program_id = program.id
            else:
                program_id = int(programid)
            
            # program_id = int(data.get("programId"))
            level_id = int(data.get("levelId"))
            course_id = int(data.get("courseId"))
            lecturer_name = data.get("allocatedTo") # Assuming frontend now sends ID
            group_name = data.get("groupName")

            # Find program_course
            pc = ProgramCourse.query.filter_by(
                program_id=program_id,
                course_id=course_id,
                level_id=level_id,
                semester_id=semester_id
            ).first()
            if not pc:
                # Use raise to fail the entire transaction immediately
                raise ValueError(f"Error for '{group_name}': Course not found in the specified program/level.")

            # Resolve lecturer by ID
            lecturer = (
                Lecturer.query.join(User)
                .filter(User.name == lecturer_name)
                .first()
            )
            if not lecturer:
                return jsonify({
                    "status": "error",
                    "message": f"Lecturer '{lecturer_name}' not found."
                }), 404

            # Check for existing allocation
            existing = CourseAllocation.query.filter_by(
                program_course_id=pc.id,
                session_id=session.id,
                group_name=group_name
            ).first()
            if existing:
                raise ValueError(f"Error for '{group_name}': An allocation already exists for this group.")

            # If all checks pass, prepare the allocation object
            allocation_data = {
                "program_course_id": pc.id,
                "session_id": session.id,
                "semester_id": semester_id,
                "lecturer_id": lecturer.id,
                "source_bulletin_id": pc.bulletin_id,
                "group_name": group_name,
                "is_lead": (group_name.lower() == "group a"),
                "is_allocated": data.get("isAllocated", False),
                "class_size": int(data.get("classSize", 0)),
                "class_option":data.get('class_option')
            }
            allocations_to_create.append(allocation_data)

        # CREATE ALL RECORDS IF VALIDATION PASSED
        if not allocations_to_create:
             raise ValueError("No valid allocations to create.")

        for data in allocations_to_create:
            new_allocation = CourseAllocation(**data)
            db.session.add(new_allocation)

        # Commit the transaction once, after all records are added
        db.session.commit()

        return jsonify({
            "status": "success",
            "message": f"Successfully allocated course to {len(allocations_to_create)} group(s).",
        }), 201

    except (ValueError, KeyError) as e:
        # Catch specific validation errors
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        # Catch unexpected server errors
        db.session.rollback()
        # It's good practice to log the full error here
        # logger.error(f"Unexpected error during allocation: {e}")
        return jsonify({"status": "error", "message": "An unexpected server error occurred."}), 500

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
                program_data["levels"].sort(key=lambda level: int(level['name'].split()[0]))
                semester_data["programs"].append(program_data)
        
        if semester_data["programs"]:
            output.append(semester_data)

    return jsonify(output)

# @allocation_bp.route('/courses-by-bulletin', methods=['POST'])
# @jwt_required()
# def get_courses_for_allocation_by_bulletin():
#     """
#     Fetches courses for a specific program, semester, and bulletin,
#     organized by level, for the purpose of allocation.
#     """
#     # Authorization: Ensure user is HOD
#     if not current_user or not current_user.is_hod:
#         return jsonify({'msg': 'Access denied. Only HODs can view this data.'}), 403

#     # Get query parameters
#     data = request.get_json()
#     bulletin_name = data.get('bulletin')
#     program_name = data.get('program')
#     semester_name = data.get('semester')
    
#     # Fetch bulletin from DB
#     bulletin = Bulletin.query.filter_by(name=bulletin_name).first()
#     program = Program.query.filter_by(name=program_name).first()
#     semester = Semester.query.filter_by(name=semester_name).first()

#     if not bulletin:
#         return jsonify({"error": f"Bulletin '{bulletin_name}' not found."}), 404

#     # Check submission status
#     is_submitted, _ = allocation_service.get_allocation_status(current_user.department_id, semester.id)

#     # Fetch program courses based on criteria
#     program_courses = ProgramCourse.query.filter_by(
#         program_id=program.id,
#         semester_id=semester.id,
#         bulletin_id=bulletin.id
#     ).all()

#      # Get all relevant ProgramCourse IDs first.
#     pc_ids = [pc.id for pc in program_courses]
    
#     # Fetch all allocations for these courses in ONE query.
#     all_allocations = CourseAllocation.query.filter(
#         CourseAllocation.program_course_id.in_(pc_ids),
#         CourseAllocation.semester_id == semester.id
#     ).all()

#     # Create a fast lookup dictionary (map).
#     # Key: program_course_id, Value: allocation object
#     allocations_map = {alloc.program_course_id: alloc for alloc in all_allocations}

#     # Structure the data by level
#     levels_data = {}
#     for pc in program_courses:
#         level = pc.level
#         course = pc.course

#         # get all allocated courses for the semester and program
#         allocation = allocations_map.get(pc.id)

#         if level.id not in levels_data:
#             levels_data[level.id] = {
#                 "id": str(level.id),
#                 "name": f"{level.name} Level",
#                 "courses": []
#             }

#         levels_data[level.id]["courses"].append({
#             "id": str(course.id),
#             "code": course.code,
#             "title": course.title,
#             "unit": course.units,
#             "isAllocated": bool(allocation),
#             "allocatedTo": allocation.lecturer_profile.user_account[0].name if allocation else None
#         })

#     # Convert the dictionary to a list for the final output
#     output = list(levels_data.values())

#     # Sort the list of levels numerically by name.
#     output.sort(key=lambda level: int(level['name'].split()[0]))

#     return jsonify({
#         "is_submitted": is_submitted,
#         "levels": output
#     })

@allocation_bp.route('/courses-by-bulletin', methods=['POST'])
@jwt_required()
def get_courses_for_allocation_by_bulletin():
    """
    Fetches courses for a specific program, semester, and bulletin,
    organized by level and specialization, for the purpose of allocation.
    """
    # Authorization: Ensure user is HOD
    if not current_user or not current_user.is_hod:
        return jsonify({'msg': 'Access denied. Only HODs can view this data.'}), 403

    # Get query parameters
    data = request.get_json()
    bulletin_name = data.get('bulletin')
    program_name = data.get('program')
    semester_name = data.get('semester')
    
    # Fetch bulletin from DB
    bulletin = Bulletin.query.filter_by(name=bulletin_name).first()
    program = Program.query.filter_by(name=program_name).first()
    semester = Semester.query.filter_by(name=semester_name).first()

    if not bulletin or not program or not semester:
        return jsonify({"error": "Invalid bulletin, program, or semester name."}), 404

    # Check submission status
    is_submitted, _ = allocation_service.get_allocation_status(current_user.department_id, semester.id)

    # Fetch program courses based on criteria, eager loading specializations for performance
    program_courses = ProgramCourse.query.filter_by(
        program_id=program.id,
        semester_id=semester.id,
        bulletin_id=bulletin.id
    ).options(db.joinedload(ProgramCourse.specializations)).all()

    # Performance Optimization 
    pc_ids = [pc.id for pc in program_courses]
    all_allocations = CourseAllocation.query.filter(
        CourseAllocation.program_course_id.in_(pc_ids),
        CourseAllocation.semester_id == semester.id
    ).all()
    allocations_map = {alloc.program_course_id: alloc for alloc in all_allocations}

    # Structure the data by level
    levels_data = {}
    for pc in program_courses:
        level = pc.level
        course = pc.course
        allocation = allocations_map.get(pc.id)

        if level.id not in levels_data:
            levels_data[level.id] = {
                "id": str(level.id),
                "name": f"{level.name} Level",
                "courses": []
            }

        # get program course specialization detials
        specialization_names = [spec.name for spec in pc.specializations]

        # If the course has specializations, create a copy for each one.
        if specialization_names:
            for spec_name in specialization_names:
                levels_data[level.id]["courses"].append({
                    "id": str(course.id),
                    "programCourseId": pc.id,
                    "code": course.code,
                    "title": course.title,
                    "unit": course.units,
                    "specialization": spec_name, # Set the specific specialization
                    "isAllocated": bool(allocation),
                    "allocatedTo": allocation.lecturer_profile.user_account[0].name if allocation else None
                })
        # Otherwise, add it as a "General" course.
        else:
            levels_data[level.id]["courses"].append({
                "id": str(course.id),
                "programCourseId": pc.id,
                "code": course.code,
                "title": course.title,
                "unit": course.units,
                "specialization": "General", # Default value
                "isAllocated": bool(allocation),
                "allocatedTo": allocation.lecturer_profile.user_account[0].name if allocation else None
            })

    # After populating, loop through the levels and sort their courses
    for level_id in levels_data:
        levels_data[level_id]['courses'].sort(key=lambda c: (c['specialization'], c['code']))

    # Convert the dictionary to a list for the final output
    output = list(levels_data.values())

    # Sort the list of levels numerically by name.
    output.sort(key=lambda level: int(level['name'].split()[0]))

    return jsonify({
        "is_submitted": is_submitted,
        "levels": output
    })

@allocation_bp.route('/allocation-status-overview', methods=['GET'])
@jwt_required()
def get_allocation_overview():
    """
    Gets an overview of the allocation status for all departments for each semester.
    Status can be 'Allocated', 'Still Allocating', or 'Not Started'.
    Accessible by superadmins and vetters.
    """
    if not (current_user.is_superadmin or current_user.is_vetter or current_user.is_admin):
        return jsonify({"error": "Unauthorized: Only superadmins and vetters can view this."}), 403

    try:
        # semesters = Semester.query.order_by(Semester.id).all()
        # departments = Department.query.order_by(Department.name).all()
        active_session = AcademicSession.query.filter_by(is_active=True).first()

        if not active_session:
            return jsonify({"error": "No active academic session found."}), 404

        output = get_allocation_status_overview()
        

        # for semester in semesters:
        #     semester_data = {
        #         "id": semester.id,
        #         "name": semester.name,
        #         "departments": []
        #     }
            
        #     for i, department in enumerate(departments):
                
        #         # Check if the department has submitted allocations for this semester
        #         if department.name not in ["Academic Planning", "Registry"]:

        #             submitted = False 
        #             vet_status = "Not Vetted" 
        #             status = "Not Started" 
                    
        #             state = DepartmentAllocationState.query.filter_by(
        #                 department_id=department.id,
        #                 semester_id=semester.id,
        #                 session_id=active_session.id
        #             ).first()
                    
        #             if state:
        #                 status = "Allocated"

        #                 if state.is_vetted:
        #                     vet_status = "Vetted"

        #                 if state.is_submitted:
        #                     submitted = state.is_submitted
        #             else:
        #                 # 2. If not submitted, check if there are any partial allocations
        #                 has_allocations = db.session.query(CourseAllocation.id)\
        #                     .join(ProgramCourse, ProgramCourse.id == CourseAllocation.program_course_id)\
        #                     .join(Program, Program.id == ProgramCourse.program_id)\
        #                     .filter(Program.department_id == department.id)\
        #                     .filter(CourseAllocation.semester_id == semester.id)\
        #                     .filter(CourseAllocation.session_id == active_session.id)\
        #                     .first() is not None
                        
        #                 if has_allocations:
        #                     status = "Still Allocating"

        #             # get most recent allocation timestamp for this department (if any)
        #             last_alloc_row = db.session.query(CourseAllocation.created_at)\
        #                 .join(ProgramCourse, ProgramCourse.id == CourseAllocation.program_course_id)\
        #                 .join(Program, Program.id == ProgramCourse.program_id)\
        #                 .filter(Program.department_id == department.id)\
        #                 .filter(CourseAllocation.semester_id == semester.id)\
        #                 .filter(CourseAllocation.session_id == active_session.id)\
        #                 .order_by(CourseAllocation.created_at.desc())\
        #                 .first()

        #             last_alloc_at = last_alloc_row[0] if last_alloc_row else None
                    
        #             hod = next((u for u in department.users if u.is_hod), None)

        #             semester_data["departments"].append({
        #                 "sn": i + 1,
        #                 "department_id": department.id,
        #                 "department_name": department.name,
        #                 "hod_name": hod.name if hod else "-",
        #                 "status": status,
        #                 "submitted": submitted,
        #                 "vet_status": vet_status if state else "Not Vetted",
        #                 "last_allocation_at": last_alloc_at.isoformat() if last_alloc_at else None
        #             })

        #     # status_order = {"Allocated": 0, "Still Allocating": 1, "Not Started": 2}
        #     # semester_data["departments"].sort(key=lambda d: status_order.get(d["status"], 99))        
        #     # sort departments by most recent allocation first (None -> goes last)
        #     semester_data["departments"].sort(key=lambda d: d.get("last_allocation_at") or "", reverse=True)

        #     output.append(semester_data)

        return jsonify(output)

    except Exception as e:
        # Log the error e
        return jsonify({"error": "An unexpected error occurred.", "details": str(e)}), 500
    
@allocation_bp.route('/details', methods=['GET'])
@jwt_required()
def get_allocation_details():
    # Get identifiers from the query parameters
    program_course_id = request.args.get('program_course_id', type=int)
    semester_id = request.args.get('semester_id', type=int)
    
    session = AcademicSession.query.filter_by(is_active=True).first()
    if not session:
        return jsonify({"status": "error", "message": "No active session"}), 404

    if not program_course_id or not semester_id:
        return jsonify({"status": "error", "message": "Missing required parameters"}), 400

    # Fetch all allocation records for this specific course in the current session
    allocations = CourseAllocation.query.filter_by(
        program_course_id=program_course_id,
        semester_id=semester_id,
        session_id=session.id
    ).all()

    # Format the data for the frontend
    details = []
    for alloc in allocations:
        details.append({
            "groupName": alloc.group_name,
            "lecturer": alloc.lecturer_profile.user_account[0].name if alloc.lecturer_profile else None,
            "classSize": alloc.class_size,
            "classOption": alloc.class_option,
        })

    return jsonify({"status": "success", "data": details})

@allocation_bp.route('/class-options', methods=['GET'])
@jwt_required()
def get_allocation_class_options():
    """
    Fetch the list of class options from UMIS.
    """
    if not current_user.is_hod:
        return jsonify({"error": "Unauthorized: Only HODs can class options list."}), 403

    umis_token = request.headers.get('X-UMIS-Token')
    umisid = request.headers.get('X-UMIS-id')

    class_options, error = allocation_service.get_allocation_class_options(umis_token, umisid)

    if error:
        return jsonify({"error": error}), 404

    return jsonify(class_options), 200

@allocation_bp.route('/push_allocation_to_umis', methods=['POST'])
@jwt_required()
def push_allocation_to_umis():
    """
    Pushes ALL allocated groups for a given program_course_id to UMIS.
    """
    if not current_user.is_vetter and not current_user.is_superadmin:
        return jsonify({"error": "Unauthorized: You are not authorized to perform this transaction."}), 403
    
    data = request.get_json()
    print("Received data for UMIS push:", data)
    program_course_id = data.get('program_course_id')

    if not program_course_id:
        return jsonify({"error": "Missing required field: program_course_id"}), 400

    # Find all allocations for the given program_course_id
    allocations = CourseAllocation.query.filter_by(program_course_id=program_course_id).all()

    # Handle the case where no allocations are found
    if not allocations:
        return jsonify({"message": "No allocations found for this course to push to UMIS."}), 200

    try:
        # Authenticate ONCE before the loop
        umis_token, auth_error = auth_dev_user()
        if auth_error:
            # If authentication fails, stop immediately.
            return jsonify({"error": f"Failed to authenticate with UMIS: {auth_error}"}), 500

        successful_pushes = 0
        failed_pushes = []
        success_keyfields = []

        # Loop and push EACH allocation
        for allocation in allocations:
            # Check if necessary data exists before creating the payload
            if not allocation.lecturer_profile or not allocation.lecturer_profile.staff_id:
                failed_pushes.append(f"Allocation for course {allocation.program_course.course.code} has a missing lecturer staff ID.")
                continue # Skip this allocation and move to the next one

            if allocation.is_pushed_to_umis:
                # Skip already pushed allocations
                continue

            # session = allocation.session.name
            semester = allocation.semester.name

            if semester.lower() == 'first semester':
                quarterid = f"{allocation.session.name}.1"
            elif semester.lower() == 'second semester':
                quarterid = f"{allocation.session.name}.2"
            else:
                quarterid = f"{allocation.session.name}.3"

            payload = {
                "quarterid": quarterid,
                "instructorid": allocation.lecturer_profile.staff_id,
                "courseid": allocation.program_course.course.code, 
                "org_id": "0",
                "coursetitle": allocation.program_course.course.title, 
                "classoption": allocation.class_option,
                "maxclass": str(allocation.class_size),
            }

            # print(f"Pushing payload for {payload['courseid']} ({payload['classoption']}) to UMIS:", payload)
            
            # Push to UMIS
            is_success, response_data = allocation_service.push_allocation_to_umis(payload, umis_token)

            # allocation.is_pushed_to_umis = True
            # allocation.pushed_to_umis_by_id = current_user.id # Record the user's ID
            # allocation.pushed_to_umis_at = datetime.now(timezone.utc) # Record the timestamp
            # db.session.commit()
            # Handle the response from the push
            if is_success:

                # Get response data
                data_dict = response_data.get('data', {})
                keyfield = data_dict.get('keyfield')
                if keyfield:
                    success_keyfields.append(str(keyfield))
                
                #  UPDATE THE ALLOCATION RECORD ON SUCCESS
                allocation.is_pushed_to_umis = True
                allocation.pushed_to_umis_by_id = current_user.id # Record the user's ID
                allocation.pushed_to_umis_at = datetime.now(timezone.utc) # Record the timestamp

                successful_pushes += 1
            else:
                failed_pushes.append(
                    f"Course {payload['courseid']} ({payload['classoption']}): {response_data}."
                )
        
        # Commit all changes after processing
        db.session.commit()

        # Provide a summary response
        if not failed_pushes:
            return jsonify({
                "status": "success",
                "message": f"Successfully pushed {successful_pushes} allocation(s) to UMIS.\nKeyfields: {', '.join(success_keyfields)}"
            }), 200
        else:
            return jsonify({
                "status": "partial_failure",
                "message": f"Completed with {len(failed_pushes)} error(s). Successfully pushed {successful_pushes} allocation(s).\nErrors: {', '.join(failed_pushes)}",
                "error": failed_pushes
            }), 207 # 207 Multi-Status is appropriate for partial successes

    except Exception as e:
        # Catch any unexpected errors (e.g., database connection issues)
        # Log the error `e` here in a real application
        return jsonify({"error": f"An unexpected server error occurred: {str(e)}"}), 500

@allocation_bp.route('/metrics', methods=['GET'])
@jwt_required()
def get_allocation_metrics():
    """
    Fetch course allocation progress metrics.
    """
    if not (current_user.is_superadmin or current_user.is_vetter or current_user.is_admin):
        return jsonify({"error": "Unauthorized: Only super admin or vetter can view these metrics."}), 403

    metrics, error = allocation_service.get_active_semester_allocation_stats()

    if error:
        return jsonify({"error": error}), 404

    return jsonify(metrics), 200