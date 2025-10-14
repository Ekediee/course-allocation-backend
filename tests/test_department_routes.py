import json
from tests.conftest import create_test_school

def test_update_department(client, superadmin_token):
    # Create a school and a department to update
    school = create_test_school(client, superadmin_token)
    department_data = {
        "name": "Initial Department",
        "school_id": school['id'],
        "acronym": "ID"
    }
    client.post('/api/v1/departments/create', headers={'Authorization': f'Bearer {superadmin_token}'}, json=department_data)
    department = json.loads(client.get('/api/v1/departments/list', headers={'Authorization': f'Bearer {superadmin_token}'}).data)['departments'][0]

    # Update the department
    update_data = {
        "name": "Updated Department",
        "school_id": school['id'],
        "acronym": "UD"
    }
    response = client.put(f"/api/v1/departments/update/{department['id']}", headers={'Authorization': f'Bearer {superadmin_token}'}, json=update_data)
    assert response.status_code == 200
    assert json.loads(response.data)['message'] == 'Department updated successfully'

    # Verify the update
    response = client.get('/api/v1/departments/list', headers={'Authorization': f'Bearer {superadmin_token}'})
    updated_department = json.loads(response.data)['departments'][0]
    assert updated_department['name'] == 'Updated Department'
    assert updated_department['acronym'] == 'UD'

def test_delete_department(client, superadmin_token):
    # Create a school and a department to delete
    school = create_test_school(client, superadmin_token)
    department_data = {
        "name": "Department to Delete",
        "school_id": school['id'],
        "acronym": "DTD"
    }
    client.post('/api/v1/departments/create', headers={'Authorization': f'Bearer {superadmin_token}'}, json=department_data)
    department = json.loads(client.get('/api/v1/departments/list', headers={'Authorization': f'Bearer {superadmin_token}'}).data)['departments'][0]

    # Delete the department
    response = client.delete(f"/api/v1/departments/delete/{department['id']}", headers={'Authorization': f'Bearer {superadmin_token}'})
    assert response.status_code == 200
    assert json.loads(response.data)['message'] == 'Department deleted successfully'

    # Verify the deletion
    response = client.get('/api/v1/departments/list', headers={'Authorization': f'Bearer {superadmin_token}'})
    departments = json.loads(response.data)['departments']
    assert len(departments) == 0