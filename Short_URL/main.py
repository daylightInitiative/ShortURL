
import sys
import os
from datetime import timedelta

from redis.exceptions import ConnectionError as RedisConnectionError

from flask import Flask, request, redirect, jsonify, render_template, send_from_directory, abort, url_for
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_admin import Admin
from flask_security import Security, RoleMixin, SQLAlchemyUserDatastore
from flask_admin import helpers as admin_helpers
from flask_admin.contrib.sqla import ModelView
#from flask_admin.theme import Bootstrap4Theme
from flask_security import UserMixin
from flask_security import current_user
from flask_security.utils import hash_password
from flask_sqlalchemy import SQLAlchemy

from .models import db, User, Role, roles_users
from .config import apply_flask_configs

from Short_URL.redis_client import redis_client # centralized redis instance
from Short_URL.utility import get_shortened_url, is_valid_url

app = Flask(__name__)
apply_flask_configs(app)

class MyModelView(ModelView):
        def is_accessible(self):
            return (
                current_user.is_active
                and current_user.is_authenticated
                and current_user.has_role("superuser")
            )

        def _handle_view(self, name, **kwargs):
            """
            Override builtin _handle_view in order to redirect users when a view is not
            accessible.
            """
            if not self.is_accessible():
                if current_user.is_authenticated:
                    abort(403)
                else:
                    return redirect(url_for("security.login", next=request.url))


db.init_app(app) # since we arent initializing constructor, internally init

# setup the flask admin panel
admin = Admin(app, name='admin-panel', template_mode='bootstrap3')
    
# Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)

limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["10 per minute"],
    storage_uri="redis://localhost:6379/0",    
    storage_options={"socket_timeout": 5},     # Passed to redis.Redis
    strategy="fixed-window"
)


basedir = os.path.abspath(os.path.dirname(__file__))
CORS(app) # enable CORS

@app.route('/')
def index():
    return render_template('index.html')


# make sure this is here because browsers will ask for this every time a webpage is loaded
@app.route('/favicon.ico')
def favicon():
    return '', 204 

@app.route('/shorten', methods=['POST'])
@limiter.limit("10 per minute", override_defaults=True)
def serve_shortened_url():
    payload = request.get_json(silent=True) or {}
    long_url = payload.get("longURL")
    if not long_url or not is_valid_url(long_url):
        return jsonify(error="Invalid or missing longURL"), 400

    code, short_url = get_shortened_url(long_url)
    if not redis_client.exists(code):
        redis_client.set(f"short:{code}", long_url, ex=timedelta(days=1))
    return jsonify(shortURL=short_url), 200 

@app.route('/<code>')
@limiter.limit("100 per minute", override_defaults=True)
def redirect_to_long_url(code):
    original = redis_client.get(f"short:{code}")
    if not original:
        abort(404)
    return redirect(original)

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

def build_sample_db():
    """
    Populate a small db with some example entries.
    """

    print("creating sample DB")
    import random
    import string

    db.drop_all()
    db.create_all()

    with app.app_context():
        user_role = Role(name="user")
        super_user_role = Role(name="superuser")
        db.session.add(user_role)
        db.session.add(super_user_role)
        db.session.commit()

        user_datastore.create_user(
            first_name="Admin",
            email="admin@example.com",
            password=hash_password("admin"),
            roles=[user_role, super_user_role],
        )

        print(hash_password("admin"))

        first_names = [
            "Harry",
            "Amelia",
            "Oliver",
            "Jack",
            "Isabella",
            "Charlie",
            "Sophie",
            "Mia",
            "Jacob",
            "Thomas",
            "Emily",
            "Lily",
            "Ava",
            "Isla",
            "Alfie",
            "Olivia",
            "Jessica",
            "Riley",
            "William",
            "James",
            "Geoffrey",
            "Lisa",
            "Benjamin",
            "Stacey",
            "Lucy",
        ]
        last_names = [
            "Brown",
            "Smith",
            "Patel",
            "Jones",
            "Williams",
            "Johnson",
            "Taylor",
            "Thomas",
            "Roberts",
            "Khan",
            "Lewis",
            "Jackson",
            "Clarke",
            "James",
            "Phillips",
            "Wilson",
            "Ali",
            "Mason",
            "Mitchell",
            "Rose",
            "Davis",
            "Davies",
            "Rodriguez",
            "Cox",
            "Alexander",
        ]

        for i in range(len(first_names)):
            tmp_email = (
                first_names[i].lower() + "." + last_names[i].lower() + "@example.com"
            )
            tmp_pass = "".join(
                random.choice(string.ascii_lowercase + string.digits) for i in range(10)
            )
            user_datastore.create_user(
                first_name=first_names[i],
                last_name=last_names[i],
                email=tmp_email,
                password=hash_password(tmp_pass),
                roles=[
                    user_role,
                ],
            )
        db.session.commit()
    return

@app.cli.command("initdb")
def build_db_command():
    """initially creates the database and adds the administrator account"""
    with app.app_context():
        if not os.path.exists(database_path):
            build_sample_db()

admin.add_view(MyModelView(Role, db.session))
admin.add_view(MyModelView(User, db.session))
app_dir = os.path.realpath(os.path.dirname(__file__))
database_path = os.path.join(app_dir, app.config["DATABASE_FILE"])

# run flask in a try catch to catch if redis isnt running
