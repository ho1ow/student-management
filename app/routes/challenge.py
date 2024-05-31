import logging
import os
from flask import Blueprint, flash, request, redirect, session, jsonify, render_template
from werkzeug.utils import secure_filename
from ..db import db
from ..models import Challenge, Teacher, User
from ..services.autho import role_required
from app import UPLOAD_FOLDER
CHALLENGE_FOLDER = os.path.join(UPLOAD_FOLDER, 'challenge')
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

bp = Blueprint('challenge', __name__, url_prefix='/challenge')


def allowed_file(filename):
    # Check if the file extension is allowed
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    return True

if not os.path.exists(CHALLENGE_FOLDER):
    os.makedirs(CHALLENGE_FOLDER)

@bp.route('/', methods=['GET', 'POST'])
def challenge():
    if request.method == 'POST':
        return create_challenge()
    else:
        return list_challenges()


def create_challenge():
    uid = session.get('user_id')
    user = User.query.get(uid)

    if user is None or user.role != 'teacher':
        return jsonify({"error": "Only teachers can create challenges"}), 403

    hint = request.form.get('hint', '')
    file = request.files.get('file')

    if not file or file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "File type not allowed"}), 400

    try:
        filename = secure_filename(file.filename)
        file_path = os.path.join(CHALLENGE_FOLDER, filename)
        file.save(file_path)

        teacher = Teacher.query.filter_by(user_id=uid).first()
        if not teacher:
            return jsonify({"error": "Teacher not found"}), 404

        challenge = Challenge(
            created_by=teacher.id,
            challenge_url=file_path,
            hint=hint
        )
        db.session.add(challenge)
        db.session.commit()
        flash('Challenge created successfully')
        return jsonify({"message": "Challenge created successfully"}), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f'Error creating challenge: {str(e)}')
        return jsonify({"error": str(e)}), 500


def list_challenges():
    try:
        challenges = Challenge.query.all()
        if not challenges:
            # return jsonify({"message": "No challenges found"}), 200
            return render_template('challenge/challenge.html', challenges=[])
        challenge_data = [{
            "id": challenge.id,
            "hint": challenge.hint,
            "owner": User.query.get(Teacher.query.get(challenge.created_by).user_id).username,
            "created_at": challenge.created_at.isoformat() if challenge.created_at else None
        } for challenge in challenges]
        return render_template('challenge/challenge.html', challenges=challenge_data)
    except Exception as e:
        logging.error(f'Error retrieving challenges: {str(e)}')
        return jsonify({"error": str(e)}), 500


@bp.route('/<int:challenge_id>', methods=['GET', 'POST', 'DELETE'])
def challenge_detail(challenge_id):
    challenge = Challenge.query.get(challenge_id)
    if not challenge:
        return jsonify({"error": f"Challenge with id {challenge_id} not found"}), 404

    if request.method == 'GET':
        return get_challenge_details(challenge)
    elif request.method == 'DELETE':
        return delete_challenge(challenge)
    elif request.method == 'POST':
        return submit_challenge_answer(challenge)


def get_challenge_details(challenge):
    return jsonify({
        "id": challenge.id,
        "hint": challenge.hint,
        "created_at": challenge.created_at.isoformat() if challenge.created_at else None
    }), 200


def delete_challenge(challenge):
    uid = session.get('user_id')
    teacher_id = Teacher.query.filter_by(user_id=uid).first().id
    if teacher_id != Challenge.query.get(challenge.id).created_by:
        return jsonify({"error": "You are not authorized to delete this challenge"}), 403
    try:
        db.session.delete(challenge)
        db.session.commit()
        return jsonify({"message": "Challenge deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f'Error deleting challenge: {str(e)}')
        return jsonify({"error": str(e)}), 500


def submit_challenge_answer(challenge):
    data = request.get_json()
    answer = data.get('answertext', '')
    if not answer:
        return jsonify({"error": "Answer text is required"}), 400

    try:
        # Get the filename without extension
        filename = challenge.challenge_url.split('/')[-1].split('.')[0]
        if answer == filename:
            try:
                # Read the file content
                with open(challenge.challenge_url, 'r') as file:
                    content = file.read()
                return jsonify({"message": "Correct answer", "content": content}), 200
            except Exception as e:
                logging.error(f'Error reading file content: {str(e)}')
                return jsonify({"error": f"Error reading file content: {str(e)}"}), 500
        else:
            return jsonify({"message": "Incorrect answer", "answer": filename}), 200
    except Exception as e:
        logging.error(f'Error checking answer: {str(e)}')
        return jsonify({"error": str(e)}), 500
