from fastapi import FastAPI
from app.routers import users, images, swipes, preferences

app = FastAPI()
app.include_router(users.router)
app.include_router(images.router)
app.include_router(swipes.router)
app.include_router(preferences.router)


@app.get('/')
async def hello():
    return {'message': 'hello world'}
