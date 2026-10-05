import uuid
from app.models.models import User, Lecturer, Department
from app.extensions import db
from sqlalchemy import desc

def get_all_users():
    """
    Retrieves all users and their associated lecturer and department information.
    """
    try:
        users_query = db.session.query(
            User.id, User.name, User.email, User.role,
            Lecturer.gender, Lecturer.staff_id, Lecturer.phone, Lecturer.rank, Lecturer.specialization,
            Lecturer.qualification, Lecturer.other_responsibilities,
            Department.name.label('department_name')
        ).outerjoin(Lecturer, User.lecturer_id == Lecturer.id).join(Department, User.department_id == Department.id).order_by(desc(User.id))
        
        users = users_query.filter(Department.name.notin_(['Registry', 'Academic Planning'])).all()

        user_list = [{
            "id": u.id, "name": u.name, "email": u.email, "role": u.role,
            "gender": u.gender, "staff_id": u.staff_id, "phone": u.phone, "rank": u.rank,
            "specialization": u.specialization, "qualification": u.qualification,
            "other_responsibilities": u.other_responsibilities, "department": u.department_name
        } for u in users]
        return user_list, None
    except Exception as e:
        return None, str(e)

def create_user(data):
    """
    Creates a new user and, if applicable, a corresponding lecturer profile.
    """

    try:
        lecturer_id = None
        role = data.get('role').lower()
        if role in ['lecturer', 'hod']:
            staff_id = data.get('staff_id')
            if not staff_id:
                staff_id = str(uuid.uuid4())
            new_lecturer = Lecturer(
                staff_id=staff_id,
                gender=data.get('gender').title(), phone=data.get('phone'), rank=data.get('rank'),
                specialization=data.get('specialization'), qualification=data.get('qualification'),
                other_responsibilities=data.get('other_responsibilities'),
                department_id=data.get('department_id')
            )
            db.session.add(new_lecturer)
            db.session.flush()
            lecturer_id = new_lecturer.id

        email = data.get('email')
        if not email:
            email = None # This will be translated to NULL

        new_user = User(
            name=data.get('name').title(), email=email, role=data.get('role'),
            department_id=data.get('department_id'), lecturer_id=lecturer_id
        )
        # new_user.set_password('default_password')
        db.session.add(new_user)
        db.session.commit()

        department = Department.query.get(new_user.department_id)
        user_data = {
            "id": new_user.id, "name": new_user.name, "email": new_user.email,
            "role": new_user.role, "department": department.name if department else None
        }
        if new_user.lecturer_id:
            lecturer = Lecturer.query.get(new_user.lecturer_id)
            user_data.update({
                "gender": lecturer.gender, "phone": lecturer.phone, "rank": lecturer.rank,
                "specialization": lecturer.specialization, "qualification": lecturer.qualification,
                "other_responsibilities": lecturer.other_responsibilities
            })
        return user_data, None
    except Exception as e:
        db.session.rollback()
        return None, str(e)

def create_users_batch(users_data):
    """
    Creates multiple users from a list of user data.
    """
    created_count = 0
    errors = []
    for user_data in users_data:
        _, error = create_user(user_data)
        if error:
            errors.append(error)
        else:
            created_count += 1
    return created_count, errors if errors else None

def update_user(user_id, data):
    """
    Updates a user and their associated lecturer profile.
    """
    try:
        user = User.query.get(user_id)
        if not user:
            return None, "User not found"

        user.name = data.get('name', user.name)
        user.email = data.get('email', user.email)
        user.role = data.get('role', user.role)
        user.department_id = data.get('department_id', user.department_id)

        if user.lecturer:
            lecturer = user.lecturer
            lecturer.gender = data.get('gender', lecturer.gender)
            lecturer.phone = data.get('phone', lecturer.phone)
            lecturer.rank = data.get('rank', lecturer.rank)
            lecturer.specialization = data.get('specialization', lecturer.specialization)
            lecturer.qualification = data.get('qualification', lecturer.qualification)
            lecturer.other_responsibilities = data.get('other_responsibilities', lecturer.other_responsibilities)

        db.session.commit()

        department = Department.query.get(user.department_id)
        user_data = {
            "id": user.id, "name": user.name, "email": user.email,
            "role": user.role, "department": department.name if department else None
        }
        if user.lecturer:
            lecturer = user.lecturer
            user_data.update({
                "gender": lecturer.gender, "phone": lecturer.phone, "rank": lecturer.rank,
                "specialization": lecturer.specialization, "qualification": lecturer.qualification,
                "other_responsibilities": lecturer.other_responsibilities
            })
        return user_data, None
    except Exception as e:
        db.session.rollback()
        return None, str(e)

def delete_user(user_id):
    """
    Deletes a user and their associated lecturer profile.
    """
    try:
        user = User.query.get(user_id)
        if not user:
            return None, "User not found"

        if user.lecturer:
            db.session.delete(user.lecturer)
        
        db.session.delete(user)
        db.session.commit()
        return True, None
    except Exception as e:
        db.session.rollback()
        return None, str(e)

def get_lecturers_grouped_by_department():
    """
    Fetches users with role 'lecturer' or 'hod', grouped by department,
    excluding 'Registry' and 'Academic Planning' departments.
    """
    try:
        excluded_depts = ['Registry', 'Academic Planning']
        
        departments = Department.query.filter(Department.name.notin_(excluded_depts)).all()
        
        result = []
        for dept in departments:
            # Join User and Lecturer
            users = db.session.query(
                User.name, User.email, User.role,
                Lecturer.staff_id, Lecturer.gender, Lecturer.rank,
                Lecturer.qualification, Lecturer.specialization, Lecturer.other_responsibilities
            ).join(Lecturer, User.lecturer_id == Lecturer.id)\
             .filter(User.department_id == dept.id)\
             .filter(User.role.in_(['lecturer', 'hod'])).all()
            
            if users:
                dept_data = {
                    "name": dept.name,
                    "lecturers": []
                }
                for u in users:
                    lecturer_data = {
                        "staff_id": u.staff_id,
                        "name": u.name,
                        "role": u.role,
                        "gender": u.gender,
                        "email": u.email,
                        "rank": u.rank,
                        "qualification": u.qualification,
                        "specialization": u.specialization,
                        "other_responsibilities": u.other_responsibilities
                    }
                    dept_data["lecturers"].append(lecturer_data)
                
                result.append(dept_data)
                
        return {"departments": result}, 200
    except Exception as e:
        return {"error": str(e)}, 500
