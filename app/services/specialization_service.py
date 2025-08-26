from app import db
from app.models.models import Specialization

def create_specialization(name, program_id):
    if Specialization.query.filter_by(name=name, program_id=program_id).first():
        return None, f"Specialization '{name}' already exists for this program"

    new_specialization = Specialization(name=name, program_id=program_id)
    db.session.add(new_specialization)
    db.session.commit()
    return new_specialization, None

def get_specializations():
    return Specialization.query.order_by(Specialization.id).all()

def get_specialization_names_by_program(program_id):
    return Specialization.query.filter_by(program_id=program_id).all()

def batch_create_specializations(specializations):
    created_count = 0
    errors = []
    
    for spec_data in specializations:
        name = spec_data.get('name')
        program_id = spec_data.get('program_id')

        if not name or not program_id:
            errors.append(f"Missing 'name' or 'program_id' in record: {spec_data}")
            continue

        if Specialization.query.filter_by(name=name, program_id=program_id).first():
            errors.append(f"Specialization '{name}' already exists for program_id {program_id}")
            continue

        new_specialization = Specialization(name=name, program_id=program_id)
        db.session.add(new_specialization)
        created_count += 1

    db.session.commit()
    return created_count, errors
