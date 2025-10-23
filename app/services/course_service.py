from app import db
from app.models.models import Course, ProgramCourse, Specialization
from sqlalchemy import desc

def get_all_courses():
    program_courses = ProgramCourse.query.order_by(desc(ProgramCourse.id)).all()
    return program_courses

def validate_course_data(code, title, units, program_id, level_id, semester_id, bulletin_id):
    # Try to find the course by its unique code.
    course = Course.query.filter_by(code=code).first()

    if not course:
        # If the course does not exist, create it.
        course = Course(code=code, title=title, units=units)
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

    # if Course.query.filter_by(code=code).first():
    #     return None, f'Course with code "{code}" already exists'

    # new_course = Course(code=code, title=title, units=units)
    # db.session.add(new_course)
    # db.session.flush()  # Flush to get the new_course.id

    course, existing_program_course = validate_course_data(
        code, title, units, program_id, level_id, semester_id, bulletin_id
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

        # Basic validation
        if not all([code, title, units, bulletin_id, program_id, semester_id, level_id]):
            errors.append(f"Missing required fields in record: {course_item}")
            continue

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
                code, title, units, program_id, level_id, semester_id, bulletin_id
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
            errors.append(f"Invalid unit value or data type error for course {code}: {e}")
            continue

    db.session.commit() # Commit once after the loop, similar to specialization_service
    return created_count, errors