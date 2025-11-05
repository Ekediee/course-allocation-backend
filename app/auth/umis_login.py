from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, set_access_cookies
from app.models.models import User, Department, Lecturer
from app.services.umis_auth_service import auth_user
from app import db

umis_auth_bp = Blueprint('umis-auth', __name__)

def generate_email_from_name(name):
    parts = name.strip().lower().split()
    if len(parts) >= 2:
        return f"{parts[0]}{parts[1][0]}@babcock.edu.ng"
    elif len(parts) == 1:
        return f"{parts[0]}@babcock.edu.ng"
    else:
        # Fallback for empty or unusual names
        return f"user_{db.session.query(User).count() + 1}@babcock.edu.ng"

@umis_auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('umisid') or not data.get('password'):
        return jsonify({"msg": "UMIS ID and password are required"}), 400

    # Authenticate with UMIS
    instructor_data, error = auth_user(data)
    if error:
        print(error)
        return jsonify({"msg": f"UMIS authentication failed: {error}"}), 400
    
    if not instructor_data:
        return jsonify({"msg": "UMIS authentication failed: Invalid credentials or user not found"}), 400

    # Extract data from UMIS response
    instructor_name = instructor_data.get('instructorname')
    department_name = instructor_data.get('departmentname')
    is_hod = instructor_data.get('headofdepartment') == 'Yes'
    email = instructor_data.get('email')
    staff_id = instructor_data.get('instructorid')

    if not is_hod:
        return jsonify({"msg": f"Invalid credentials - only HOD's can access this resource"}), 403

    # Find department in local DB
    department = Department.query.filter_by(name=department_name).first()
    if not department:
        return jsonify({"msg": f"Department '{department_name}' not found in the system"}), 404

    # Find user in local DB by name
    user = User.query.filter(User.name.ilike(f"%{instructor_name.strip()}%")).first()

    if is_hod:
        # Find the current HOD in the department and update their role to 'lecturer'
        current_hod = User.query.filter_by(department_id=department.id, role='hod').first()
        if current_hod and (not user or current_hod.id != user.id):
            current_hod.role = 'lecturer'
            db.session.add(current_hod)

    if not user:
        # Create a new user if they don't exist
        new_lecturer = Lecturer(staff_id=staff_id, department_id=department.id)
        db.session.add(new_lecturer)
        db.session.flush()  # Flush to get the new_lecturer.id

        generated_email = generate_email_from_name(instructor_name)

        new_user = User(
            name=instructor_name,
            email=email if email else generated_email,
            role='hod' if is_hod else 'lecturer',
            department_id=department.id,
            lecturer_id=new_lecturer.id
        )
        db.session.add(new_user)
        user = new_user
    else:
        # Update existing user's role if they are now a HOD
        if is_hod and user.role != 'hod':
            user.role = 'hod'
            db.session.add(user)

    db.session.commit()

    # Generate access token
    token = create_access_token(identity=str(user.id))

    # Build user info
    user_info = {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
    }

    if user.lecturer:
        user_info.update({
            "department": user.lecturer.department.name if user.lecturer.department else None,
            "rank": user.lecturer.rank,
            "qualification": user.lecturer.qualification
        })
    else:
        user_info.update({
            "department": None,
            "rank": None,
            "qualification": None
        })

    resp = jsonify({
        "access_token": token,
        "user": user_info
    })

    set_access_cookies(resp, token)
    return resp
