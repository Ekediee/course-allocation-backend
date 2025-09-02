from flask_jwt_extended import jwt_required, current_user
from flask import Blueprint, request, jsonify
from app import db
from app.models.models import School, CourseAllocation, User
from icecream import ic

school_bp = Blueprint('schools', __name__)

@school_bp.route('/create', methods=['POST'])
@jwt_required()
def create_school():

    ic(current_user.is_vetter)

    if not current_user or not (current_user.is_superadmin or current_user.is_vetter):
        return jsonify({"msg": "Unauthorized – Only superadmin can create schools"}), 403

    data = request.get_json()
    name = data.get('name')
    acronym = data.get('acronym')

    

    if not name:
        return jsonify({'error': 'School name is required'}), 400

    if School.query.filter_by(name=name).first():
        return jsonify({'error': f"School - '{name}' already exists"}), 400

    # Create new school
    new_school = School(name=name, acronym=acronym)
    db.session.add(new_school)
    db.session.flush()

    db.session.commit()
    # return jsonify({'message': f"Session '{name}' initialized by superadmin."}), 201
    return jsonify({
        "msg": f"School '{name}' created and activated successfully",
        "bulletin": {
            "id": new_school.id,
            "name": new_school.name,
            "acronym": new_school.acronym
        }
    }), 201


@school_bp.route('/list', methods=['GET'])
@jwt_required()
def get_schools():

    if not current_user or not (current_user.is_superadmin or current_user.is_vetter):
        return jsonify({"msg": "Unauthorized – Only superadmin can fetch schools"}), 403

    schools = School.query.order_by(School.id).filter(School.acronym.notin_(['SVAD'])).all()
    
    return jsonify({
        "schools": [
            {
                "id": school.id,
                "name": school.name,
                "acronym": school.acronym
            } for school in schools
        ]
    }), 200

@school_bp.route('/lists', methods=['GET'])
@jwt_required()
def get_schools_names():

    if not current_user or not (current_user.is_superadmin or current_user.is_vetter):
        return jsonify({"msg": "Unauthorized – Only superadmin can fetch schools"}), 403

    schools = School.query.order_by(School.id).filter(School.acronym.notin_(['SVAD'])).all()
    
    return jsonify({
        "schools": [
            {
                "id": school.id,
                "name": school.name,
            } for school in schools
        ]
    }), 200

@school_bp.route('/lists/admin', methods=['GET'])
@jwt_required()
def get_schools_names_admin():

    if not current_user or not (current_user.is_superadmin or current_user.is_vetter):
        return jsonify({"msg": "Unauthorized – Only superadmin can fetch schools"}), 403

    schools = School.query.order_by(School.id).filter(School.acronym.in_(['SVAD'])).all()
    
    return jsonify({
        "schools": [
            {
                "id": school.id,
                "name": school.name,
            } for school in schools
        ]
    }), 200

@school_bp.route('/batch', methods=['POST'])
@jwt_required()
def batch_upload():

    if not current_user or not (current_user.is_superadmin or current_user.is_vetter):
        return jsonify({"error": "Unauthorized – Only superadmin can create schools"}), 403
    
    data = request.get_json()

    print("Received data for batch upload:", data)
    schools = data.get('schools', [])

    created = []
    for schl in schools:
        name = schl.get('name')
        acronym = schl.get('acronym')
        if name and acronym:
            school = School(name=name, acronym=acronym)
            db.session.add(school)
            created.append(name)

    db.session.commit()

    return jsonify({
        "message": f"Successfully uploaded {len(created)} schools.",
        "schools_created": created
    })
