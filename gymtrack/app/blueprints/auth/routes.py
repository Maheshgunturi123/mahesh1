from flask import render_template
from app.blueprints.auth import auth_bp

@auth_bp.route('/')
def index():
    return render_template('base.html')
