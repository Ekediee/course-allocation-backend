from app import db
from datetime import datetime, timezone
# from werkzeug.security import generate_password_hash, check_password_hash
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

class School(db.Model):
    __tablename__ = 'school'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    departments = db.relationship('Department', backref='school', lazy=True)


class Department(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    school_id = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=False)

    programs = db.relationship('Program', backref='department', lazy=True)
    users = db.relationship('User', backref='department', lazy=True)
    lecturers = db.relationship('Lecturer', backref='department', lazy=True)


class Lecturer(db.Model):
    __tablename__ = 'lecturer'

    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.String(50), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    rank = db.Column(db.String(50), nullable=True)  # e.g., Professor
    qualification = db.Column(db.String(100), nullable=True)

    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=False)

    allocations = db.relationship('CourseAllocation', backref='lecturer_profile', lazy=True)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'hod' or 'lecturer'
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=True)
    
    lecturer_id = db.Column(db.Integer, db.ForeignKey('lecturer.id'), unique=True, nullable=True)
    password = db.Column(db.String(128), nullable=True)
    lecturer = db.relationship('Lecturer', backref='user_account', uselist=False)

    @property
    def is_hod(self):
        return self.role == 'hod'

    @property
    def is_superadmin(self):
        return self.role == 'superadmin'
    
    @property
    def is_vetter(self):
        return self.role == 'vetter'

    @property
    def is_lecturer(self):
        return self.role == 'lecturer'
    
    # === Handle Secure Password ===
    def set_password(self, password):
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)


class Program(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=False)

    # program_courses = db.relationship('ProgramCourse', backref='program', lazy=True)


class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), nullable=False, unique=True)
    title = db.Column(db.String(255), nullable=False)
    units = db.Column(db.Integer, nullable=True)

    # program_courses = db.relationship('ProgramCourse', backref='course', lazy=True)


class Semester(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)

    allocations = db.relationship('CourseAllocation', backref='semester', lazy=True)

    # program_courses = db.relationship('ProgramCourse', backref='semester', lazy=True)


class Level(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False, unique=True)

    # program_courses = db.relationship('ProgramCourse', backref='level', lazy=True)


# class ProgramCourse(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     program_id = db.Column(db.Integer, db.ForeignKey('program.id'), nullable=False)
#     course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
#     semester_id = db.Column(db.Integer, db.ForeignKey('semester.id'), nullable=False)
#     level_id = db.Column(db.Integer, db.ForeignKey('level.id'), nullable=False)
#     units = db.Column(db.Integer, nullable=False)

#     course_allocations = db.relationship('CourseAllocation', backref='program_course', lazy=True)

class ProgramCourse(db.Model):
    __tablename__ = 'program_course'

    id = db.Column(db.Integer, primary_key=True)

    program_id = db.Column(db.Integer, db.ForeignKey('program.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    level_id = db.Column(db.Integer, db.ForeignKey('level.id'), nullable=False)
    semester_id = db.Column(db.Integer, db.ForeignKey('semester.id'), nullable=False)
    bulletin_id = db.Column(db.Integer, db.ForeignKey('bulletin.id'), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, onupdate=datetime.now(timezone.utc))


    # Relationships
    program = db.relationship('Program', backref='program_courses')
    course = db.relationship('Course', backref='program_courses')
    level = db.relationship('Level', backref='program_courses')
    semester = db.relationship('Semester', backref='program_courses')
    bulletin = db.relationship('Bulletin', backref='program_courses')

    course_allocations = db.relationship(
        'CourseAllocation',
        backref='program_course',
        cascade='all, delete-orphan',
        lazy=True
    )


class AcademicSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    is_active = db.Column(db.Boolean, default=False)

    allocations = db.relationship('CourseAllocation', backref='session', lazy=True)



class CourseAllocation(db.Model):
    __table_args__ = (
        db.UniqueConstraint('program_course_id', 'session_id', 'group_name', name='uq_allocation_group'),
    )

    id = db.Column(db.Integer, primary_key=True)

    program_course_id = db.Column(db.Integer, db.ForeignKey('program_course.id'), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('academic_session.id'), nullable=False)
    semester_id = db.Column(db.Integer, db.ForeignKey('semester.id'), nullable=False)
    lecturer_id = db.Column(db.Integer, db.ForeignKey('lecturer.id'), nullable=True)

    group_name = db.Column(db.String(20), nullable=True)  # NULL = no group (single allocation)
    is_lead = db.Column(db.Boolean, default=False)
    is_allocated = db.Column(db.Boolean, default=False)

    is_special_allocation = db.Column(db.Boolean, default=False)
    source_bulletin_id = db.Column(db.Integer, db.ForeignKey('bulletin.id'), nullable=True)
    class_size = db.Column(db.Integer, nullable=True)  # e.g., 100

    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, onupdate=datetime.now(timezone.utc))


    source_bulletin = db.relationship('Bulletin')


class Bulletin(db.Model):
    __tablename__ = 'bulletin'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)  # e.g., "2019–2023"
    start_year = db.Column(db.Integer, nullable=False)
    end_year = db.Column(db.Integer, nullable=False)
    is_active = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, onupdate=datetime.now(timezone.utc))
