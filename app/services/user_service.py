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
            Lecturer.gender, Lecturer.phone, Lecturer.rank, Lecturer.specialization,
            Lecturer.qualification, Lecturer.other_responsibilities,
            Department.name.label('department_name')
        ).outerjoin(Lecturer, User.lecturer_id == Lecturer.id).join(Department, User.department_id == Department.id).order_by(desc(User.id))
        
        users = users_query.filter(Department.name.notin_(['Registry', 'Academic Planning'])).all()

        user_list = [{
            "id": u.id, "name": u.name, "email": u.email, "role": u.role,
            "gender": u.gender, "phone": u.phone, "rank": u.rank,
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
        if data.get('role') in ['lecturer', 'hod']:
            new_lecturer = Lecturer(
                staff_id=data.get('staff_id'),
                gender=data.get('gender'), phone=data.get('phone'), rank=data.get('rank'),
                specialization=data.get('specialization'), qualification=data.get('qualification'),
                other_responsibilities=data.get('other_responsibilities'),
                department_id=data.get('department_id')
            )
            db.session.add(new_lecturer)
            db.session.flush()
            lecturer_id = new_lecturer.id

        new_user = User(
            name=data.get('name'), email=data.get('email'), role=data.get('role'),
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