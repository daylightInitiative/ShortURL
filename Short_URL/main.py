from flask import Flask, request, redirect, jsonify, render_template, send_from_directory, abort
from hashlib import sha256
from flask_cors import CORS
from urllib.parse import urlparse

app = Flask(__name__)
CORS(app) # enable CORS

url_dict = {}
url_counter = 1

def is_valid_url(url):
    parsed = urlparse(url)
    return parsed.scheme in ('http', 'https') and parsed.netloc

@app.route('/')
def index():
    return render_template('index.html')

# thinking about 
def get_shortened_url(long_url) -> str:
    # utf-8 is the standard encoding for the web
    combined_str = long_url + "ShortURLRandom" # our salt
    short_url_hash = sha256(long_url.encode('utf-8')).hexdigest()
    url_code = short_url_hash[:5]

    # this way its (almost) completely random
    # craft the url from this hash
    new_url = f"http://localhost:5000/{url_code}"
    return new_url, url_code

@app.route('/<short_code>', methods=['GET'])
def redirect_to_long_url(short_code):
    # Look up the long URL using the short code
    long_url = url_dict.get(short_code)
    
    if long_url:
        return redirect(long_url)
    else:
        abort(404)

@app.route('/shorten', methods=['POST'])
def serve_shortened_url():
    global url_dict
    data = request.get_json()

    long_url = data.get('longURL')
    if not long_url:
        return jsonify({"error": "Missing url entry"}), 400

    if not is_valid_url(long_url):
        return jsonify({'error': 'Invalid URL'}), 400

    print(f"shortening URL: {long_url}")
    small_url, small_code = get_shortened_url(long_url)

    # check if it already exists then we just redirect
    if url_dict.get(small_code):
        return jsonify({"shortURL": small_url}), 200

    url_dict[small_code] = long_url

    print(f"new URL: {small_url}")
    output = {
        "shortURL": small_url,
    }

    # we need to turn the long_url into a shortened url
    # and then add it to a global dictionary for right now (database will be added later)
    return jsonify(output), 200
    



@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

if __name__ == '__main__':
    app.run(debug=True)