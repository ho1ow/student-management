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
from app import UPLOAD_FOLDER

ASSIGNMENT_FOLDER = os.path.join(UPLOAD_FOLDER, 'assignment')
SUBMISSION_FOLDER = os.path.join(UPLOAD_FOLDER, 'submission')

def allowed_file(filename):
    # return '.' in filename and filename.rsplit('.', 1)[1].lower() in
    return True


bp = Blueprint('assignment', __name__, url_prefix='/assignment')


@bp.route('/', methods=['GET', 'POST'])
def add_assignment():
    try:
        assignment_data = []
        if g.user.role == 'teacher':
            assignments = Assignment.query.join(Teacher).filter(
                Teacher.user_id == g.user.id).all()
        else:
            class_id=Student.query.filter_by(user_id=session['user_id']).first().class_id
            teacher_id=Class.query.get(class_id).teacher_id
            assignments = Assignment.query.filter_by(teacher_id=teacher_id).all()
            

        for assignment in assignments:
            try:
                with open(assignment.file_url, 'r') as file:
                    content = file.read()
                assignment_data.append({
                    "id": assignment.id,
                    "title": assignment.title,
                    "description": assignment.description,
                    "teacher_id": assignment.teacher_id,
                    "created_at": assignment.created_at.isoformat() if assignment.created_at else None,
                    "content": content
                })
            except IOError as e:
                logging.error(
                    f'Failed to read file {assignment.file_url}: {str(e)}')
                assignment_data.append({
                    "id": assignment.id,
                    "title": assignment.title,
                    "description": assignment.description,
                    "teacher_id": assignment.teacher_id,
                    "created_at": assignment.created_at.isoformat() if assignment.created_at else None,
                    "content": f'Error reading file: {str(e)}'
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

                # Ensure the teacher exists and get their id
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


def read_file(url):
    try:
        with open(url, 'r') as file:
            content = file.read()
        return content
    except IOError as e:
        logging.error(f'Failed to read file {url}: {str(e)}')
        return f'Error reading file: {str(e)}'

@bp.route('/<int:id>', methods=['GET', 'PUT', 'DELETE'])
@role_required('teacher')
def view_assignment(id):
    assignment = Assignment.query.get(id)
    if not assignment:
        return jsonify({"error": f"Assignment with id {id} not found"}), 404

    teacher = Teacher.query.filter_by(user_id=session['user_id']).first()
    if not teacher:
        return jsonify({"error": "Teacher not found"}), 404

    teacher_id = teacher.id

    if request.method == 'GET':
        if teacher_id != assignment.teacher_id:
            logging.error(f"User {teacher_id} is not authorized to view assignment {id}")
            return jsonify({"error": "You are not authorized to view this assignment"}), 403

        user = User.query.filter_by(id=teacher.user_id).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        content= read_file(assignment.file_url)
        
        teacher_name = user.fullname
        assignment_data = {
            "id": assignment.id,
            "title": assignment.title,
            "description": assignment.description,
            "teacher_id": assignment.teacher_id,
            "teacher_name": teacher_name,
            "created_at": assignment.created_at.isoformat() if assignment.created_at else None,
            "file_url": assignment.file_url,
            "content": content
        }
        return jsonify(assignment_data), 200

    elif request.method == 'PUT':
        if teacher_id != assignment.teacher_id:
            return jsonify({"error": "You are not authorized to edit this assignment"}), 403

        assignment.title = request.json.get('title', assignment.title)
        assignment.description = request.json.get('description', assignment.description)
        db.session.commit()
        return jsonify({"message": "Assignment updated successfully"}), 200

    elif request.method == 'DELETE':
        if teacher_id != assignment.teacher_id:
            return jsonify({"error": "You are not authorized to delete this assignment"}), 403

        db.session.delete(assignment)
        db.session.commit()
        return jsonify({"message": "Assignment deleted successfully"}), 200


@bp.route('/<int:id>/submit', methods=['POST'])
def submit_assignment(id):
    assignment = Assignment.query.get(id)
    if not assignment:
        return jsonify({"error": f"Assignment with id {id} not found"}), 404
    file = request.files.get('file', None)
    if not file or file.filename == '':
        flash('No file selected')
        return 'No file selected'
    if allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(SUBMISSION_FOLDER, filename)
        try:
            file.save(file_path)

            submission = Submission(
                assignment_id=id, student_id=g.user.id, file_url=file_path)
            db.session.add(submission)
            db.session.commit()
            return jsonify({"message": "Assignment submitted successfully"}), 200
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}')
            return 'An error occurred'
    else:
        flash('File type not allowed')
        return 'File type not allowed'


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

    file_content = read_file(submission.file_url)

    submission_data = {
        "id": submission.id,
        "assignment_id": submission.assignment_id,
        "student_id": submission.student_id,
        "file_content": file_content,
        "created_at": submission.created_at.isoformat() if submission.created_at else None
    }

    return jsonify(submission_data), 200