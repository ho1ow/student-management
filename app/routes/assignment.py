from app import UPLOAD_FOLDER
import logging
import os
from flask import (
    Blueprint, flash, request, redirect, g, session, url_for, jsonify, render_template
)
from werkzeug.utils import secure_filename
from ..db import db
from ..models import Assignment, Submission, User, Teacher, Student, Class
from ..services.autho import role_required

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'py'}

ASSIGNMENT_FOLDER = os.path.join(UPLOAD_FOLDER, 'assignment')
SUBMISSION_FOLDER = os.path.join(UPLOAD_FOLDER, 'submission')

if not os.path.exists(ASSIGNMENT_FOLDER):
    os.makedirs(ASSIGNMENT_FOLDER)
if not os.path.exists(SUBMISSION_FOLDER):
    os.makedirs(SUBMISSION_FOLDER)


def allowed_file(filename):
    # return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    return True


bp = Blueprint('assignment', __name__, url_prefix='/assignment')


def read_file_content(file_path):
    try:
        with open(file_path, 'r') as file:
            return file.read()
    except Exception as e:
        logging.error(f"Error reading file {file_path}: {str(e)}")
        return f"Error reading file: {str(e)}"


@bp.route('/', methods=['GET', 'POST'])
def add_assignment():
    try:
        assignment_data = []
        if g.user.role == 'teacher':
            assignments = Assignment.query.join(Teacher).filter(
                Teacher.user_id == g.user.id).all()
            logging.debug(f"teacher_id: {g.user.id}")
        else:
            class_id = Student.query.filter_by(
                user_id=session['user_id']).first().class_id
            teacher_id = Class.query.get(class_id).teacher_id
            assignments = Assignment.query.filter_by(
                teacher_id=teacher_id).all()

        for assignment in assignments:
            content = read_file_content(assignment.file_url)
            assignment_data.append({
                "id": assignment.id,
                "title": assignment.title,
                "description": assignment.description,
                "teacher_id": assignment.teacher_id,
                "created_at": assignment.created_at.isoformat() if assignment.created_at else None,
                "content": content
            })

    except Exception as e:
        logging.error(f'Failed to retrieve assignments: {str(e)}')
        flash(f'Failed to retrieve assignments: {str(e)}')
        assignment_data = []

    if request.method == 'POST':
        if g.user.role != 'teacher':
            flash('You are not authorized to add an assignment')
            return redirect(url_for('assignment.add_assignment'))

        title = request.form.get('title')
        description = request.form.get('description')
        file = request.files.get('file')

        if not file or file.filename == '':
            flash('No file selected')
            return redirect(url_for('assignment.add_assignment'))

        if allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(ASSIGNMENT_FOLDER, filename)
            try:
                file.save(file_path)

                teacher = Teacher.query.filter_by(user_id=g.user.id).first()
                if not teacher:
                    flash('Teacher does not exist')
                    return redirect(url_for('assignment.add_assignment'))

                logging.info(
                    f'Creating assignment with teacher_id: {teacher.id}')

                assignment = Assignment(
                    title=title,
                    description=description,
                    teacher_id=teacher.id,
                    file_url=file_path
                )
                db.session.add(assignment)
                db.session.commit()
                flash('Assignment added successfully')
                return redirect(url_for('assignment.add_assignment'))
            except Exception as e:
                db.session.rollback()
                logging.error(
                    f'An error occurred while adding the assignment: {str(e)}')
                flash(f'An error occurred: {str(e)}')
                return redirect(url_for('assignment.add_assignment'))
        else:
            flash('File type not allowed')
            return redirect(url_for('assignment.add_assignment'))

    teacher_name = User.query.get(Assignment.query.first(
    ).teacher_id).fullname if Assignment.query.first() else None
    return render_template('assignment/assignment.html', assignments=assignment_data, teacher_name=teacher_name)


@bp.route('/<int:id>', methods=['GET'])
def view_assignment(id):
    assignment = Assignment.query.get(id)
    content = read_file_content(assignment.file_url)
    teacher_name = db.session.query(User.fullname).join(
        Teacher, Teacher.user_id == User.id).filter(Teacher.id == assignment.teacher_id).first()
    teacher_name = teacher_name[0] if teacher_name else "Unknown"

    assignment_data = {
        "id": assignment.id,
        "title": assignment.title,
        "description": assignment.description,
        "teacher_id": assignment.teacher_id,
        "teacher_name": teacher_name,
        "created_at": assignment.created_at.isoformat() if assignment.created_at else None,
        "content": content
    }
    return jsonify(assignment_data), 200


@bp.route('/<int:id>', methods=['PUT', 'DELETE'])
def edit_assignment(id):
    assignment = Assignment.query.get(id)
    if not assignment:
        return jsonify({"error": f"Assignment with id {id} not found"}), 404

    teacher = Teacher.query.filter_by(user_id=session['user_id']).first()
    if not teacher:
        return jsonify({"error": "no "}), 404

    if teacher.id != assignment.teacher_id:
        logging.error(
            f"User {teacher.id} is not authorized to view assignment {id}")
        return jsonify({"error": "You are not authorized to view this assignment"}), 403

    user = User.query.filter_by(id=teacher.user_id).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    content = read_file_content(assignment.file_url)

    assignment_data = {
        "id": assignment.id,
        "title": assignment.title,
        "description": assignment.description,
        "teacher_id": assignment.teacher_id,
        "teacher_name": user.fullname,
        "created_at": assignment.created_at.isoformat() if assignment.created_at else None,
        "content": content
    }
    return jsonify(assignment_data), 200


@bp.route('/<int:id>/submit', methods=['POST'])
def submit_assignment(id):
    assignment = Assignment.query.get(id)
    if not assignment:
        return jsonify({"error": f"Assignment with id {id} not found"}), 404

    file = request.files.get('file', None)
    if not file or file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    if allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(SUBMISSION_FOLDER, filename)

        # Ensure the submission directory exists
        if not os.path.exists(SUBMISSION_FOLDER):
            os.makedirs(SUBMISSION_FOLDER)

        try:
            file.save(file_path)

            # Check if the student exists
            student = Student.query.filter_by(user_id=g.user.id).first()
            if not student:
                return jsonify({"error": "Student not found"}), 404

            submission = Submission(
                assignment_id=assignment.id,
                student_id=student.id,  # Use the student's id
                file_url=file_path
            )
            db.session.add(submission)
            db.session.commit()
            return jsonify({"message": "Assignment submitted successfully"}), 200
        except Exception as e:
            db.session.rollback()
            logging.error(
                f'An error occurred while submitting the assignment: {str(e)}')
            return jsonify({"error": f'An error occurred: {str(e)}'}), 500
    else:
        return jsonify({"error": "File type not allowed"}), 400


@bp.route('/<int:id>/submissions', methods=['GET'])
@role_required('teacher')
def view_submissions(id):
    assignment = Assignment.query.get(id)
    if not assignment:
        return jsonify({"error": f"Assignment with id {id} not found"}), 404

    submissions = Submission.query.filter_by(assignment_id=id).all()
    submission_data = [{
        "id": submission.id,
        "assignment_id": submission.assignment_id,
        "student_id": submission.student_id,
        "created_at": submission.created_at.isoformat() if submission.created_at else None,
        "file_url": submission.file_url
    } for submission in submissions]

    return render_template('assignment/submissions.html', submissions=submission_data, assignment_id=id)


@bp.route('/<int:id>/submissions/<int:submission_id>', methods=['GET'])
@role_required('teacher')
def view_submission(id, submission_id):
    submission = Submission.query.get(submission_id)
    if not submission:
        return jsonify({"error": f"Submission with id {submission_id} not found"}), 404

    if submission.assignment_id != id:
        return jsonify({"error": f"Submission with id {submission_id} not found for assignment with id {id}"}), 404

    file_content = read_file_content(submission.file_url)

    submission_data = {
        "id": submission.id,
        "assignment_id": submission.assignment_id,
        "student_id": submission.student_id,
        "file_content": file_content,
        "created_at": submission.created_at.isoformat() if submission.created_at else None
    }

    return jsonify(submission_data), 200
