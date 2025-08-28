import pytest
from app import create_app, db
from app.models.models import User, Department, School
from flask_jwt_extended import create_access_token

@pytest.fixture(scope='function')
def test_client():
    flask_app = create_app(config_name='testing')
    flask_app.config['JWT_SECRET_KEY'] = 'super-secret-testing-key'
    
    with flask_app.test_client() as testing_client:
        with flask_app.app_context():
            db.create_all()
            setup_test_data()
            yield testing_client
            db.session.remove()
            db.drop_all()

def setup_test_data():
    school = School(name="Test School", acronym="TS")
    db.session.add(school)
    db.session.commit()

    department = Department(name="Test Department", acronym="TD", school_id=school.id)
    db.session.add(department)
    db.session.commit()
    
    superadmin = User(name="Super Admin", email="super@admin.com", role="superadmin", department_id=department.id)
    superadmin.set_password("superadminpass")
    
    vetter = User(name="Vetter User", email="vetter@user.com", role="vetter", department_id=department.id)
    vetter.set_password("vetterpass")

    db.session.add_all([superadmin, vetter])
    db.session.commit()

def get_auth_headers(user_email):
    user = User.query.filter_by(email=user_email).first()
    access_token = create_access_token(identity=str(user.id))
    return {'Authorization': f'Bearer {access_token}'}

def test_get_all_users(test_client):
    headers = get_auth_headers("super@admin.com")
    response = test_client.get('/api/v1/users', headers=headers)
    assert response.status_code == 200
    json_data = response.get_json()
    assert "users" in json_data
    assert isinstance(json_data["users"], list)

def test_create_lecturer_user(test_client):
    headers = get_auth_headers("super@admin.com")
    department = Department.query.first()
    data = {
        "name": "Test Lecturer",
        "email": "lecturer@test.com",
        "role": "lecturer",
        "department_id": department.id,
        "gender": "Male",
        "phone": "1234567890",
        "rank": "Senior Lecturer",
        "specialization": "AI",
        "qualification": "PhD"
    }
    response = test_client.post('/api/v1/users', json=data, headers=headers)
    assert response.status_code == 201
    json_data = response.get_json()
    assert json_data['msg'] == "User created successfully"
    assert json_data['user']['email'] == "lecturer@test.com"
    assert json_data['user']['role'] == "lecturer"
    assert json_data['user']['rank'] == "Senior Lecturer"

def test_create_user_by_vetter(test_client):
    headers = get_auth_headers("vetter@user.com")
    department = Department.query.first()
    data = {
        "name": "Another Lecturer",
        "email": "lecturer2@test.com",
        "role": "lecturer",
        "department_id": department.id,
        "gender": "Female"
    }
    response = test_client.post('/api/v1/users', json=data, headers=headers)
    assert response.status_code == 201
    json_data = response.get_json()
    assert json_data['msg'] == "User created successfully"

def test_batch_create_users(test_client):
    headers = get_auth_headers("super@admin.com")
    department = Department.query.first()
    data = {
        "users": [
            {
                "name": "Batch User 1",
                "email": "batch1@test.com",
                "role": "lecturer",
                "department_id": department.id,
                "gender": "Male"
            },
            {
                "name": "Batch User 2",
                "email": "batch2@test.com",
                "role": "hod",
                "department_id": department.id,
                "gender": "Female"
            }
        ]
    }
    response = test_client.post('/api/v1/users/batch', json=data, headers=headers)
    assert response.status_code == 201
    json_data = response.get_json()
    assert json_data['message'] == "Successfully created 2 users."
