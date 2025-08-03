
from hashlib import sha256
from urllib.parse import urlparse

def get_shortened_url(long_url):
    salt = "ShortURLRandom"
    digest = sha256((long_url + salt).encode("utf-8")).hexdigest()
    code = digest[:5]
    return code, f"http://localhost:5000/{code}"

def is_valid_url(url):
    parsed = urlparse(url)
    return parsed.scheme in ('http', 'https') and parsed.netloc

