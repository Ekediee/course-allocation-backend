import pytest
import json
from app import create_app, db
from app.models.models import User, Department, School, CourseType
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
    
    hod = User(name="HOD User", email="hod@user.com", role="hod", department_id=department.id)
    hod.set_password("hodpass")

    db.session.add_all([superadmin, hod])
    db.session.commit()

def get_auth_headers(user_email):
    user = User.query.filter_by(email=user_email).first()
    access_token = create_access_token(identity=str(user.id))
    return {'Authorization': f'Bearer {access_token}'}

def test_create_course_type(test_client):
    # Test successful creation with superadmin
    headers = get_auth_headers("super@admin.com")
    response = test_client.post('/api/v1/course-types/create',
                           headers=headers,
                           data=json.dumps({'name': 'General'}),
                           content_type='application/json')
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['msg'] == 'Course type created successfully'
    assert data['course_type']['name'] == 'General'

    # Test unauthorized creation with hod
    headers = get_auth_headers("hod@user.com")
    response = test_client.post('/api/v1/course-types/create',
                           headers=headers,
                           data=json.dumps({'name': 'Core'}),
                           content_type='application/json')
    assert response.status_code == 403

    # Test missing name
    headers = get_auth_headers("super@admin.com")
    response = test_client.post('/api/v1/course-types/create',
                           headers=headers,
                           data=json.dumps({}),
                           content_type='application/json')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['error'] == 'Name is required'

    # Test duplicate name
    response = test_client.post('/api/v1/course-types/create',
                           headers=headers,
                           data=json.dumps({'name': 'General'}),
                           content_type='application/json')
    assert response.status_code == 409
    data = json.loads(response.data)
    assert data['error'] == 'Course type with this name already exists'

def test_get_course_types(test_client):
    # Create a course type first
    headers = get_auth_headers("super@admin.com")
    test_client.post('/api/v1/course-types/create',
                headers=headers,
                data=json.dumps({'name': 'Elective'}),
                content_type='application/json')

    # Test get all course types with hod
    headers = get_auth_headers("hod@user.com")
    response = test_client.get('/api/v1/course-types/list',
                          headers=headers)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)
    assert len(data) > 0
    assert any(ct['name'] == 'Elective' for ct in data)

    # Test unauthorized get without token
    response = test_client.get('/api/v1/course-types/list')
    assert response.status_code == 401
