from flask import Blueprint, jsonify, request
from app.models import Level
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