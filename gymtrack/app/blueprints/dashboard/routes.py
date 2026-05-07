from flask import render_template
from app.blueprints.dashboard import dashboard_bp

@dashboard_bp.route('/')
def index():
    return render_template('base.html')
