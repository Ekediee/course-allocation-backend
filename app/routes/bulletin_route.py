from flask_jwt_extended import jwt_required, current_user
from flask import Blueprint, request, jsonify
from app import db
from app.models.models import Bulletin, CourseAllocation, User
from icecream import ic

bulletin_bp = Blueprint('bulletins', __name__)

@bulletin_bp.route('/create', methods=['POST'])
@jwt_required()
def create_bulletin():

    ic(current_user.is_vetter)

    if not current_user or not (current_user.is_superadmin or current_user.is_vetter):
        return jsonify({"msg": "Unauthorized – Only superadmin can create bulletins"}), 403

    data = request.get_json()
    name = data.get('name')
    start_year = data.get('start_year')
    end_year = data.get('end_year')

    

    if not name:
        return jsonify({'error': 'Bulletin name is required'}), 400

    if Bulletin.query.filter_by(name=name).first():
        return jsonify({'error': f"Bulletin - '{name}' already exists"}), 400
    
    # Deactivate current active bulletin
    Bulletin.query.update({Bulletin.is_active: False})

    # Create new bulletin
    new_bulletin = Bulletin(name=name, start_year=start_year, end_year=end_year, is_active=True)
    db.session.add(new_bulletin)
    db.session.flush()

    db.session.commit()
    # return jsonify({'message': f"Session '{name}' initialized by superadmin."}), 201
    return jsonify({
        "msg": f"Bulletin '{name}' created and activated successfully",
        "bulletin": {
            "id": new_bulletin.id,
            "name": new_bulletin.name,
            "start_year": new_bulletin.start_year,
            "end_year": new_bulletin.end_year
        }
    }), 201


@bulletin_bp.route('/list', methods=['GET'])
@jwt_required()
def get_bulletin():

    if not current_user or not (current_user.is_superadmin or current_user.is_vetter):
        return jsonify({"msg": "Unauthorized – Only superadmin can fetch bulletins"}), 403

    bulletins = Bulletin.query.order_by(Bulletin.id).all()
    
    return jsonify({
        "bulletins": [
            {
                "id": bulletin.id,
                "name": bulletin.name,
                "start_year": bulletin.start_year,
                "end_year": bulletin.end_year,
                "is_active": bulletin.is_active
            } for bulletin in bulletins
        ]
    }), 200
