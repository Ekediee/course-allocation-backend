import pytest
from app import create_app, db
from app.models.models import School, Department, Program, User, Level, Semester, Bulletin, Course, ProgramCourse
from flask_jwt_extended import create_access_token
import io

@pytest.fixture(scope='function')
def test_client():
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
    school = School(name="School of Science", acronym="SOS")
    db.session.add(school)
    db.session.commit()

    department = Department(name="Computer Science", acronym="CS", school_id=school.id)
    db.session.add(department)
    db.session.commit()

    program = Program(name="B.Sc. Computer Science", department_id=department.id, acronym="CSC")
    db.session.add(program)
    db.session.commit()

    level = Level(name="100")
    semester = Semester(name="First")
    bulletin = Bulletin(name="2023-2027", start_year=2023, end_year=2027)
    admin_user = User(name="Admin User", email="admin@test.com", role="superadmin")
    admin_user.set_password("password")

    db.session.add_all([level, semester, bulletin, admin_user])
    db.session.commit()

def get_auth_headers(user_email):
    user = User.query.filter_by(email=user_email).first()
    access_token = create_access_token(identity=str(user.id))
    return {'Authorization': f'Bearer {access_token}'}

def test_get_all_courses(test_client):
    headers = get_auth_headers("admin@test.com")
    response = test_client.get('/api/v1/courses', headers=headers)
    assert response.status_code == 200
    json_data = response.get_json()
    assert "courses" in json_data

def test_create_course(test_client):
    headers = get_auth_headers("admin@test.com")
    program = Program.query.first()
    level = Level.query.first()
    semester = Semester.query.first()
    bulletin = Bulletin.query.first()

    data = {
        "code": "CS101",
        "title": "Intro to Programming",
        "unit": 3,
        "program_id": program.id,
        "level_id": level.id,
        "semester_id": semester.id,
        "bulletin_id": bulletin.id,
        "specialization_id": None
    }

    response = test_client.post('/api/v1/courses', json=data, headers=headers)
    assert response.status_code == 201
    json_data = response.get_json()
    assert json_data['msg'] == "Course created successfully."
    assert json_data['course']['code'] == "CS101"

def test_batch_create_courses(test_client):
    headers = get_auth_headers("admin@test.com")
    program = Program.query.first()
    level = Level.query.first()
    semester = Semester.query.first()
    bulletin = Bulletin.query.first()

    csv_data = "course_code,course_title,course_unit\nCS102,Data Structures,3\nCS201,Algorithms,3"
    data = {
        'file': (io.BytesIO(csv_data.encode('utf-8')), 'test.csv'),
        'program_id': program.id,
        'level_id': level.id,
        'semester_id': semester.id,
        'bulletin_id': bulletin.id
    }

    response = test_client.post('/api/v1/courses/batch', data=data, headers=headers, content_type='multipart/form-data')
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['message'] == "Successfully created 2 courses."
