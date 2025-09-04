from redis import Redis
from redis import ConnectionError as RedisConnectionError

# this redis instance is shared across files to prevent issues.
try:
    redis_client = Redis(host='localhost', port=6379, db=0, decode_responses=True)
    redis_client.ping()
except RedisConnectionError:
    print("\n\nRedis is not running!\nStart redis-server in another terminal or on windows in WSL; as a process or daemon.")
except Exception as e:
    print(f"Unexpected error occurred: {e}")