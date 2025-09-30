
import pytest
from app import create_app, db
from app.models import (
    School, Department, User, Lecturer, Program, Level, Semester,
    Course, Bulletin, AcademicSession, ProgramCourse, CourseAllocation,
    DepartmentAllocationState
)
from flask_jwt_extended import create_access_token

@pytest.fixture(scope='module')
def test_client():
    """
    Creates a test client for the Flask application.
    This fixture is run once per module.
    """
    flask_app = create_app(config_name='testing')

    flask_app.config['JWT_SECRET_KEY'] = 'super-secret-testing-key'
    flask_app.config['JWT_COOKIE_CSRF_PROTECT'] = False

    with flask_app.test_client() as testing_client:
        with flask_app.app_context():
            db.create_all()
            setup_test_data()
            yield testing_client
            db.session.remove()
            db.drop_all()

def setup_test_data():
    """Populates the database with test data for allocation status overview."""
    # Users
    superadmin = User(name="Super Admin", email="super@admin.com", role="superadmin")
    superadmin.set_password("superadminpass")
    vetter = User(name="Dr. Vetter", email="vetter@test.com", role="vetter")
    vetter.set_password("vetterpass")
    hod = User(name="Dr. HOD", email="hod@test.com", role="hod")
    hod.set_password("hodpass")
    db.session.add_all([superadmin, vetter, hod])
    db.session.commit()

    # School
    school = School(name="Test School", acronym="TS")
    db.session.add(school)
    db.session.commit()

    # Departments
    cs_dept = Department(name="Computer Science", acronym="CS", school_id=school.id)
    eco_dept = Department(name="Economics", acronym="ECO", school_id=school.id)
    db.session.add_all([cs_dept, eco_dept])
    db.session.commit()

    # Link HOD to a department
    hod_lec = Lecturer(staff_id="HOD001", department_id=cs_dept.id)
    hod.lecturer = hod_lec
    db.session.add(hod_lec)
    db.session.commit()

    # Semesters & Session
    sem1 = Semester(name="First Semester")
    sem2 = Semester(name="Second Semester")
    session = AcademicSession(name="2024/2025", is_active=True)
    db.session.add_all([sem1, sem2, session])
    db.session.commit()

    # Programs
    cs_prog = Program(name="B.Sc. CS", department_id=cs_dept.id, acronym="CSC")
    eco_prog = Program(name="B.Sc. Eco", department_id=eco_dept.id, acronym="ECO")
    db.session.add_all([cs_prog, eco_prog])
    db.session.commit()

    # Course, Level, Bulletin
    course1 = Course(code="CS101", title="Intro to CS", units=3)
    course2 = Course(code="ECO101", title="Intro to Eco", units=3)
    level100 = Level(name="100")
    bulletin = Bulletin(name="2024-2028", start_year=2024, end_year=2028, is_active=True)
    db.session.add_all([course1, course2, level100, bulletin])
    db.session.commit()

    # Program Courses
    pc_cs = ProgramCourse(program_id=cs_prog.id, course_id=course1.id, level_id=level100.id, semester_id=sem1.id, bulletin_id=bulletin.id)
    pc_eco = ProgramCourse(program_id=eco_prog.id, course_id=course2.id, level_id=level100.id, semester_id=sem1.id, bulletin_id=bulletin.id)
    db.session.add_all([pc_cs, pc_eco])
    db.session.commit()

    # Simulating Statuses for First Semester
    # 1. CS Dept: Allocated (Submitted)
    cs_submission = DepartmentAllocationState(department_id=cs_dept.id, semester_id=sem1.id, session_id=session.id, submitted_by_id=superadmin.id)
    db.session.add(cs_submission)
    
    # 2. Eco Dept: Still Allocating (Has allocations but not submitted)
    eco_allocation = CourseAllocation(program_course_id=pc_eco.id, session_id=session.id, semester_id=sem1.id, lecturer_id=hod_lec.id, is_allocated=True)
    db.session.add(eco_allocation)
    
    db.session.commit()

def test_get_allocation_status_overview_as_superadmin(test_client):
    """
    GIVEN a superadmin user
    WHEN the '/allocation-status-overview' endpoint is called
    THEN check for a 200 response and validate the data returned.
    """
    superadmin = User.query.filter_by(email="super@admin.com").first()
    access_token = create_access_token(identity=str(superadmin.id))
    headers = {'Authorization': f'Bearer {access_token}'}

    response = test_client.get('/api/v1/allocation/allocation-status-overview', headers=headers)
    data = response.get_json()

    assert response.status_code == 200
    assert isinstance(data, list)
    assert len(data) == 2  # First and Second semesters

    # First Semester checks
    sem1_data = next((s for s in data if s['name'] == 'First Semester'), None)
    assert sem1_data is not None
    
    cs_status = next((d for d in sem1_data['departments'] if d['department_name'] == 'Computer Science'), None)
    assert cs_status['status'] == 'Allocated'

    eco_status = next((d for d in sem1_data['departments'] if d['department_name'] == 'Economics'), None)
    assert eco_status['status'] == 'Still Allocating'

    # Second Semester checks (should be 'Not Started' for both)
    sem2_data = next((s for s in data if s['name'] == 'Second Semester'), None)
    assert sem2_data is not None

    cs_status_sem2 = next((d for d in sem2_data['departments'] if d['department_name'] == 'Computer Science'), None)
    assert cs_status_sem2['status'] == 'Not Started'

    eco_status_sem2 = next((d for d in sem2_data['departments'] if d['department_name'] == 'Economics'), None)
    assert eco_status_sem2['status'] == 'Not Started'

def test_get_allocation_status_overview_as_vetter(test_client):
    """
    GIVEN a vetter user
    WHEN the '/allocation-status-overview' endpoint is called
    THEN check for a 200 response.
    """
    vetter = User.query.filter_by(email="vetter@test.com").first()
    access_token = create_access_token(identity=str(vetter.id))
    headers = {'Authorization': f'Bearer {access_token}'}

    response = test_client.get('/api/v1/allocation/allocation-status-overview', headers=headers)
    assert response.status_code == 200

def test_get_allocation_status_overview_unauthorized(test_client):
    """
    GIVEN a non-superadmin/non-vetter user (e.g., HOD)
    WHEN the '/allocation-status-overview' endpoint is called
    THEN check for a 403 Forbidden response.
    """
    hod = User.query.filter_by(email="hod@test.com").first()
    access_token = create_access_token(identity=str(hod.id))
    headers = {'Authorization': f'Bearer {access_token}'}

    response = test_client.get('/api/v1/allocation/allocation-status-overview', headers=headers)
    assert response.status_code == 403
