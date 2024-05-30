import enum
from .db import db


class RoleEnum(enum.Enum):
    student = 'student'
    teacher = 'teacher'


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(), unique=True, nullable=False)
    password = db.Column(db.String(), nullable=False)
    fullname = db.Column(db.String(), nullable=True)
    phone = db.Column(db.String(), nullable=True)
    role = db.Column(db.String(), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    def __init__(self, username, password, fullname=None, phone=None, role=None):
        self.username = username
        self.password = password
        self.fullname = fullname
        self.phone = phone
        self.role = role

class Teacher(db.Model):
    __tablename__ = 'teachers'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    
class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'))
    created_at = db.Column(db.DateTime, server_default=db.func.now())

class Class(db.Model):
    __tablename__ = 'class'
    id=db.Column(db.Integer, primary_key=True)
    class_name = db.Column(db.String(), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    

class Assignment(db.Model):
    __tablename__ = 'assignments'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(), nullable=False)
    description = db.Column(db.String())
    teacher_id = db.Column(
        db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    file_url = db.Column(db.String())

    def __init__(self, title, description, teacher_id, file_url):
        self.title = title
        self.description = description
        self.teacher_id = teacher_id
        self.file_url = file_url


class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.String(), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

class Submission(db.Model):
    __tablename__ = 'submissions'
    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignments.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    file_url = db.Column(db.String())
    created_at = db.Column(db.DateTime, default=db.func.now())

    def __init__(self, assignment_id, student_id, file_url):
        self.assignment_id = assignment_id
        self.student_id = student_id
        self.file_url = file_url



class Challenge(db.Model):
    __tablename__ = 'challenges'
    id = db.Column(db.Integer, primary_key=True)
    created_by = db.Column(
        db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    challenge_url = db.Column(db.String(), nullable=False)
    hint = db.Column(db.String())
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    def __init__(self, created_by, challenge_url, hint):
        self.created_by = created_by
        self.challenge_url = challenge_url
        self.hint = hint
