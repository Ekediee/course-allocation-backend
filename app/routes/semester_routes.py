from flask import Blueprint, jsonify, request
from app.models import Semester
from flask_jwt_extended import jwt_required, current_user
from app import db

semester_bp = Blueprint("semester", __name__)

@semester_bp.route("/list", methods=["GET"])
@jwt_required()
def get_all_semesters():

    if not current_user or not (current_user.is_superadmin or current_user.is_vetter):
        return jsonify({"msg": "Unauthorized – Only admin roles can views semesters"}), 403
    
    semesters = Semester.query.order_by(Semester.id).all()
    data = [
        {
            "id": semester.id,
            "name": semester.name
        } for semester in semesters
    ]
    return jsonify(data), 200

@semester_bp.route('/create', methods=['POST'])
@jwt_required()
def create_semester():

    if not current_user or not (current_user.is_superadmin or current_user.is_vetter):
        return jsonify({"msg": "Unauthorized – Only admin users can create semesters"}), 403

    data = request.get_json()
    semester_name = data.get('name')

    

    if not semester_name:
        return jsonify({'error': 'Sesmester name is required'}), 400

    if Semester.query.filter_by(name=semester_name).first():
        return jsonify({'error': f"The semester - '{semester_name}' already exists"}), 400
    
    # Create new session
    new_semester = Semester(name=semester_name)
    db.session.add(new_semester)
    db.session.flush()

    db.session.commit()
    # return jsonify({'message': f"Session '{session_name}' initialized by superadmin."}), 201
    return jsonify({
        "msg": f"'{new_semester.name}' created and activated successfully",
        "session": {
            "id": new_semester.id,
            "name": new_semester.name
        }
    }), 201
