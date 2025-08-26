from app import db
from app.models.models import Course, ProgramCourse, Specialization
import csv

def get_all_courses():
    program_courses = ProgramCourse.query.all()
    return program_courses

def create_course(data):
    code = data.get('code')
    title = data.get('title')
    units = data.get('unit')
    program_id = data.get('program_id')
    level_id = data.get('level_id')
    semester_id = data.get('semester_id')
    bulletin_id = data.get('bulletin_id')
    specialization_id = data.get('specialization_id')

    if Course.query.filter_by(code=code).first():
        return None, f'Course with code "{code}" already exists'

    new_course = Course(code=code, title=title, units=units)
    db.session.add(new_course)
    db.session.flush()  # Flush to get the new_course.id

    program_course = ProgramCourse(
        course_id=new_course.id,
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

    return new_course, None

def batch_create_courses(file, bulletin_id, program_id, semester_id, level_id, specialization_id):
    created_count = 0
    errors = []

    try:
        stream = file.stream.read().decode("UTF8")
        csv_reader = csv.DictReader(stream.splitlines())
    except Exception as e:
        return 0, [f"Failed to read CSV file: {e}"]

    for row in csv_reader:
        code = row.get('course_code')
        title = row.get('course_title')
        units = row.get('course_unit')

        if not code or not title or not units:
            errors.append(f"Missing data in row: {row}")
            continue

        if Course.query.filter_by(code=code).first():
            errors.append(f'Course with code "{code}" already exists')
            continue

        try:
            units = int(units)
        except ValueError:
            errors.append(f"Invalid unit value for course {code}: {units}")
            continue

        new_course = Course(code=code, title=title, units=units)
        db.session.add(new_course)
        db.session.flush()

        program_course = ProgramCourse(
            course_id=new_course.id,
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

    db.session.commit()
    return created_count, errors
