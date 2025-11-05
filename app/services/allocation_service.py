from app import db
from app.models import DepartmentAllocationState, AcademicSession, User, CourseAllocation, ProgramCourse, Lecturer, Semester, Program, Level
from datetime import datetime, timezone

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

def unblock_allocation(department_id, semester_id):
    """
    Unblocks a department's allocation for a given semester in the active session.
    """
    session = AcademicSession.query.filter_by(is_active=True).first()
    if not session:
        return None, "No active academic session found."

    state = DepartmentAllocationState.query.filter_by(
        department_id=department_id,
        session_id=session.id,
        semester_id=semester_id
    ).first()

    if not state or not state.is_submitted:
        return None, "Allocations for this department and semester are not currently submitted."

    state.is_submitted = False
    state.is_vetted = False
    db.session.commit()
    
    return state, None

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
                group_name=item['groupName'],
                is_lead=item['groupName'].lower() == "group a",
                is_allocated=item['isAllocated'],
                class_size=item['classSize']
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

    if not semester or not session:
        return None, "Invalid semester or session."
    
    state = DepartmentAllocationState.query.filter_by(
        department_id=department_id,
        session_id=session.id,
        semester_id=semester.id
    ).first()

    if not state or not state.is_submitted:
        vetted = False
        submitted = False

    
    vetted = state.is_vetted
    submitted = state.is_submitted
    db.session.commit()

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
                semester_id=semester.id
            ).distinct()

            for pc in program_courses:
                course = pc.course
                allocations = CourseAllocation.query.filter_by(
                    program_course_id=pc.id,
                    semester_id=semester.id,
                    session_id=session.id
                ).all()

                if allocations:
                    for allocation in allocations:
                        lecturer_name = None
                        if allocation.lecturer_profile and allocation.lecturer_profile.user_account:
                            lecturer_name = allocation.lecturer_profile.user_account[0].name

                        level_data["courses"].append({
                            "id": str(course.id),
                            "code": course.code,
                            "title": course.title,
                            "unit": course.units,
                            "isAllocated": bool(allocation),
                            "allocatedTo": lecturer_name,
                            "groupName": allocation.group_name
                        })
                else:
                    level_data["courses"].append({
                        "id": str(course.id),
                        "code": course.code,
                        "title": course.title,
                        "unit": course.units,
                        "isAllocated": False,
                        "allocatedTo": None,
                        "groupName": None
                    })
            
            if level_data["courses"]:
                program_data["levels"].append(level_data)

        if program_data["levels"]:
            semester_data["programs"].append(program_data)

    output = []
    output.append(semester_data)
    return output, None
