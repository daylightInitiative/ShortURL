
import os
from datetime import timedelta

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
 
from Short_URL.redis_client import redis_client # centralized redis instance
from Short_URL.utility import get_shortened_url, is_valid_url


app = Flask(__name__)

app.config["RATELIMIT_HEADERS_ENABLED"] = True  # sends X-RateLimit headers
app.config['FLASK_ADMIN_SWATCH'] = 'flatly'

# setup the db paths
app.config["SECRET_KEY"] = "secret"
app.config["DATABASE_FILE"] = "authdb.sqlite"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + app.config["DATABASE_FILE"]
app.config["SQLALCHEMY_ECHO"] = True
# Flask-Security config
app.config["SECURITY_URL_PREFIX"] = "/admin"
app.config["SECURITY_PASSWORD_HASH"] = "pbkdf2_sha512"
app.config["SECURITY_PASSWORD_SALT"] = "ATGUOHAELKiubahiughaerGOJAEGj"
# Flask-Security URLs, overridden because they don't put a / at the end
app.config["SECURITY_LOGIN_URL"] = "/login/"
app.config["SECURITY_LOGOUT_URL"] = "/logout/"
app.config["SECURITY_REGISTER_URL"] = "/register/"
app.config["SECURITY_POST_LOGIN_VIEW"] = "/admin/"
app.config["SECURITY_POST_LOGOUT_VIEW"] = "/admin/"
app.config["SECURITY_POST_REGISTER_VIEW"] = "/admin/"
# Flask-Security features
app.config["SECURITY_REGISTERABLE"] = True
app.config["SECURITY_SEND_REGISTER_EMAIL"] = False
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
# setup the flask admin panel
admin = Admin(app, name='admin-panel', template_mode='bootstrap3')

roles_users = db.Table(
    "roles_users",
    db.Column("user_id", db.Integer(), db.ForeignKey("user.id")),
    db.Column("role_id", db.Integer(), db.ForeignKey("role.id")),
)

class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)

    def __str__(self):
        return self.name

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(255))
    last_name = db.Column(db.String(255))
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    last_login = db.Column(db.DateTime())
    roles = db.relationship(
        "Role", secondary=roles_users, backref=db.backref("users", lazy="dynamic")
    )
    fs_uniquifier = db.Column(db.String(64), unique=True, nullable=False)

    def __str__(self):
        return self.email
    
# Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)



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
@limiter.limit("60 per minute", override_defaults=True)
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

if __name__ == "__main__":
    print("Running in __main__")
    app.run(debug=True)