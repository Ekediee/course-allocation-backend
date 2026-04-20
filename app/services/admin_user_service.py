import random
import string
from threading import Thread
from flask import current_app
import requests
from app.models.models import User, AdminUser, Department
from app.extensions import db, mail
from sqlalchemy.exc import IntegrityError
from flask_mail import Message
import os

def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

def generate_random_password(length=12):
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for i in range(length))

def send_credentials_email(email, password, role):
    msg = Message(
        'Your Admin Account for Course Allocation System',
        recipients=[email]
    )
    msg.body = f"""
    You have been added as an admin user for the Course Allocation System with the role of {role}.
    Your username is: {email}
    Your password is: {password}
    
    Please change your password after your first login.
    """
    app = current_app._get_current_object()
    thr = Thread(target=send_async_email, args=[app, msg])
    thr.start()
    return thr

def get_all_admin_users():
    try:
        admin_users = db.session.query(
            User.id,
            User.name,
            User.email,
            User.role,
            AdminUser.gender,
            AdminUser.phone,
            Department.name.label('department_name')
        ).join(AdminUser, User.admin_user_id == AdminUser.id)\
         .join(Department, AdminUser.department_id == Department.id)\
         .filter(User.role.in_(['admin', 'vetter', 'superadmin']))\
         .all()

        users_list = [{
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'role': user.role,
            'gender': user.gender,
            'phone': user.phone,
            'department': user.department_name
        } for user in admin_users] 
        
        return users_list, None
    except Exception as e:
        return None, str(e)

def create_admin_user(data):
    try:
        if User.query.filter_by(email=data['email']).first():
            return None, None, "Email already exists"

        password = generate_random_password()
        
        new_user = User(
            name=data['name'],
            email=data['email'],
            role=data['role'],
            department_id=data['department_id']
        )
        new_user.set_password(password)

        admin_profile = AdminUser(
            gender=data['gender'],
            phone=data['phone'],
            department_id=data['department_id']
        )

        new_user.admin_user = admin_profile
        
        db.session.add(new_user)
        db.session.add(admin_profile)
        
        db.session.commit()

        send_credentials_email(new_user.email, password, new_user.role)

        department = Department.query.get(admin_profile.department_id)

        user_data = {
            'id': new_user.id,
            'name': new_user.name,
            'email': new_user.email,
            'role': new_user.role,
            'gender': admin_profile.gender,
            'phone': admin_profile.phone,
            'department': department.name if department else None
        }
        return user_data, password, None
    except IntegrityError:
        db.session.rollback()
        return None, None, "Database integrity error."
    except Exception as e:
        db.session.rollback()
        return None, None, str(e)

def create_admin_users_batch(users_data):
    created_count = 0
    errors = []
    for index, user_data in enumerate(users_data):
        user, error = create_admin_user(user_data)
        if error:
            errors.append({'line': index + 1, 'error': error})
        else:
            created_count += 1
    
    return created_count, errors

def fetch_umis_faculties(umis_token, umisid):
    """
    Fetches faculties from UMIS
    """
    print(f"Fetching faculty data from UMIS for ID: {umisid} with token: {umis_token}")
    # FETCH CLASS OPTION DATA
    faculty_api = f"{os.getenv('UMIS_INSTRUCTOR_URL')}{umisid}"
    header = {
        'action': 'read',
        'authorization': umis_token
    }
    resp = requests.get(faculty_api, headers=header)

    if resp.status_code != 200:
        return None, f"Failed to fetch faculty data ({resp.status_code})"
    
    faculty_list = resp.json()
    
    if 'data' not in faculty_list or not isinstance(faculty_list['data'], list):
        return None, "Invalid faculty data format from UMIS"

    if 'data' in faculty_list:
        sorted_faculty_list = sorted(
            [{
                'id': faculty.get('instructorid'),
                'instructorname': faculty.get('instructorname'),
                'email': faculty.get('email'),
                'departmentid': faculty.get('departmentid'),
                'departmentname': faculty.get('departmentname'),
                'schoolid': faculty.get('schoolid'),
                'schoolname': faculty.get('schoolname'),
            } for faculty in faculty_list.get('data')],
            key=lambda faculty: faculty.get('name', '')
        )

        return sorted_faculty_list, None
                        
    return None, "Faculty not found in UMIS data"
    

