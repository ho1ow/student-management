from functools import wraps
import logging
from flask import g, redirect, url_for, flash
from ..models import RoleEnum


def role_required(role):
    def decorator(view):
        @wraps(view)
        def wrapped_view(**kwargs):
            if g.user is None:
                return redirect(url_for('auth.login'))
            if g.user.role != role:
                logging.error(
                    f'User {g.user.username} does not have access to this page, role: {g.user.role}, {type(g.user.role)}')
                flash('You do not have access to this page.', 'error')
                return 'not this role'
            return view(**kwargs)
        return wrapped_view
    return decorator
