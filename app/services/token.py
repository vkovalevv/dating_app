from redis import Redis
from app.redis_client import redis_tokens
from .auth import create_refresh_token
REFRESH_TOKEN_TTL = 60*60*24*30


class TokenService:
    def __init__(self, redis: Redis):
        self.redis = redis

    def save_refresh_token(self, user_id: int, token: str) -> None:
        pipeline = self.redis.pipeline()
        pipeline.setex(f'refresh_token:{token}', REFRESH_TOKEN_TTL, user_id)
        pipeline.sadd(f'user_tokens:{user_id}', token)
        pipeline.expire(f'user_tokens:{user_id}', REFRESH_TOKEN_TTL)
        pipeline.execute()

    def get_user_id(self, token: str) -> int | None:
        user_id = self.redis.get(f'refresh_token:{token}')
        if not user_id:
            return None
        return int(user_id)

    def rotate_refresh_token(self, user_id: int, old_token: str, new_token: str) -> None:
        pipeline = self.redis.pipeline()
        pipeline.delete(f'refresh_token:{old_token}')
        pipeline.srem(f'user_tokens:{user_id}', old_token)
        pipeline.setex(f'refresh_token:{new_token}',
                       REFRESH_TOKEN_TTL, user_id)
        pipeline.sadd(f'user_tokens:{user_id}', new_token)
        pipeline.expire(f'user_tokens:{user_id}')
        pipeline.execute()


redis = TokenService(redis=redis_tokens)
