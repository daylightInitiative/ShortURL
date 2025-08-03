
import os
from datetime import timedelta

from flask import Flask, request, redirect, jsonify, render_template, send_from_directory, abort
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
 
from Short_URL.redis_client import redis_client # centralized redis instance
from Short_URL.utility import get_shortened_url, is_valid_url

app = Flask(__name__)

app.config["RATELIMIT_HEADERS_ENABLED"] = True  # sends X-RateLimit headers

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



if __name__ == "__main__":
    app.run(debug=True)