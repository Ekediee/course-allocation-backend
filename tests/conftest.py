import sys
import os
import pytest
from app import create_app, db
from app.models.models import User, School
from flask_jwt_extended import create_access_token
import json

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture(scope='session')
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture(scope='function')
def superadmin_token(app):
    with app.app_context():
        superadmin = User(name='superadmin', email='superadmin@test.com', role='superadmin')
        superadmin.set_password('superadmin')
        db.session.add(superadmin)
        db.session.commit()
        access_token = create_access_token(identity=superadmin.id)
        yield access_token
        db.session.delete(superadmin)
        db.session.commit()

def create_test_school(client, token):
    school_data = {
        "name": "Test School",
        "acronym": "TS"
    }
    response = client.post('/api/v1/schools/create', headers={'Authorization': f'Bearer {token}'}, json=school_data)
    return json.loads(response.data)["bulletin"]