from app import db
from app.models import (
    DepartmentAllocationState, 
    AcademicSession, 
    User, CourseAllocation, 
    ProgramCourse, Lecturer, 
    Semester, Program, Level,
    Department
)
from datetime import datetime, timezone
import requests
import json
from sqlalchemy import or_
import os
from dotenv import load_dotenv

from app.models.models import Bulletin

load_dotenv()

def push_allocation_to_umis(payload, token):
    url = os.getenv('UMIS_ALLOCATION_URL')

    headers = {
        'Content-Type': 'application/json',
        'authorization': token,
        'action': 'data'
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        
        response_data = response.json()

        # Interpret the response from UMIS.
        if response_data.get("ResultCode") == 0:
            # On success, return a tuple: (True, the full parsed dictionary)
            return True, response_data
        else:
            # On failure, return a tuple: (False, an error message string)
            error_desc = response_data.get("ResultDesc", "Unknown error from UMIS")
            return False, error_desc

    except requests.exceptions.RequestException as e:
        # Handle network errors
        return False, f"Network error connecting to UMIS: {str(e)}"
    except ValueError:
        # Handle cases where the response is not valid JSON
        return False, f"Invalid JSON response from UMIS: {response.text}"

def get_allocation_class_options(umis_token, umisid):
    """
    Retrieves all allocation class options from UMIS.
    """
    
    # FETCH CLASS OPTION DATA
    class_option_api = f"{os.getenv('UMIS_CLASS_OPTION_URL')}{umisid}"
    header = {
        'action': 'read',
        'authorization': umis_token
    }
    resp = requests.get(class_option_api, headers=header)

    if resp.status_code != 200:
        return None, f"Failed to fetch class_option data ({resp.status_code})"
    
    class_options = resp.json()
    if 'data' not in class_options or not isinstance(class_options['data'], list):
        return None, "Invalid class_option data format from UMIS"

    if 'data' in class_options:
        sorted_class_options = sorted(
            [{
                'id': option.get('class_option_id'),
                'name': option.get('class_option_name')
            } for option in class_options.get('data')],
            key=lambda option: option.get('name', '')
        )

        return sorted_class_options, None
                        
    return None, "class_option not found in UMIS data"
    

def get_allocation_status(department_id, semester_id):
    """
    Checks if the allocation for a given department and semester is submitted for the active session.
    """
    session = AcademicSession.query.filter_by(is_active=True).first()
    if not session:
        return False, "No active session found."

    state = DepartmentAllocationState.query.filter_by(
        department_id=department_id,
        session_id=session.id,
        semester_id=semester_id
    ).first()

    return state.is_submitted if state else False, None

def submit_allocation(department_id, user_id, semester_id):
    """
    Submits the allocation for a department and semester for the active session.
    """
    session = AcademicSession.query.filter_by(is_active=True).first()
    if not session:
        return None, "No active academic session found."

    # Find or create the state
    state = DepartmentAllocationState.query.filter_by(
        department_id=department_id,
        session_id=session.id,
        semester_id=semester_id
    ).first()

    if not state:
        state = DepartmentAllocationState(
            department_id=department_id,
            session_id=session.id,
            semester_id=semester_id
        )
        db.session.add(state)
    
    if state.is_submitted:
        return None, "Allocations for this department and semester have already been submitted."

    state.is_submitted = True
    state.submitted_at = datetime.now(timezone.utc)
    state.submitted_by_id = user_id
    
    db.session.commit()
    return state, None

def vet_allocation(department_id, admin_user_id, semester_id):
    """
    Marks an allocation as vetted for a department and semester in the active session.
    """
    session = AcademicSession.query.filter_by(is_active=True).first()
    if not session:
        return None, "No active academic session found."

    # Find the specific allocation state record. It must exist.
    state = DepartmentAllocationState.query.filter_by(
        department_id=department_id,
        session_id=session.id,
        semester_id=semester_id
    ).first()

    if not state:
        return None, "No allocation record found for the specified department, session, and semester."

    # Enforce business rules: Must be submitted but not yet vetted.
    if not state.is_submitted:
        return None, "This allocation cannot be vetted because it has not been submitted yet."
        
    if state.is_vetted:
        return None, "This allocation has already been vetted."

    # Update the state to mark it as vetted
    state.is_vetted = True
    state.vetted_at = datetime.now(timezone.utc)
    state.vetted_by_id = admin_user_id
    
    db.session.commit()
    return state, None

# def unblock_allocation(department_id, semester_id):
#     """
#     Unblocks a department's allocation for a given semester in the active session.
#     """
#     session = AcademicSession.query.filter_by(is_active=True).first()
#     if not session:
#         return None, "No active academic session found."

#     state = DepartmentAllocationState.query.filter_by(
#         department_id=department_id,
#         session_id=session.id,
#         semester_id=semester_id
#     ).first()

#     if not state or not state.is_submitted:
#         return None, "Allocations for this department and semester are not currently submitted."

#     state.is_submitted = False
#     state.is_vetted = False
#     db.session.commit()
    
#     return state, None

def unblock_allocation(department_id, semester_id):
    """
    Resets a department's allocation by DELETING the state record for a given
    semester in the active session. This allows for a fresh submission.
    """
    try:
        session = AcademicSession.query.filter_by(is_active=True).first()
        if not session:
            return None, "No active academic session found."

        state = DepartmentAllocationState.query.filter_by(
            department_id=department_id,
            session_id=session.id,
            semester_id=semester_id
        ).first()

        # If no state record exists, there's nothing to unblock.
        if not state:
            return None, "No allocation submission record found to unblock."

        # If the allocation is already unblocked, no action is needed.
        if not state.is_submitted:
            return None, "Allocation for this department and semester is already in an unblocked state."

        # Instead of resetting flags, delete the entire record from the database.
        db.session.delete(state)
        db.session.commit()
        
        # Return a success message instead of the now-deleted 'state' object.
        return {"message": "Allocation has been successfully unblocked. The department can now resubmit."}, None

    except Exception as e:
        # If any database error occurs, roll back the session to prevent a bad state.
        db.session.rollback()
        # In a real application, you would log the error `e` here.
        return None, f"An unexpected database error occurred during unblocking: {str(e)}"

def update_course_allocation(data_list, department_id):
    if not data_list:
        return None, "Request body cannot be empty."

    first_item = data_list[0]
    semester_id = first_item.get('semesterId')

    # Check if the allocation is submitted
    is_submitted, error = get_allocation_status(department_id, semester_id)
    if error:
        return None, error
    if is_submitted:
        return None, "Cannot update allocations that have already been submitted."

    session = AcademicSession.query.filter_by(is_active=True).first()
    if not session:
        return None, "No active academic session found."

    try:
        # Delete existing allocations for the course
        first_item = data_list[0]
        program_id = first_item['programId']
        course_id = first_item['courseId']
        level_id = first_item['levelId']
        semester_id = first_item.get('semesterId')

        # Find the ProgramCourse ID, which links everything
        program_course = ProgramCourse.query.filter_by(
            program_id=program_id,
            course_id=course_id,
            level_id=level_id,
            semester_id=semester_id
        ).first()

        if not program_course:
            return None, "Course not found in program"
        
        # Verify that the program of the course belongs to the HOD's department.
        if program_course.program.department_id != department_id:
            return None, "Unauthorized: You do not have permission to update this course."

        # Delete all existing allocations for this course/semester/session
        CourseAllocation.query.filter_by(
            program_course_id=program_course.id,
            semester_id=semester_id,
            session_id=session.id
        ).delete()
        
        # Create the new allocation records from the submitted data
        for item in data_list:
            lecturer_name = item.get("allocatedTo")
            if not lecturer_name: # Skip if no lecturer is assigned
                continue
            
            lecturer = (
                Lecturer.query.join(User)
                .filter(User.name == lecturer_name)
                .first()
            )
            
            if not lecturer:
                return None, f"Lecturer '{lecturer_name}' not found."
                

            new_allocation = CourseAllocation(
                program_course_id=program_course.id,
                session_id=session.id,
                semester_id=semester_id,
                lecturer_id=lecturer.id,
                source_bulletin_id=program_course.bulletin_id,
                group_name=item.get('groupName'),
                is_lead=item.get('groupName').lower() == "group a",
                is_allocated=item.get('isAllocated'),
                class_size=item.get('classSize'),
                class_option=item.get('class_option')
            )
            db.session.add(new_allocation)

        # Commit the transaction (deletes and adds happen together)
        db.session.commit()
        return True, None

    except Exception as e:
        db.session.rollback()
        return None, str(e)

def get_allocations_by_department(department_id, semester_id):
    """
    Gets all course allocations for a given department and semester,
    organized by program and level.
    """
    programs = Program.query.filter_by(department_id=department_id).all()
    semester = db.session.get(Semester, semester_id)
    session = AcademicSession.query.filter_by(is_active=True).first()
    bulletins = Bulletin.query.all()

    if not programs:
        # If no programs exist, return empty list immediately
        return [], None

    if not semester or not session:
        return None, "Invalid semester or session."
    
    state = DepartmentAllocationState.query.filter_by(
        department_id=department_id,
        session_id=session.id,
        semester_id=semester.id
    ).first()

    if state:
        vetted = state.is_vetted
        submitted = state.is_submitted
    else:
        vetted = False
        submitted = False

    output = []

    for bulletin in bulletins:
        tot_course_allocated = 0
        tot_courses_pushed = 0

        bulletin_data = {"id": bulletin.id, "name": bulletin.name, "is_all_pushed": False,"semester": []}
        semester_data = {
            "sessionId": session.id, 
            "sessionName": session.name,
            "vetted": vetted,
            "submitted": submitted,
            "id": semester.id, 
            "name": semester.name, 
            "department_id": programs[0].department.id,
            "department_name": programs[0].department.name, 
            "programs": []
        }

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
                
                program_courses = ProgramCourse.query.filter_by(
                    program_id=program.id, 
                    level_id=level.id,
                    semester_id=semester.id,
                    # bulletin_id=bulletin.id # only current bulletin courses
                ).distinct()

                for pc in program_courses:
                    course = pc.course
                    allocations = CourseAllocation.query.filter_by(
                        program_course_id=pc.id,
                        semester_id=semester.id,
                        session_id=session.id,
                        source_bulletin_id=bulletin.id
                    ).all()

                    if allocations:
                        # check if all courses have been pushed to umis
                        tot_course_allocated += len(allocations)
                        courses_pushed = [alloc for alloc in allocations if alloc.is_pushed_to_umis]
                        tot_courses_pushed += len(courses_pushed)

                        for allocation in allocations:
                            lecturer_name = None
                            if allocation.lecturer_profile and allocation.lecturer_profile.user_account:
                                lecturer_name = allocation.lecturer_profile.user_account[0].name

                            level_data["courses"].append({
                                "id": str(allocation.program_course_id),
                                "code": course.code,
                                "title": course.title,
                                "unit": course.units,
                                "isAllocated": bool(allocation),
                                "allocatedTo": lecturer_name,
                                "class_option": allocation.class_option,
                                "groupName": allocation.group_name,
                                "is_pushed_to_umis": allocation.is_pushed_to_umis,
                                "pushed_to_umis_by": allocation.pushed_by.name if allocation.pushed_by else None,
                            })
                    # else:
                    #     level_data["courses"].append({
                    #         "id": str(course.id),
                    #         "code": course.code,
                    #         "title": course.title,
                    #         "unit": course.units,
                    #         "isAllocated": False,
                    #         "allocatedTo": None,
                    #         "groupName": None
                    #     })
                
                if level_data["courses"]:
                    program_data["levels"].append(level_data)

            if program_data["levels"]:
                semester_data["programs"].append(program_data)

        is_all_pushed = (tot_course_allocated > 0) and (tot_course_allocated == tot_courses_pushed)
        
        bulletin_data["is_all_pushed"] = is_all_pushed
        bulletin_data["semester"].append(semester_data)
        output.append(bulletin_data)

    
    return output, None

# from collections import defaultdict

# def get_allocations_by_department(department_id, semester_id):
#     """
#     Gets all course allocations for a given department and semester,
#     organized by bulletin, program, and level.
#     """
#     # Initial Data Fetching
#     department = db.session.get(Department, department_id)
#     semester = db.session.get(Semester, semester_id)
#     session = AcademicSession.query.filter_by(is_active=True).first()
#     bulletins = Bulletin.query.order_by(Bulletin.name).all()

#     if not department or not semester or not session:
#         return None, "Invalid department, semester, or active session."

#     programs = department.programs
#     if not programs:
#         return [], None

#     state = DepartmentAllocationState.query.filter_by(
#         department_id=department_id,
#         session_id=session.id,
#         semester_id=semester_id
#     ).first()

#     # PERFORMANCE OPTIMIZATION: Fetch all data in bulk
#     # Get all ProgramCourse IDs for the entire department in one query.
#     all_pc_ids_query = db.session.query(ProgramCourse.id)\
#         .join(Program)\
#         .filter(Program.department_id == department_id)

#     # Fetch all allocations for the current session & semester in ONE query.
#     all_allocations = CourseAllocation.query.filter(
#         CourseAllocation.program_course_id.in_(all_pc_ids_query),
#         CourseAllocation.session_id == session.id,
#         CourseAllocation.semester_id == semester_id
#     ).options(
#         db.joinedload(CourseAllocation.pushed_by) # Eager load the 'pushed_by' user
#     ).all()

#     # Create a fast lookup map: {program_course_id: [list of allocations]}
#     allocations_map = defaultdict(list)
#     for alloc in all_allocations:
#         allocations_map[alloc.program_course_id].append(alloc)
    
#     # Structure the Data
#     output = []
#     for bulletin in bulletins:
#         bulletin_allocations = [] # Collect all allocations for this bulletin

#         semester_data = {
#             "sessionId": session.id, 
#             "sessionName": session.name,
#             "vetted": state.is_vetted if state else False,
#             "submitted": state.is_submitted if state else False,
#             "id": semester.id, 
#             "name": semester.name, 
#             "department_id": department.id,
#             "department_name": department.name, 
#             "programs": []
#         }

#         for program in programs:
#             program_data = {"id": program.id, "name": program.name, "levels": []}
            
#             # Fetch all program courses for this program and semester
#             program_courses = ProgramCourse.query.filter_by(
#                 program_id=program.id,
#                 semester_id=semester.id
#             ).all()

#             # Group courses by level_id
#             courses_by_level = defaultdict(list)
#             for pc in program_courses:
#                 courses_by_level[pc.level_id].append(pc)

#             for level_id, courses_in_level in courses_by_level.items():
#                 level = db.session.get(Level, level_id)
#                 level_data = {"id": str(level.id), "name": f"{level.name} Level", "courses": []}

#                 for pc in courses_in_level:
#                     course = pc.course
                    
#                     # Filter the pre-fetched allocations for this course and bulletin
#                     allocs_for_course = allocations_map.get(pc.id, [])
#                     bulletin_specific_allocs = [a for a in allocs_for_course if a.source_bulletin_id == bulletin.id]

#                     if bulletin_specific_allocs:
#                         bulletin_allocations.extend(bulletin_specific_allocs) # Add to the bulletin's total

#                         for allocation in bulletin_specific_allocs:
#                             lecturer_name = allocation.lecturer_profile.user_account[0].name if allocation.lecturer_profile and allocation.lecturer_profile.user_account else None
                            
#                             level_data["courses"].append({
#                                 "id": str(course.id), 
#                                 "programCourseId": allocation.program_course_id,
#                                 "code": course.code,
#                                 "title": course.title,
#                                 "unit": course.units,
#                                 "isAllocated": True,
#                                 "allocatedTo": lecturer_name,
#                                 "class_option": allocation.class_option,
#                                 "groupName": allocation.group_name,
#                                 "is_pushed_to_umis": allocation.is_pushed_to_umis,
#                                 "pushed_to_umis_by": allocation.pushed_by.name if allocation.pushed_by else None,
#                             })
                
#                 if level_data["courses"]:
#                     program_data["levels"].append(level_data)

#             if program_data["levels"]:
#                 semester_data["programs"].append(program_data)
        
#         # Calculate only after all data for the bulletin has been gathered
#         total_for_bulletin = len(bulletin_allocations)
#         pushed_for_bulletin = sum(1 for alloc in bulletin_allocations if alloc.is_pushed_to_umis)
        
#         # is_all_pushed is True only if there are allocations AND they all have been pushed
#         is_all_pushed = (total_for_bulletin > 0) and (total_for_bulletin == pushed_for_bulletin)

#         # Only add the bulletin to the output if it has relevant data
#         if semester_data["programs"]:
#             output.append({
#                 "id": bulletin.id,
#                 "name": bulletin.name,
#                 "is_all_pushed": is_all_pushed,
#                 "semester": [semester_data]
#             })

#     return output, None

def department_courses(department_id, semester_id, session_id):
    """
    Gets the total number of relevant courses for a department in a given semester.
    This includes:
    1. All courses from the active bulletin for that semester.
    2. Any courses from PREVIOUS bulletins that have been allocated in the given session.
    """
    # Get the active bulletin
    active_bulletin = Bulletin.query.filter_by(is_active=True).first()

    if not active_bulletin:
        # If there's no bulletin, we can't determine the base list of courses.
        return []
    
    # courses = (db.session.query(ProgramCourse.id)
    #     .join(Program, Program.id == ProgramCourse.program_id)
    #     .filter(ProgramCourse.semester_id == semester_id)
    #     .filter(Program.department_id == department_id)
    #     .filter(ProgramCourse.bulletin_id == active_bulletin.id)
    # ).all()

    # return courses

    # Find all ProgramCourse IDs that have been allocated to this department in this session.
    # This captures the "legacy" allocations.
    allocations_in_session_query = db.session.query(CourseAllocation.program_course_id)\
        .join(ProgramCourse, ProgramCourse.id == CourseAllocation.program_course_id)\
        .join(Program, Program.id == ProgramCourse.program_id)\
        .filter(
            Program.department_id == department_id,
            CourseAllocation.session_id == session_id
        ).distinct()

    allocated_pc_ids = {row.program_course_id for row in allocations_in_session_query.all()}

    # Main query to get the definitive list of courses
    courses_query = (db.session.query(ProgramCourse.id)
        .join(Program, Program.id == ProgramCourse.program_id)
        .filter(
            Program.department_id == department_id,
            ProgramCourse.semester_id == semester_id,
            # The Course is in the active bulletin OR it has an allocation this session
            or_(
                ProgramCourse.bulletin_id == active_bulletin.id,
                ProgramCourse.id.in_(allocated_pc_ids)
            )
        ).distinct()
    )
    
    return courses_query.all()

def department_allocation_progress(department_id, semester_id, session_id):
    allocations = (db.session.query(CourseAllocation.program_course_id)
        .join(ProgramCourse, ProgramCourse.id == CourseAllocation.program_course_id)
        .join(Program, Program.id == ProgramCourse.program_id)
        .filter(Program.department_id == department_id)
        .filter(CourseAllocation.semester_id == semester_id)
        .filter(CourseAllocation.session_id == session_id)
        .distinct()
        .all()
    )

    all_allocations = (db.session.query(CourseAllocation.program_course_id)
        .join(ProgramCourse, ProgramCourse.id == CourseAllocation.program_course_id)
        .join(Program, Program.id == ProgramCourse.program_id)
        .filter(Program.department_id == department_id)
        .filter(CourseAllocation.semester_id == semester_id)
        .filter(CourseAllocation.session_id == session_id)
        .all()
    )

    return allocations, all_allocations

def get_allocation_status_overview():
    """
    Gets an overview of the allocation status for all departments for each semester.
    Status can be 'Allocated', 'Still Allocating', or 'Not Started'.
    Accessible by superadmins and vetters.
    """

    try:
        semesters = Semester.query.filter_by(is_active=True).all() # Get only active semesters (semesters = Semester.query.order_by(Semester.id).all())
        departments = Department.query.order_by(Department.name).all()
        active_session = AcademicSession.query.filter_by(is_active=True).first()

        if not active_session:
            return {"error": "No active academic session found."}
        
        # We need the active bulletin for our logic, check for it once
        active_bulletin = Bulletin.query.filter_by(is_active=True).first()
        if not active_bulletin:
            return {"error": "No active bulletin found."}

        output = []
        for semester in semesters:
            semester_data = {
                "sessionId": active_session.id, 
                "sessionName": active_session.name,
                "id": semester.id,
                "name": semester.name,
                "departments": []
            }
            
            for i, department in enumerate(departments):
                
                # Check if the department has submitted allocations for this semester
                if department.name not in ["Academic Planning", "Registry", "General Study Division", "Biosciences and Biotechnology"]:

                    submitted = False 
                    vet_status = "Not Vetted" 
                    status = "Not Started" 

                    courses = department_courses(department.id, semester.id, active_session.id)

                    allco, _ = department_allocation_progress(department.id, semester.id, active_session.id)
                    
                    state = DepartmentAllocationState.query.filter_by(
                        department_id=department.id,
                        semester_id=semester.id,
                        session_id=active_session.id
                    ).first()
                    
                    if state:
                        status = "Allocated"

                        if state.is_vetted:
                            vet_status = "Vetted"

                        if state.is_submitted:
                            submitted = state.is_submitted
                    elif len(allco) > 0:
                        status = "Still Allocating"
                        # # 2. If not submitted, check if there are any partial allocations
                        # has_allocations = db.session.query(CourseAllocation.id)\
                        #     .join(ProgramCourse, ProgramCourse.id == CourseAllocation.program_course_id)\
                        #     .join(Program, Program.id == ProgramCourse.program_id)\
                        #     .filter(Program.department_id == department.id)\
                        #     .filter(CourseAllocation.semester_id == semester.id)\
                        #     .filter(CourseAllocation.session_id == active_session.id)\
                        #     .first() is not None
                        
                        # if has_allocations:
                        #     status = "Still Allocating"

                    # get most recent allocation timestamp for this department (if any)
                    last_alloc_row = db.session.query(CourseAllocation.created_at)\
                        .join(ProgramCourse, ProgramCourse.id == CourseAllocation.program_course_id)\
                        .join(Program, Program.id == ProgramCourse.program_id)\
                        .filter(Program.department_id == department.id)\
                        .filter(CourseAllocation.semester_id == semester.id)\
                        .filter(CourseAllocation.session_id == active_session.id)\
                        .order_by(CourseAllocation.created_at.desc())\
                        .first()

                    last_alloc_at = last_alloc_row[0] if last_alloc_row else None
                    
                    hod = next((u for u in department.users if u.is_hod), None)

                    semester_data["departments"].append({
                        "sn": i + 1,
                        "department_id": department.id,
                        "department_name": department.name,
                        "hod_name": hod.name if hod else "-",
                        "total_courses": len(courses) if len(courses) > 0 else 0,
                        "total_courses_allocated": len(allco) if len(allco) > 0 else 0,
                        "allocation_rate": round((len(allco)/len(courses))*100, 1) if len(courses) > 0 else 0,
                        "status": status,
                        "submitted": submitted,
                        "vet_status": vet_status if state else "Not Vetted",
                        "vetted_by": state.vetted_by.name if state and state.is_vetted and state.vetted_by else None,
                        "last_allocation_at": last_alloc_at.isoformat() if last_alloc_at else None
                    })
        
            # sort departments by most recent allocation first (None -> goes last)
            semester_data["departments"].sort(key=lambda d: d.get("last_allocation_at") or "", reverse=True)

            output.append(semester_data)

        return output

    except Exception as e:
        # Log the error e
        return {"error": "An unexpected error occurred.", "details": str(e)}
    
# def get_active_semester_allocation_stats():
#     """
#     Gets active semesters' allocation stats for admin users oversight and decision making.
#     """

#     try:
#         active_semester = Semester.query.filter_by(is_active=True).first()
#         departments = Department.query.order_by(Department.name).all()
#         active_session = AcademicSession.query.filter_by(is_active=True).first()

#         # if not active_session:
#         #     return jsonify({"error": "No active academic session found."}), 404

#         output = []
        
#         semester_data = {
#             "id": active_semester.id,
#             "name": active_semester.name,
#         }
        
        
#         # Get list of all departments
#         department_acad = [department.name for department in departments if department.name not in ["Academic Planning", "Registry"]]

#         allocation_progress = 0
#         allocation_submitted = 0
#         allocated_courses = 0

#         for i, department in enumerate(departments):

#             if department.name not in ["Academic Planning", "Registry"]:

#                 # courses = department_courses(department.id, semester.id)

#                 allco = department_allocation_progress(department.id, active_semester.id, active_session.id)

#                 if len(allco) > 0:
#                     allocation_progress += 1
#                     allocated_courses += len(allco)
                
#                 state = DepartmentAllocationState.query.filter_by(
#                     department_id=department.id,
#                     semester_id=active_semester.id,
#                     session_id=active_session.id
#                 ).first()
                
#                 if state:
#                     allocation_submitted += 1
        
#         allocation_not_started = len(department_acad) - allocation_progress
#         allocation_progress = allocation_progress - allocation_submitted

#         semester_data["allocated_courses"] = allocated_courses
#         semester_data["allocation_in_progress"] = allocation_progress
#         semester_data["allocation_submitted"] = allocation_submitted
#         semester_data["allocation_not_started"] = allocation_not_started
#         semester_data["compliance_score"] = round((allocation_submitted/len(department_acad))*100, 1)
#         semester_data["in_progress_rate"] = round((allocation_progress/len(department_acad))*100, 1)
#         semester_data["not_started_rate"] = round((allocation_not_started/len(department_acad))*100, 1)

#         return semester_data, None

#     except Exception as e:
#         # Log the error e
#         return None, f"An unexpected error occurred: {str(e)}",

def get_active_semester_allocation_stats():
    """
    Gets active semesters' allocation stats for admin users oversight and decision making.
    """
    try:
        active_semester = Semester.query.filter_by(is_active=True).first()
        departments = Department.query.order_by(Department.name).all()
        active_session = AcademicSession.query.filter_by(is_active=True).first()
        all_allocation = CourseAllocation.query.filter_by(session_id=active_session.id, semester_id=active_semester.id).all()

        # Add robust checks
        if not active_semester:
            return None, "No active semester found."
        if not active_session:
            return None, "No active academic session found."

        semester_data = {
            "id": active_semester.id,
            "name": active_semester.name,
        }

        number_of_pushed_allocation = sum(1 for alloc in all_allocation if alloc.is_pushed_to_umis) if all_allocation else 0
        
        department_acad = [d for d in departments if d.name not in ["Academic Planning", "Registry", "General Study Division", "Biosciences and Biotechnology"]]
        
        if not department_acad:
             return None, "No academic departments found to generate stats."

        allocation_in_progress_count = 0
        allocation_submitted_count = 0
        total_allocated_courses = 0
        total_allocated_course_groups = 0
        total_courses_to_allocate = 0 # New metric

        for department in department_acad:
            
            # --- UPDATED METRICS CALCULATION ---
            # Get the definitive list of total courses for this department
            courses_to_allocate = department_courses(department.id, active_semester.id, active_session.id)
            total_courses_to_allocate += len(courses_to_allocate)

            # Get the number of actually allocated courses
            allocations, all_allocations = department_allocation_progress(department.id, active_semester.id, active_session.id)
            total_allocated_courses += len(allocations)
            total_allocated_course_groups += len(all_allocations)
            
            # Check submission state
            state = DepartmentAllocationState.query.filter_by(
                department_id=department.id,
                semester_id=active_semester.id,
                session_id=active_session.id
            ).first()
            
            if state and state.is_submitted:
                allocation_submitted_count += 1
            elif len(allocations) > 0:
                allocation_in_progress_count += 1

        total_departments = len(department_acad)
        allocation_not_started_count = total_departments - allocation_submitted_count - allocation_in_progress_count

        semester_data["total_allocated_course_groups"] = total_allocated_course_groups
        semester_data["number_of_pushed_allocation"] = number_of_pushed_allocation
        semester_data["allocated_courses"] = total_allocated_courses
        semester_data["allocation_in_progress"] = allocation_in_progress_count
        semester_data["allocation_submitted"] = allocation_submitted_count
        semester_data["allocation_not_started"] = allocation_not_started_count
        semester_data["compliance_score"] = round((allocation_submitted_count / total_departments) * 100, 1)
        semester_data["in_progress_rate"] = round((allocation_in_progress_count / total_departments) * 100, 1)
        semester_data["not_started_rate"] = round((allocation_not_started_count / total_departments) * 100, 1)

        return semester_data, None

    except Exception as e:
        # Log the error e
        return None, f"An unexpected error occurred: {str(e)}"

