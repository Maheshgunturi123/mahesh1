from flask import render_template
from app.blueprints.exercises import exercises_bp

@exercises_bp.route('/')
def index():
    return render_template('base.html')
