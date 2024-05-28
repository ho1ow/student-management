from flask_sqlalchemy import SQLAlchemy
from flask import g

db = SQLAlchemy()  

def init_db(app):
    db.init_app(app)

def get_db():
    if 'db_session' not in g:
        g.db_session = db.session
    return g.db_session

def teardown_db(exception):
    db_session = g.pop('db_session', None)
    if db_session is not None:
        db_session.close()
