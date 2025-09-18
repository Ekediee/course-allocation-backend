import pytest
from unittest.mock import patch
from app import create_app, db
from app.models.models import User, Department, School, Lecturer
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
    school = School(name="Education And Humanities", acronym="EAH")
    db.session.add(school)
    db.session.commit()

    department = Department(name="Religious Studies", acronym="RELB", school_id=school.id)
    db.session.add(department)
    db.session.commit()
    
    lecturer = User(name="Existing Lecturer", email="lecturer@test.com", role="lecturer", department_id=department.id)
    lecturer.set_password("lecturerpass")
    
    hod = User(name="Existing HOD", email="hod@test.com", role="hod", department_id=department.id)
    hod.set_password("hodpass")

    db.session.add_all([lecturer, hod])
    db.session.commit()

@patch('app.auth.umis_login.auth_user')
def test_umis_login_new_hod(mock_auth_user, test_client):
    mock_auth_user.return_value = ({
        'instructorname': 'New HOD',
        'departmentname': 'Religious Studies',
        'headofdepartment': 'Yes',
        'email': 'newhod@test.com',
        'instructorid': 'NEWHOD001'
    }, None)

    data = {'umisid': 'someid', 'password': 'somepassword'}
    
    response = test_client.post('/api/v1/auth/umis/login', json=data)
    
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['user']['name'] == 'New HOD'
    assert json_data['user']['role'] == 'hod'

    new_hod = User.query.filter_by(email='newhod@test.com').first()
    assert new_hod is not None
    assert new_hod.role == 'hod'

    old_hod = User.query.filter_by(email='hod@test.com').first()
    assert old_hod.role == 'lecturer'

@patch('app.auth.umis_login.auth_user')
def test_umis_login_existing_lecturer(mock_auth_user, test_client):
    mock_auth_user.return_value = ({
        'instructorname': 'Existing Lecturer',
        'departmentname': 'Religious Studies',
        'headofdepartment': 'No',
        'email': 'lecturer@test.com',
        'instructorid': 'LECT001'
    }, None)

    data = {'umisid': 'someid', 'password': 'somepassword'}
    
    response = test_client.post('/api/v1/auth/umis/login', json=data)
    
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['user']['name'] == 'Existing Lecturer'
    assert json_data['user']['role'] == 'lecturer'

    lecturer = User.query.filter_by(email='lecturer@test.com').first()
    assert lecturer.role == 'lecturer'
