from app.models import Student, Teacher, User, RoleEnum
from werkzeug.security import check_password_hash, generate_password_hash
from flask import (
    Blueprint, flash, g, logging, redirect, render_template, request, session, url_for
)
import functools
from ..db import db
import logging

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

bp = Blueprint('auth', __name__, url_prefix='/')


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username:
            flash('Username is required.', 'error')
            return render_template('auth/register.html')

        if not password:
            flash('Password is required.', 'error')
            return render_template('auth/register.html')


        if User.query.filter_by(username=username).first():
            flash(f'User {username} is already registered.', 'error')
            return render_template('auth/register.html')

        hashed_password = generate_password_hash(password)
        user = User(username=username, password=hashed_password, role='teacher',fullname=request.form.get('fullname'))

        try:
            db.session.add(user)
            db.session.commit()

            if user.role == 'teacher':
                teacher = Teacher(user_id=user.id)
                db.session.add(teacher)
            elif user.role == 'student':
                student = Student(user_id=user.id)
                db.session.add(student)
            db.session.commit()

            flash('Registration successful! You can now login.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')

    return render_template('auth/register.html')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        error = None

        user = User.query.filter_by(username=username).first()

        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user.password, password):
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = user.id
            return redirect(url_for('user.user_profile'))

        flash(error)

    return render_template('auth/login.html')


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = User.query.get(user_id)


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))
