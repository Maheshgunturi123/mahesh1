from flask import render_template, redirect, url_for, flash
from flask_login import login_user, current_user
from app.blueprints.auth import auth_bp
from app.blueprints.auth.forms import RegistrationForm
from app.models import User
from app.extensions import db


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash('Account created. Welcome to GymTrack!', 'success')
        return redirect(url_for('dashboard.index'))
    return render_template('auth/register.html', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Stub — implemented in Story 1.3
    return render_template('base.html')
