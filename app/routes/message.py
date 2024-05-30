import logging
from flask import (
    Blueprint, flash, request, redirect, g, session, url_for, jsonify, render_template
)
from ..db import db
from ..models import Message, User
from ..services.autho import role_required

bp = Blueprint('message', __name__, url_prefix='/message')


@bp.route('/', methods=['GET', 'POST'])
def messages():
    if request.method == 'POST':
        sender_id = session.get('user_id')
        receiver_id = request.json.get('receiver_id')
        content = request.json.get('content')
        
        try:
            message = Message(
                sender_id=sender_id,
                receiver_id=receiver_id,
                content=content
            )
            db.session.add(message)
            db.session.commit()
            return jsonify({"message": "Message sent successfully"}), 200
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error sending message: {e}")
            return jsonify({"error": str(e)}), 500

    return render_template('message/messages.html')


@bp.route('/conversations', methods=['GET'])
def get_conversations():
    try:
        user_id = session.get('user_id')
        sent_messages = db.session.query(Message.receiver_id).filter(Message.sender_id == user_id).distinct()
        received_messages = db.session.query(Message.sender_id).filter(Message.receiver_id == user_id).distinct()
        conversation_user_ids = sent_messages.union(received_messages).all()
        conversation_users = []

        for user_id_tuple in conversation_user_ids:
            other_user_id = user_id_tuple[0]
            other_user = User.query.get(other_user_id)
            conversation_users.append({
                "user_id": other_user.id,
                "username": other_user.username
            })

        return jsonify(conversation_users), 200
    except Exception as e:
        logging.error(f"Error retrieving conversations: {e}")
        return jsonify({"error": str(e)}), 500


@bp.route('/<int:sender_id>/<int:receiver_id>', methods=['GET'])
def get_messages(sender_id, receiver_id):
    try:
        messages = Message.query.filter(
            ((Message.sender_id == sender_id) & (Message.receiver_id == receiver_id)) |
            ((Message.sender_id == receiver_id) & (Message.receiver_id == sender_id))
        ).order_by(Message.created_at.desc()).limit(10).all()
        message_data = [{
            "id": message.id,
            "sender_id": message.sender_id,
            "receiver_id": message.receiver_id,
            "content": message.content,
            "created_at": message.created_at.isoformat() if message.created_at else None
        } for message in messages]
        return jsonify(message_data), 200
    except Exception as e:
        logging.error(f"Error retrieving messages: {e}")
        return jsonify({"error": str(e)}), 500


@bp.route('/<int:message_id>', methods=['PUT'])
def update_message(message_id):
    try:
        message = Message.query.get(message_id)
        if not message:
            return jsonify({"error": f"Message with id {message_id} not found"}), 404
        if g.user.id != message.sender_id:
            return jsonify({"error": "You are not authorized to edit this message"}), 403
        
        content = request.json.get('content')
        message.content = content
        db.session.commit()
        return jsonify({"message": "Message updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error updating message: {e}")
        return jsonify({"error": str(e)}), 500


@bp.route('/<int:message_id>', methods=['DELETE'])
def delete_message(message_id):
    try:
        message = Message.query.get(message_id)
        if not message:
            return jsonify({"error": f"Message with id {message_id} not found"}), 404
        if g.user.id != message.sender_id:
            return jsonify({"error": "You are not authorized to delete this message"}), 403
        
        db.session.delete(message)
        db.session.commit()
        return jsonify({"message": "Message deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting message: {e}")
        return jsonify({"error": str(e)}), 500
