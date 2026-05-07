from flask import jsonify
from app.blueprints.api import api_bp

@api_bp.route('/')
def index():
    return jsonify({"status": "ok", "message": "GymTrack API"})
