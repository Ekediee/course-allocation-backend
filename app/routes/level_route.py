from flask import Blueprint, jsonify, request
from app.models.models import Level
from flask_jwt_extended import jwt_required, current_user
from app import db

level_bp = Blueprint("level", __name__)

@level_bp.route("/list", methods=["GET"])
@jwt_required()
def get_all_levels():

    if not current_user or not (current_user.is_superadmin or current_user.is_vetter):
        return jsonify({"msg": "Unauthorized – Only admin roles can views levels"}), 403
    
    levels = Level.query.order_by(Level.id).all()
    data = [
        {
            "id": level.id,
            "name": level.name
        } for level in levels
    ]
    return jsonify(data), 200

@level_bp.route('/create', methods=['POST'])
@jwt_required()
def create_level():
    if not current_user or not (current_user.is_superadmin or current_user.is_vetter):
        return jsonify({"msg": "Unauthorized – Only superadmin or vetter can create levels"}), 403

    data = request.get_json()
    name = data.get('name')

    if not name:
        return jsonify({'error': 'Name is required'}), 400

    if Level.query.filter_by(name=name).first():
        return jsonify({'error': 'Level with this name already exists'}), 409

    new_level = Level(name=name)
    db.session.add(new_level)
    db.session.commit()

    return jsonify({
        "msg": "Level created successfully",
        "level": {
            "id": new_level.id,
            "name": new_level.name
        }
    }), 201