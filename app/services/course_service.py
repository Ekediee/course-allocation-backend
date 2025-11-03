from app import db
from app.models.models import Course, ProgramCourse, Specialization, Program, Level, Semester, AcademicSession, Bulletin
from sqlalchemy import desc 
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy.exc import IntegrityError

def get_all_courses():
    program_courses = ProgramCourse.query.order_by(desc(ProgramCourse.id)).all()
    return program_courses

def validate_course_data(code, title, units, program_id, level_id, semester_id, bulletin_id, course_type_id):
    # Try to find the course by its unique code.
    course = Course.query.filter_by(code=code).first()

    if not course:
        # If the course does not exist, create it.
        course = Course(code=code, title=title, units=units, course_type_id=course_type_id)
        db.session.add(course)
        db.session.flush()  # Use flush to get the course.id before commit

    # Check if this specific association already exists
    existing_program_course = ProgramCourse.query.filter_by(
        course_id=course.id,
        program_id=program_id,
        level_id=level_id,
        semester_id=semester_id,
        bulletin_id=bulletin_id
    ).first()

    return course, existing_program_course

def create_course(data):
    code = data.get('code')
    title = data.get('title')
    units = data.get('unit')
    program_id = data.get('program_id')
    level_id = data.get('level_id')
    semester_id = data.get('semester_id')
    bulletin_id = data.get('bulletin_id')
    specialization_id = data.get('specialization_id')
    course_type_id = data.get('course_type_id')

    # if Course.query.filter_by(code=code).first():
    #     return None, f'Course with code "{code}" already exists'

    # new_course = Course(code=code, title=title, units=units)
    # db.session.add(new_course)
    # db.session.flush()  # Flush to get the new_course.id

    course, existing_program_course = validate_course_data(
        code, title, units, program_id, level_id, semester_id, bulletin_id, course_type_id
    )

    if existing_program_course:
        # If the association already exists, return an error.
        return None, f'This course ({code}) has already been added to this program for the selected bulletin and semester.'

    # Create the new ProgramCourse association
    program_course = ProgramCourse(
        course_id=course.id,
        program_id=program_id,
        level_id=level_id,
        semester_id=semester_id,
        bulletin_id=bulletin_id
    )

    if specialization_id:
        specialization = Specialization.query.get(specialization_id)
        if specialization:
            program_course.specializations.append(specialization)

    db.session.add(program_course)
    db.session.commit()

    return course, None

def batch_create_courses(courses_data):
    created_count = 0
    errors = []

    for course_item in courses_data:
        code = course_item.get('code')
        title = course_item.get('title')
        units = course_item.get('unit') 
        bulletin_id = course_item.get('bulletin_id')
        program_id = course_item.get('program_id')
        semester_id = course_item.get('semester_id')
        level_id = course_item.get('level_id')
        specialization_id = course_item.get('specialization_id')
        course_type_id = course_item.get('course_type_id')

        # Basic validation
        if not all([code, title, bulletin_id, program_id, semester_id, level_id, course_type_id]):
            errors.append(f"Missing required fields in record: {course_item}")
            continue

        if  units is None:
            units = 0

        # if Course.query.filter_by(code=code).first():
        #     errors.append(f'Course with code "{code}" already exists,\n')
        #     continue

        # try:
        #     units = int(units)
        # except (ValueError, TypeError):
        #     errors.append(f"Invalid unit value for course {code}: {units}")
        #     continue

        # # Create Course and ProgramCourse
        # new_course = Course(code=code, title=title, units=units)
        # db.session.add(new_course)
        # db.session.flush() # Flush to get the new_course.id

        try:
            units = int(units)
            course, existing_program_course = validate_course_data(
                code, title, units, program_id, level_id, semester_id, bulletin_id, course_type_id
            )

            if existing_program_course:
                errors.append(f'Course "{code}" is already in this program for the selected semester/bulletin.')
                continue
        
            # Create the new ProgramCourse association
            program_course = ProgramCourse(
                course_id=course.id,
                program_id=program_id,
                level_id=level_id,
                semester_id=semester_id,
                bulletin_id=bulletin_id
            )

            if specialization_id:
                specialization = Specialization.query.get(specialization_id)
                if specialization:
                    program_course.specializations.append(specialization)

            db.session.add(program_course)
            created_count += 1
        
        except (ValueError, TypeError) as e:
            errors.append(f"Invalid or non-numeric unit value for course {code}: '{units}'")
            continue

    db.session.commit() # Commit once after the loop, similar to specialization_service
    return created_count, errors

def validate_course_identifiers(course_id, program_id, level_id, semester_id, bulletin_id):
    # Basic validation
    if not all([course_id, program_id, level_id, semester_id, bulletin_id]):
        return None, "Missing one or more required identifiers (course, program, level, semester, bulletin)."
    
    try:
        # 2. Build the query with all unique fields and execute with .one()
        program_course = ProgramCourse.query.filter_by(
            course_id=course_id,
            program_id=program_id,
            level_id=level_id,
            semester_id=semester_id,
            bulletin_id=bulletin_id
        ).one()
    except NoResultFound:
        return None, "Program course not found with the specified details."
    except MultipleResultsFound:
        # This should ideally never happen if you have a unique constraint in your DB
        return None, "Error: Multiple records found. Data is inconsistent."
    
    return program_course, None


def update_course(program_course_id, data):
    # Fetch the SINGLE ProgramCourse instance using its primary key.
    program_course = ProgramCourse.query.get(program_course_id)
    
    # 2. Check if that instance was found.
    if not program_course:
        return None, "Program course not found"

    course = program_course.course

    # Update Course fields
    new_code = data.get('code')
    # Check if code is being changed to a new value
    if new_code and new_code != course.code:
        # Check if the new code already exists in the database
        existing_course = Course.query.filter_by(code=new_code).first()
        if existing_course:
            return None, f"Course code '{new_code}' already exists."
        course.code = new_code

    # Update other Course fields
    course.title = data.get('title', course.title)
    course.units = data.get('unit', course.units)
    course.course_type_id = data.get('course_type_id', course.course_type_id)

    # Update ProgramCourse fields

    # VALIDATE UNIQUENESS OF PROGRAMCOURSE SLOT BEFORE APPLYING CHANGES
    new_program_id = data.get('program_id', program_course.program_id)
    new_level_id = data.get('level_id', program_course.level_id)
    new_semester_id = data.get('semester_id', program_course.semester_id)
    new_bulletin_id = data.get('bulletin_id', program_course.bulletin_id)

    # Check if the slot is being changed
    if (new_program_id != program_course.program_id or
        new_level_id != program_course.level_id or
        new_semester_id != program_course.semester_id or
        new_bulletin_id != program_course.bulletin_id):
        
        # Check if the destination slot is already occupied by this course
        existing_slot = ProgramCourse.query.filter_by(
            course_id=course.id,
            program_id=new_program_id,
            level_id=new_level_id,
            semester_id=new_semester_id,
            bulletin_id=new_bulletin_id
        ).first()

        if existing_slot:
            return None, "This course is already assigned to the target program, level, semester, and bulletin."

        # If the slot is free, apply the changes
        program_course.program_id = new_program_id
        program_course.level_id = new_level_id
        program_course.semester_id = new_semester_id
        program_course.bulletin_id = new_bulletin_id

    # Update specialization
    if 'specialization_id' in data:
            specialization_id = data.get('specialization_id')
            # If specialization_id is None or 0, clear the specializations
            if not specialization_id:
                program_course.specializations = []
            else:
                specialization = Specialization.query.get(specialization_id)
                if specialization:
                    # Replace the list of specializations with a new list containing just this one
                    program_course.specializations = [specialization]

    try:
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        # This is a fallback for any unforseen constraint violations
        return None, f"A database integrity error occurred: {e}"

    return program_course, None

def delete_course(program_course_id):

    program_course = ProgramCourse.query.get(program_course_id)

    if not program_course:

        return False, "Program course not found"



    db.session.delete(program_course)

    db.session.commit()
    return True, None


# def get_courses_by_department(department_id, semester_id):
#     """
#     Gets all course for a given department and semester,
#     organized by program and level.
#     """

#     programs = Program.query.filter_by(department_id=department_id).all()
#     semester = db.session.get(Semester, semester_id)
#     session = AcademicSession.query.filter_by(is_active=True).first()
#     bulletins = Bulletin.query.all()

#     if not semester or not session:
#         return None, "Invalid semester or session."
#     output = []

#     for bulletin in bulletins:
#         bulletin_data = {"id": bulletin.id, "name": bulletin.name, "semester": []}

#         semester_data = {"sessionId": session.id, "sessionName": session.name, "id": semester.id, "name": semester.name, "department_name": programs[0].department.name, "programs": []}

#         for program in programs:
#             program_data = {"id": program.id, "name": program.name, "levels": []}
            
#             level_ids = (
#                 db.session.query(ProgramCourse.level_id)
#                 .filter_by(program_id=program.id)
#                 .distinct()
#                 .all()
#             )
            
#             for level_row in level_ids:
#                 level_id = level_row.level_id
#                 level = db.session.get(Level, level_id)

#                 level_data = {"id": str(level.id), "name": f"{level.name} Level", "courses": []}
                
#                 program_courses = ProgramCourse.query.filter_by(
#                     program_id=program.id, 
#                     level_id=level.id,
#                     semester_id=semester.id,
#                     bulletin_id=bulletin.id
#                 ).distinct()

#                 for pc in program_courses:
#                     course = pc.course

#                     level_data["courses"].append({
#                         "id": str(course.id),
#                         "code": course.code,
#                         "title": course.title,
#                         "unit": course.units
#                     })
                
#                 # Define a key for sorting: prioritize GST courses, then sort alphabetically.
#                 def sort_key(course):
#                     code = course.get("code", "")
#                     priority = 0 if code.startswith('BU-GST') or code.startswith('GST') else 1
#                     return (priority, code)

#                 # Sort the list of courses in-place using the custom key.
#                 level_data["courses"].sort(key=sort_key)

#                 if level_data["courses"]:
#                     program_data["levels"].append(level_data)

#             program_data["levels"].sort(key=lambda d: d.get("name") or "", reverse=False)
#             if program_data["levels"]:
#                 semester_data["programs"].append(program_data)

#         # if semester_data["programs"]:
#         bulletin_data["semester"].append(semester_data)

#         output.append(bulletin_data)
        
#     return output, None

def get_courses_by_department(department_id, semester_id):
    """
    Gets all courses for a given department and semester, organized by
    program, level, and specialization.
    """
    programs = Program.query.filter_by(department_id=department_id).all()
    semester = db.session.get(Semester, semester_id)
    session = AcademicSession.query.filter_by(is_active=True).first()
    bulletins = Bulletin.query.all()

    if not semester or not session:
        return None, "Invalid semester or session."
    
    output = []

    # Define a key for sorting courses: prioritize GST, then sort by code.
    def course_sort_key(course):
        code = course.get("code", "")
        priority = 0 if code.startswith('BU-GST') or code.startswith('GST') else 1
        return (priority, code)

    for bulletin in bulletins:
        bulletin_data = {"id": bulletin.id, "name": bulletin.name, "semester": []}
        semester_data = {"sessionId": session.id, "sessionName": session.name, "id": semester.id, "name": semester.name, "department_name": programs[0].department.name, "programs": []}

        for program in programs:
            program_data = {"id": program.id, "name": program.name, "levels": []}
            
            level_ids = db.session.query(ProgramCourse.level_id)\
                .filter_by(program_id=program.id)\
                .distinct().all()
            
            for level_row in level_ids:
                level_id = level_row.level_id
                level = db.session.get(Level, level_id)

                # Initialize with a 'specializations' list instead of a 'courses' list.
                level_data = {"id": str(level.id), "name": f"{level.name} Level", "specializations": []}
                
                program_courses = ProgramCourse.query.filter_by(
                    program_id=program.id, 
                    level_id=level.id,
                    semester_id=semester.id,
                    bulletin_id=bulletin.id
                ).distinct()

                # Create temporary structures to group courses by specialization.
                general_courses = []
                specialization_map = {} # Key: specialization_id, Value: specialization object

                for pc in program_courses:
                    course = pc.course
                    course_details = {
                        "id": str(course.id),
                        "code": course.code,
                        "title": course.title,
                        "unit": course.units
                    }

                    # Group courses into "General" or their specific specializations.
                    if not pc.specializations:
                        general_courses.append(course_details)
                    else:
                        for spec in pc.specializations:
                            if spec.id not in specialization_map:
                                specialization_map[spec.id] = {
                                    "id": spec.id,
                                    "name": spec.name,
                                    "courses": []
                                }
                            specialization_map[spec.id]["courses"].append(course_details)
                
                # Assemble the final specializations list for the level.
                # Add the "General" category first if it has any courses.
                if general_courses:
                    general_courses.sort(key=course_sort_key) # Sort courses within the group
                    level_data["specializations"].append({
                        "id": "general",
                        "name": "General",
                        "courses": general_courses
                    })
                
                # Add the other specialization categories.
                for spec_id in sorted(specialization_map.keys()): # Sort specializations by ID
                    spec_data = specialization_map[spec_id]
                    spec_data["courses"].sort(key=course_sort_key) # Sort courses within the group
                    level_data["specializations"].append(spec_data)

                if level_data["specializations"]:
                    program_data["levels"].append(level_data)

            program_data["levels"].sort(key=lambda d: d.get("name") or "", reverse=False)
            if program_data["levels"]:
                semester_data["programs"].append(program_data)

        bulletin_data["semester"].append(semester_data)
        output.append(bulletin_data)
        
    return output, None

    