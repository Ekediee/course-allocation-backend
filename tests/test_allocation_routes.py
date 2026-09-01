import pytest
from app import create_app, db
from app.models import (
    School, Department, User, Lecturer, Program, Level, Semester,
    Course, Bulletin, AcademicSession, ProgramCourse, Specialization, CourseAllocation
)
from flask_jwt_extended import create_access_token

@pytest.fixture(scope='function')
def test_client():
    """
    Creates a test client for the Flask application.
    This fixture is run once per module.
    """
    flask_app = create_app(config_name='testing')

    # Explicitly set JWT_SECRET_KEY for testing
    flask_app.config['JWT_SECRET_KEY'] = 'super-secret-testing-key'
    flask_app.config['JWT_COOKIE_CSRF_PROTECT'] = False

    # Create a test client using the Flask application configured for testing
    with flask_app.test_client() as testing_client:
        # Establish an application context
        with flask_app.app_context():
            db.create_all()
            # Setup initial data
            setup_test_data()
            yield testing_client  # this is where the testing happens!
            db.session.remove()
            db.drop_all()

def setup_test_data():
    """Populates the database with test data."""
    # Create entities
    school = School(name="School of Science", acronym="SOS")
    department = Department(name="Computer Science", acronym="CS", school=school)
    
    hod_user = User(name="Dr. HOD", email="hod@test.com", role="hod")
    hod_user.set_password("password")
    
    lecturer_profile = Lecturer(staff_id="HOD001")
    department.lecturers.append(lecturer_profile)
    hod_user.lecturer = lecturer_profile
    
    db.session.add_all([school, department, hod_user, lecturer_profile])
    db.session.commit()

    program = Program(name="B.Sc. Computer Science", department_id=department.id, acronym="CSC")
    level100 = Level(name="100")
    level300 = Level(name="300")
    semester = Semester(name="First Semester")
    bulletin = Bulletin(name="2024-2028", start_year=2024, end_year=2028, is_active=True)
    session = AcademicSession(name="2024/2025", is_active=True)
    
    db.session.add_all([program, level100, level300, semester, bulletin, session])
    db.session.commit()

    # Courses
    cosc101 = Course(code="COSC101", title="Intro to CS", units=3)
    cosc301 = Course(code="COSC301", title="OS", units=3)
    seng302 = Course(code="SENG302", title="Software Design", units=3)
    db.session.add_all([cosc101, cosc301, seng302])
    db.session.commit()

    # Specialization
    swe_spec = Specialization(name="Software Engineering", program_id=program.id)
    db.session.add(swe_spec)
    db.session.commit()

    # Program Courses
    pc_cosc101 = ProgramCourse(program_id=program.id, course_id=cosc101.id, level_id=level100.id, semester_id=semester.id, bulletin_id=bulletin.id)
    pc_cosc301 = ProgramCourse(program_id=program.id, course_id=cosc301.id, level_id=level300.id, semester_id=semester.id, bulletin_id=bulletin.id)
    pc_seng302 = ProgramCourse(program_id=program.id, course_id=seng302.id, level_id=level300.id, semester_id=semester.id, bulletin_id=bulletin.id)
    
    db.session.add_all([pc_cosc101, pc_cosc301, pc_seng302])
    db.session.commit()

    # Link specialization to course
    pc_seng302.specializations.append(swe_spec)
    db.session.commit()

    # Allocation
    allocation = CourseAllocation(program_course_id=pc_cosc101.id, session_id=session.id, semester_id=semester.id, lecturer_id=lecturer_profile.id, is_allocated=True)
    db.session.add(allocation)
    db.session.commit()


def test_get_hod_allocations_by_specialization(test_client):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/allocations/list-by-specialization' endpoint is called by an HOD
    THEN check that the response is valid and contains the correct structure
    """
    # Get HOD user
    hod_user = User.query.filter_by(email="hod@test.com").first()
    access_token = create_access_token(identity=str(hod_user.id))
    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    response = test_client.get('/api/v1/allocation/list-by-specialization', headers=headers)
    data = response.get_json()

    # Assertions
    assert response.status_code == 200
    assert isinstance(data, list)
    assert len(data) == 1 # Should have one semester

    program_data = data[0]['programs'][0]
    assert program_data['name'] == "B.Sc. Computer Science"
    
    # Find 100 Level data
    level100_data = next((l for l in program_data['levels'] if l['name'] == '100 Level'), None)
    assert level100_data is not None
    assert level100_data['specializations'][0]['name'] == 'General'
    assert level100_data['specializations'][0]['courses'][0]['code'] == 'COSC101'
    assert level100_data['specializations'][0]['courses'][0]['isAllocated'] == True

    # Find 300 Level data
    level300_data = next((l for l in program_data['levels'] if l['name'] == '300 Level'), None)
    assert level300_data is not None
    
    # Check for general course at 300 level
    general_300 = next((s for s in level300_data['specializations'] if s['name'] == 'General'), None)
    assert general_300 is not None
    assert general_300['courses'][0]['code'] == 'COSC301'

    # Check for specialization course at 300 level
    swe_300 = next((s for s in level300_data['specializations'] if s['name'] == 'Software Engineering'), None)
    assert swe_300 is not None
    assert swe_300['courses'][0]['code'] == 'SENG302'


def test_get_allocations_by_session_and_semester_success(test_client):
    """Should return 200 with allocations grouped by semester then program when both session_id and semester_id are provided."""
    session = AcademicSession.query.filter_by(name="2024/2025").first()
    semester = Semester.query.filter_by(name="First Semester").first()

    response = test_client.get(f'/api/v1/allocation/by-session?session_id={session.id}&semester_id={semester.id}')
    assert response.status_code == 200

    data = response.get_json()
    assert data["session"]["id"] == session.id
    assert len(data["semesters"]) == 1
    assert data["semesters"][0]["id"] == semester.id
    assert len(data["semesters"][0]["programs"]) == 1

    program_data = data["semesters"][0]["programs"][0]
    assert program_data["name"] == "B.Sc. Computer Science"
    assert len(program_data["courses"]) == 1

    course_data = program_data["courses"][0]
    assert course_data["code"] == "COSC101"
    assert course_data["title"] == "Intro to CS"
    assert course_data["unit"] == 3
    assert course_data["lecturer"]["name"] == "Dr. HOD"
    assert course_data["lecturer"]["staff_id"] == "HOD001"


def test_get_allocations_by_session_only_success(test_client):
    """Should return 200 with allocations for all semesters in the session when semester_id is omitted."""
    session = AcademicSession.query.filter_by(name="2024/2025").first()

    response = test_client.get(f'/api/v1/allocation/by-session?session_id={session.id}')
    assert response.status_code == 200

    data = response.get_json()
    assert data["session"]["id"] == session.id
    assert len(data["semesters"]) >= 1


def test_get_allocations_missing_session_id(test_client):
    """Should return 400 when session_id query parameter is missing."""
    response = test_client.get('/api/v1/allocation/by-session')
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data


def test_get_allocations_invalid_session_id(test_client):
    """Should return 404 when session_id does not exist."""
    response = test_client.get('/api/v1/allocation/by-session?session_id=99999')
    assert response.status_code == 404
    data = response.get_json()
    assert "error" in data


def test_get_allocations_invalid_semester_id(test_client):
    """Should return 404 when semester_id does not exist."""
    session = AcademicSession.query.filter_by(name="2024/2025").first()
    response = test_client.get(f'/api/v1/allocation/by-session?session_id={session.id}&semester_id=99999')
    assert response.status_code == 404
    data = response.get_json()
    assert "error" in data

