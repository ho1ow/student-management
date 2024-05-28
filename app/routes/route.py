from flask import Blueprint, render_template, request, redirect, url_for, flash
from ..db import db
from ..models import *

bp = Blueprint('main', __name__)


@bp.route('/hello')
def hello():
    return 'Hello, World!'

@bp.route('/index')
def index():
    return 'check'