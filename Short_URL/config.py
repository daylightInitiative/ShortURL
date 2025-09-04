


def apply_flask_configs(app):
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
    app.config["SECURITY_LOGOUT_URL"] = "/"
    app.config["SECURITY_REGISTER_URL"] = "/register/"
    app.config["SECURITY_POST_LOGIN_VIEW"] = "/admin/"
    app.config["SECURITY_POST_LOGOUT_VIEW"] = "/"
    app.config["SECURITY_POST_REGISTER_VIEW"] = "/admin/"
    # Flask-Security features
    app.config["SECURITY_REGISTERABLE"] = True
    app.config["SECURITY_SEND_REGISTER_EMAIL"] = False
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False