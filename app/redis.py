from redis import Redis
from app.schemas.users import UsersStack, User as UserSchema
from app.models.users import User as UserModel

redis_cache = Redis(host='localhost', port=6379, db=2, decode_responses=True)


def save_stack_to_redis(user: UserModel, stack: list[UserModel]):
    key = f'user:{user.id}'
    users = [UserSchema.model_validate(usr) for usr in stack]
    stack_schema = UsersStack(users=users)

    redis_cache.set(key, stack_schema.model_dump_json())
    
def get_stack_from_redis(user: UserModel):
    data = redis_cache.get(f'user:{user.id}')
    return UsersStack.model_validate_json(data)