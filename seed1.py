from app import db
from app.models import (
    School, Department, Program, Course, Level, Semester, 
    Bulletin, ProgramCourse, User, Lecturer
)
from faker import Faker
import random
from icecream import ic

fake = Faker()

# === Clear tables (for dev reset only) ===
db.session.query(User).delete()
db.session.query(Lecturer).delete()
db.session.query(ProgramCourse).delete()
db.session.query(Course).delete()
db.session.query(Program).delete()
db.session.query(Department).delete()
db.session.query(School).delete()
db.session.query(Bulletin).delete()
db.session.query(Level).delete()
db.session.query(Semester).delete()
db.session.commit()

# === Core Entities ===
school = School(name="School of Computing")
db.session.add(school)
db.session.flush()

cs_department = Department(name="Computer Science", school_id=school.id)
db.session.add(cs_department)
db.session.flush()

programs = [
    Program(name="Information Technology", department_id=cs_department.id),
    Program(name="Software Engineering", department_id=cs_department.id),
]
db.session.add_all(programs)
db.session.flush()

levels = [Level(name=f"{lvl}L") for lvl in [100, 200, 300, 400]]
semesters = [Semester(name="First Semester"), Semester(name="Second Semester")]
db.session.add_all(levels + semesters)
db.session.flush()

bulletin = Bulletin(name="2023-2027", start_year=2023, end_year=2027, is_active=True)
db.session.add(bulletin)
db.session.flush()

# === Courses and ProgramCourses ===
courses = []
program_courses = []

for program in programs:
    for level in levels:
        for semester in semesters:
            for i in range(10):
                code = f"{program.name[:4].upper()}{level.name[:1]}{semester.name[0]}{i+1:02d}"
                title = f"{fake.catch_phrase()}"
                course = Course(code=code, title=title)
                db.session.add(course)
                db.session.flush()
                courses.append(course)

                pc = ProgramCourse(
                    program_id=program.id,
                    course_id=course.id,
                    level_id=level.id,
                    semester_id=semester.id,
                    bulletin_id=bulletin.id,
                    units=random.choice([2, 3]),
                    # grouping_enabled=random.choice([True, False])
                )
                program_courses.append(pc)


# === Lecturers ===
lecturers = [
    Lecturer(
        staff_id="CS001",
        phone="08012345678",
        rank="Professor",
        qualification="PhD",
        department_id=cs_department.id
    ),
    Lecturer(
        staff_id="CS002",
        phone="08023456789",
        rank="Senior Lecturer",
        qualification="PhD",
        department_id=cs_department.id
    ),
    Lecturer(
        staff_id="CS003",
        phone="08034567890",
        rank="Lecturer I",
        qualification="MSc",
        department_id=cs_department.id
    )
]
db.session.add_all(lecturers)
db.session.flush()

# === Users (Login Access) ===
hod_user = User(
    name="Ebiesuwa Oluwaseun",
    email="ebiesuwa@babcock.edu.ng",
    role="hod",
    department_id=cs_department.id,
    lecturer_id=lecturers[0].id
)

lecturer_users = [
    User(
        name=fake.name(),
        email=f"{fake.user_name()}@babcock.edu.ng",
        role="lecturer",
        department_id=cs_department.id,
        lecturer_id=lec.id
    )
    for lec in lecturers[1:]
]

# === Finalize DB Inserts ===
db.session.add_all(program_courses)
db.session.add(hod_user)
db.session.add_all(lecturer_users)
db.session.commit()

ic("✅ Seeded School, Department, Programs, Courses, Lecturers, Users.")