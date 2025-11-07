from app.extensions import db
from datetime import datetime, timezone
# from werkzeug.security import generate_password_hash, check_password_hash
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

# Association table for the many-to-many relationship
# between ProgramCourse and Specialization
program_course_specializations = db.Table('program_course_specializations',
    db.Column('program_course_id', db.Integer, db.ForeignKey('program_course.id'), primary_key=True),
    db.Column('specialization_id', db.Integer, db.ForeignKey('specialization.id'), primary_key=True)
)

class School(db.Model):
    __tablename__ = 'school'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    acronym = db.Column(db.String(10), nullable=True)  # e.g., "SMS", "EAH"

    departments = db.relationship('Department', backref='school', lazy=True)


class Department(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    acronym = db.Column(db.String(10), nullable=True)  # e.g., "CS", "BSAD"

    school_id = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=False)

    programs = db.relationship('Program', backref='department', lazy=True)
    users = db.relationship('User', backref='department', lazy=True)
    lecturers = db.relationship('Lecturer', backref='department', lazy=True)
    admin_users = db.relationship('AdminUser', backref='department', lazy=True)


class Lecturer(db.Model):
    __tablename__ = 'lecturer'

    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.String(50), unique=True, nullable=False)
    gender = db.Column(db.String(50), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    rank = db.Column(db.String(50), nullable=True)  # e.g., Professor
    specialization = db.Column(db.String(254), nullable=True) # Area of specialization
    qualification = db.Column(db.String(100), nullable=True)
    other_responsibilities = db.Column(db.String(100), nullable=True)

    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=False)

    allocations = db.relationship('CourseAllocation', backref='lecturer_profile', lazy=True)


class AdminUser(db.Model):
    __tablename__ = 'admin_user'

    id = db.Column(db.Integer, primary_key=True)
    gender = db.Column(db.String(50), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=False)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=True)
    role = db.Column(
        db.Enum("superadmin", "admin", "vetter", "hod", "lecturer", name="user_roles"),
        nullable=False
    )  # superadmin, 'hod' or 'lecturer'
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=True)
    
    lecturer_id = db.Column(db.Integer, db.ForeignKey('lecturer.id'), unique=True, nullable=True)
    admin_user_id = db.Column(db.Integer, db.ForeignKey('admin_user.id'), unique=True, nullable=True)
    password = db.Column(db.String(128), nullable=True)
    lecturer = db.relationship('Lecturer', backref='user_account', uselist=False)
    admin_user = db.relationship('AdminUser', backref='user_account', uselist=False)

    @property
    def is_hod(self):
        return self.role == 'hod'

    @property
    def is_superadmin(self):
        return self.role == 'superadmin'
    
    @property
    def is_admin(self):
        return self.role == 'admin'
    
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
    acronym = db.Column(db.String(10), nullable=True)  # e.g., "EDPA", "BSAD"

    # Relationship to Specialization
    specializations = db.relationship('Specialization', backref='program', lazy=True, cascade="all, delete-orphan")


class Specialization(db.Model):
    __tablename__ = 'specialization'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    program_id = db.Column(db.Integer, db.ForeignKey('program.id'), nullable=False)


class CourseType(db.Model):
    __tablename__ = 'course_type'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)


class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), nullable=False, unique=True)
    title = db.Column(db.String(255), nullable=False)
    units = db.Column(db.Integer, nullable=True)
    course_type_id = db.Column(db.Integer, db.ForeignKey('course_type.id'), nullable=True)

    course_type = db.relationship('CourseType', backref='courses')


class Semester(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)

    allocations = db.relationship('CourseAllocation', backref='semester', lazy=True)


class Level(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False, unique=True)


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
    
    # Relationship to Specialization
    specializations = db.relationship('Specialization', secondary=program_course_specializations,
                                      lazy='subquery', backref=db.backref('program_courses', lazy=True))


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
    class_option = db.Column(db.String(50), nullable=True)  
    is_lead = db.Column(db.Boolean, default=False)
    is_allocated = db.Column(db.Boolean, default=False)

    is_de_allocation = db.Column(db.Boolean, default=False)
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


class DepartmentAllocationState(db.Model):
    __tablename__ = 'department_allocation_state'

    id = db.Column(db.Integer, primary_key=True)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('academic_session.id'), nullable=False)
    semester_id = db.Column(db.Integer, db.ForeignKey('semester.id'), nullable=False)
    is_submitted = db.Column(db.Boolean, default=False, nullable=False)
    submitted_at = db.Column(db.DateTime, nullable=True)
    submitted_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    is_vetted = db.Column(db.Boolean, default=False, nullable=False)
    vetted_at = db.Column(db.DateTime, nullable=True)
    vetted_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    department = db.relationship('Department', backref='allocation_states')
    session = db.relationship('AcademicSession', backref='allocation_states')
    semester = db.relationship('Semester', backref='allocation_states')
    submitted_by = db.relationship('User', backref='submitted_allocations', foreign_keys=[submitted_by_id])
    vetted_by = db.relationship('User', backref='vetted_allocations', foreign_keys=[vetted_by_id])

    __table_args__ = (
        db.UniqueConstraint('department_id', 'session_id', 'semester_id', name='_department_session_semester_uc'),
    )

class AppSetting(db.Model):
    __tablename__ = 'app_setting'

    id = db.Column(db.Integer, primary_key=True)
    # The name of the setting, e.g., 'maintenance_mode'
    setting_name = db.Column(db.String(50), unique=True, nullable=False)
    # The value of the setting
    is_enabled = db.Column(db.Boolean, default=False, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

    def __repr__(self):
        return f'<AppSetting {self.setting_name}={self.is_enabled}>'