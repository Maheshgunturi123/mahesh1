from flask import render_template
from app.blueprints.admin import admin_bp

@admin_bp.route('/')
def index():
    return render_template('base.html')
