import pytest
import json
from app import create_app, db
from app.models.models import User, Department, School, Level
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

def test_create_level(test_client):
    # Test successful creation with superadmin
    headers = get_auth_headers("super@admin.com")
    response = test_client.post('/api/v1/levels/create',
                           headers=headers,
                           data=json.dumps({'name': '100'}),
                           content_type='application/json')
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['msg'] == 'Level created successfully'
    assert data['level']['name'] == '100'

    # Test unauthorized creation with non-admin role (e.g., no token)
    response = test_client.post('/api/v1/levels/create',
                           data=json.dumps({'name': '200'}),
                           content_type='application/json')
    assert response.status_code == 401

    # Test missing name
    headers = get_auth_headers("super@admin.com")
    response = test_client.post('/api/v1/levels/create',
                           headers=headers,
                           data=json.dumps({}),
                           content_type='application/json')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['error'] == 'Name is required'

    # Test duplicate name
    response = test_client.post('/api/v1/levels/create',
                           headers=headers,
                           data=json.dumps({'name': '100'}),
                           content_type='application/json')
    assert response.status_code == 409
    data = json.loads(response.data)
    assert data['error'] == 'Level with this name already exists'

def test_get_all_levels(test_client):
    # Create a level first
    headers = get_auth_headers("super@admin.com")
    test_client.post('/api/v1/levels/create',
                headers=headers,
                data=json.dumps({'name': '200'}),
                content_type='application/json')

    # Test get all levels with superadmin
    headers = get_auth_headers("super@admin.com")
    response = test_client.get('/api/v1/levels/list',
                          headers=headers)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)
    assert len(data) > 0
    assert any(level['name'] == '200' for level in data)

    # Test unauthorized get without token
    response = test_client.get('/api/v1/levels/list')
    assert response.status_code == 401
