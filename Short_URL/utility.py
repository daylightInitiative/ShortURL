import re

from hashlib import sha256
from urllib.parse import urlparse
from Short_URL.redis_client import redis_client

alphabet = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

def to_base62(num: int) -> str:
    if num == 0:
        return alphabet[0]
    result = []
    while num:
        num, rem = divmod(num, 62)
        result.append(alphabet[rem])
    return ''.join(reversed(result))

def get_shortened_url(long_url: str):
    cleaned_url = re.sub(r"^https?://(www\.)?", "", long_url, flags=re.IGNORECASE)
    url_hash = sha256(f"{cleaned_url}".encode("utf-8")).hexdigest()[:9]
    code = to_base62(int(url_hash, 16))

    return code, f"http://localhost:5000/{code}"

def is_valid_url(url):
    parsed = urlparse(url)
    return parsed.scheme in ('http', 'https') and parsed.netloc

