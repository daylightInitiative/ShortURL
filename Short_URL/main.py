from flask import Flask, request, redirect, jsonify, render_template, send_from_directory, abort
from hashlib import sha256
from flask_cors import CORS
from urllib.parse import urlparse
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(basedir, 'urls.db')}" # cross-platform usage of os.path.join
CORS(app) # enable CORS
db = SQLAlchemy(app)

class URL(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    URLcode = db.Column(db.String(2096), unique=True, nullable=False)  # Max URL length
    original_url = db.Column(db.String(2096), nullable=False)

def is_valid_url(url):
    parsed = urlparse(url)
    return parsed.scheme in ('http', 'https') and parsed.netloc

@app.route('/')
def index():
    return render_template('index.html')

def get_shortened_url(long_url) -> str:
    # utf-8 is the standard encoding for the web
    combined_str = long_url + "ShortURLRandom" # our salt
    short_url_hash = sha256(long_url.encode('utf-8')).hexdigest()
    url_code = short_url_hash[:5]

    # this way its (almost) completely random
    # craft the url from this hash
    new_short_url = f"http://localhost:5000/{url_code}"
    return new_short_url, url_code

# make sure this is here because browsers will ask for this every time a webpage is loaded
@app.route('/favicon.ico')
def favicon():
    return '', 204  

@app.route('/<short_code>', methods=['GET'])
def redirect_to_long_url(short_code):
    # Look up the long URL using the short code
    short_url = URL.query.filter_by(URLcode=short_code).first_or_404()     #.first_or_404()
    return redirect(short_url.original_url)

@app.route('/shorten', methods=['POST'])
def serve_shortened_url():
    data = request.get_json()

    long_url = data.get('longURL')
    if not long_url:
        return jsonify({"error": "Missing url entry"}), 400

    if not is_valid_url(long_url):
        return jsonify({'error': 'Invalid URL'}), 400

    print(f"shortening URL: {long_url}")
    small_url, small_code = get_shortened_url(long_url)

    # check if it already exists then we just redirect
    url_already_exists = URL.query.filter_by(URLcode=small_code).first()
    if url_already_exists:
       return jsonify({"shortURL": small_url}), 200

    new_url = URL(URLcode=small_code, original_url=long_url)
    db.session.add(new_url)
    db.session.commit()

    print(f"new URL: {small_url}({long_url})")
    output = {
        "shortURL": small_url,
    }

    return jsonify(output), 200

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

FLASK_APP = "Short_URL.main"

#print(__name__) 
if __name__ == FLASK_APP:

    with app.app_context():
        db.create_all()
        print("Database tables recreated")

    app.run(debug=True)