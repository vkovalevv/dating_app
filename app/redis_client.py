from redis import Redis
from app.schemas.users import UsersStack
from app.models.users import User as UserModel
from app.config import settings
redis_cache = Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT,
                    db=2, decode_responses=True)
redis_tokens = Redis(host=settings.REDIS_HOST,
                     port=settings.REDIS_PORT, db=3, decode_responses=True)


def save_stack_to_redis(user_id: int, stack_ids: list[int]):
    key = f'user:{user_id}'
    pipe = redis_cache.pipeline()
    pipe.delete(key)
    pipe.rpush(key, *stack_ids)
    pipe.expire(key, 60*60*24)
    pipe.execute()


def get_stack_from_redis(user: UserModel):
    data = redis_cache.get(f'user:{user.id}')
    return UsersStack.model_validate_json(data)


def get_next_from_stack(user_id: int) -> int | None:
    '''
    Достаем следующего пользователя из колоды
    '''
    key = f'user:{user_id}'
    next_user_id = redis_cache.lpop(key)

    return int(next_user_id) if next_user_id else None
