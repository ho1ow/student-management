from flask import Flask, g, redirect, request, session, url_for

from app.models import User


from .db import init_db, teardown_db, db


def create_app():
    app = Flask(__name__, instance_relative_config=True,
                template_folder='../templates', static_folder='../static')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://root:abc@localhost:9999/classroom?sslmode=disable'
    app.config['SECRET_KEY'] = 'this-really-needs-to-be-changed'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    init_db(app)

    with app.app_context():
        db.create_all()

        from .routes import auth, route, user, assignment, challenge
        app.register_blueprint(auth.bp)
        app.register_blueprint(route.bp)
        app.register_blueprint(user.bp)
        app.register_blueprint(assignment.bp)
        app.register_blueprint(challenge.bp)
        app.teardown_appcontext(teardown_db)

    @app.before_request
    def require_login():
        allowed_routes = ['auth.login', 'auth.register', 'static']
        if request.endpoint not in allowed_routes and 'user_id' not in session:
            return redirect(url_for('auth.login'))

    def load_logged_in_user():
        user_id = session.get('user_id')
        if user_id is None:
            g.user = None
        else:
            g.user = User.query.get(user_id)

    return app
