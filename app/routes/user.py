import logging
from flask import (
    Blueprint, flash, g, jsonify, redirect, render_template, request, session, url_for
)
from werkzeug.security import generate_password_hash
from ..db import db
from ..models import User, RoleEnum, Teacher, Student, Class
from ..services.autho import role_required

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

bp = Blueprint('user', __name__, url_prefix='/')


def get_class_id(user_id):
    cl = None
    class_ids = None
    user = User.query.get(user_id)
    if user.role == RoleEnum.student.value:
        student = Student.query.filter_by(user_id=user.id).first()
        cl = student.class_id if student else None
    elif user.role == RoleEnum.teacher.value:
        teacher = Teacher.query.filter_by(user_id=user.id).first()
        class_ids = [class_.id for class_ in Class.query.filter_by(
            teacher_id=teacher.id).all()] if teacher else []
        class_ids = str(class_ids).strip('[]')
    return cl if user.role == RoleEnum.student.value else class_ids


@bp.route('/users', methods=['GET'])
def get_user_profile():
    try:
        user_list = User.query.all()
        users_data = []
        for user in user_list:
            user_info = {
                "id": user.id,
                "username": user.username,
                "fullname": user.fullname,
                "phone": user.phone,
                "role": user.role,
                "class": get_class_id(user.id),
                "created_at": user.created_at.isoformat() if user.created_at else None
            }
            users_data.append(user_info)
        ss = session.get('user_id')
        logging.debug(f"Session user_id: {ss}")
        return render_template('user/users.html', users=users_data, ss=ss)
    except Exception as e:
        logging.error(f"Error in get_user_profile: {str(e)}")
        return jsonify({"error": str(e)}), 500


@bp.route('/users/<int:user_id>', methods=['GET'])
def get_user_by_id(user_id):
    try:
        u = User.query.get(user_id)
        if not u:
            return jsonify({"error": f"User with id {user_id} not found"}), 404

        can_update = False

        if User.query.get(session.get('user_id')).role == 'teacher':
            can_update = True

        user_info = {
            "id": u.id,
            "username": u.username,
            "fullname": u.fullname,
            "phone": u.phone,
            "class": get_class_id(u.id),
            "role": u.role,
        }
        logging.debug(f"session: {session}")
        logging.debug(f"user_id: {u.id}")
        logging.debug(f"can_update: {can_update}")

        return render_template('user/details.html', user=user_info, can_update=can_update)
    except Exception as e:
        logging.error(f"Error in get_user_by_id: {str(e)}")
        return jsonify({"error": str(e)}), 500


@bp.route('/profile', methods=['GET', 'PUT'])
def user_profile():
    user = User.query.get(session.get('user_id'))

    if request.method == 'PUT':
        try:
            user.phone = request.json.get('phone', user.phone)
            user.password = generate_password_hash(
                request.json.get('password', user.password))

            db.session.commit()
            logging.info("User profile updated successfully")
            return jsonify({"message": "User profile updated successfully"}), 200
        except Exception as e:
            db.session.rollback()
            logging.error(f"Failed to update user profile: {e}")
            return jsonify({"error": str(e)}), 500
    else:
        if session.get('user_id') != user.id:
            return jsonify({"error": "You are not authorized to view this page"}), 403
        try:
            user_info = {
                "id": user.id,
                "username": user.username,
                "fullname": user.fullname,
                "phone": user.phone,
                "role": user.role,
                "password": user.password,
                "created_at": user.created_at.isoformat() if user.created_at else None
            }
            role = g.user.role.capitalize()
            return render_template('user/details.html', user=user_info, role=role, can_update=True)
        except Exception as e:
            logging.error(f"Failed to retrieve user profile: {e}")
            return jsonify({"error": str(e)}), 500


@bp.route('/student', methods=['POST'])
@role_required('teacher')
def add_student():
    logging.info(f"session: {session}, request.json: {request.json}")
    username = request.json.get('username')
    password = request.json.get('password')
    fullname = request.json.get('fullname')
    class_id = request.json.get('class_id')
    phone = request.json.get('phone', '')

    try:
        if User.query.filter_by(username=username).first():
            return jsonify({"error": f"User {username} is already registered."}), 400

        user = User(username=username, password=generate_password_hash(password),
                    fullname=fullname, phone=phone, role=RoleEnum.student.value)
        db.session.add(user)
        db.session.commit()

        student = Student(user_id=user.id, class_id=class_id)
        db.session.add(student)
        db.session.commit()

        return jsonify({"message": "Student added successfully"}), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error in add_student: {str(e)}")
        return jsonify({"error": str(e)}), 500


@bp.route('/student/<int:user_id>', methods=['PUT'])
@role_required('teacher')
def edit_student(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": f"User with id {user_id} not found"}), 404
    # if user.role == RoleEnum.teacher.value:
    #     return jsonify({"error": "You cannot edit teacher"}), 400
    try:
        user.username = request.json.get('username', user.username)
        user.password = generate_password_hash(request.json.get('password', user.password))
        user.fullname = request.json.get('fullname', user.fullname)
        user.phone = request.json.get('phone', user.phone)
        db.session.commit()
        
        student = Student.query.filter_by(user_id=user.id).first()
        student.class_id = request.json.get('class_id', student.class_id)
        db.session.commit()

        return jsonify({"message": "Student updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error in edit_student: {str(e)}")
        return jsonify({"error": str(e)}), 500


@bp.route('/student/<int:user_id>', methods=['DELETE'])
@role_required('teacher')
def delete_student(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": f"User with id {user_id} not found"}), 404
    try:
        student = Student.query.filter_by(user_id=user_id).first()
        if student:
            db.session.delete(student)
        
        db.session.delete(user)
        db.session.commit()
        return jsonify({"message": "delete ok"}), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error in delete_student: {str(e)}")
        return jsonify({"error": str(e)}), 500

