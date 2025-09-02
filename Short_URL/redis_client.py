from redis import Redis

# this redis instance is shared across files to prevent issues.
redis_client = Redis(host='localhost', port=6379, db=0, decode_responses=True)