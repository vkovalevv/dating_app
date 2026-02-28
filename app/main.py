from fastapi import FastAPI
from app.routers import users, images, swipes, preferences
from app.task.celery import generate_stack_for_all

app = FastAPI()
app.include_router(users.router)
app.include_router(images.router)
app.include_router(swipes.router)
app.include_router(preferences.router)


@app.get('/')
async def hello():
    generate_stack_for_all.apply_async()
    return {'message': 'hello world'}
