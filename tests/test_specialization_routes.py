import pytest
from app import create_app, db
from app.models.models import School, Department, Program, User, Specialization
from flask_jwt_extended import create_access_token

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
    school = School(name="School of Engineering", acronym="SOE")
    db.session.add(school)
    db.session.commit()

    department = Department(name="Software Engineering", acronym="SWE", school_id=school.id)
    db.session.add(department)
    db.session.commit()

    program = Program(name="B.Eng. Software Engineering", department_id=department.id, acronym="SWE")
    admin_user = User(name="Admin User", email="admin@test.com", role="superadmin")
    admin_user.set_password("password")

    db.session.add_all([program, admin_user])
    db.session.commit()

def get_auth_headers(user_email):
    user = User.query.filter_by(email=user_email).first()
    access_token = create_access_token(identity=str(user.id))
    return {'Authorization': f'Bearer {access_token}'}

def test_create_specialization(test_client):
    headers = get_auth_headers("admin@test.com")
    program = Program.query.first()
    data = {"name": "Cloud Computing", "program_id": program.id}

    response = test_client.post('/api/v1/specializations/create', json=data, headers=headers)
    assert response.status_code == 201
    json_data = response.get_json()
    assert json_data['msg'] == "Specialization 'Cloud Computing' created successfully"
    assert json_data['specialization']['name'] == "Cloud Computing"

def test_get_specializations(test_client):
    headers = get_auth_headers("admin@test.com")
    program = Program.query.first()
    spec = Specialization(name="AI", program_id=program.id)
    db.session.add(spec)
    db.session.commit()

    response = test_client.get('/api/v1/specializations/list', headers=headers)
    assert response.status_code == 200
    json_data = response.get_json()
    assert len(json_data['specializations']) > 0
    assert json_data['specializations'][0]['name'] == "AI"

def test_get_specialization_names_by_program(test_client):
    headers = get_auth_headers("admin@test.com")
    program = Program.query.first()
    spec = Specialization(name="Data Science", program_id=program.id)
    db.session.add(spec)
    db.session.commit()

    data = {"program_id": program.id}
    response = test_client.post('/api/v1/specializations/names/list', json=data, headers=headers)
    assert response.status_code == 200
    json_data = response.get_json()
    assert len(json_data['specializations']) > 0
    assert json_data['specializations'][0]['name'] == "Data Science"

def test_batch_upload_specializations(test_client):
    headers = get_auth_headers("admin@test.com")
    program = Program.query.first()
    data = {
        "specializations": [
            {"name": "Cybersecurity", "program_id": program.id},
            {"name": "Networking", "program_id": program.id}
        ]
    }

    response = test_client.post('/api/v1/specializations/batch-upload', json=data, headers=headers)
    assert response.status_code == 201
    json_data = response.get_json()
    assert json_data['message'] == "Successfully created 2 specializations."
